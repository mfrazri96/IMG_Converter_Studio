import os
import shutil
import threading
import time
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Dict, List, Optional
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image

try:
    import cv2
except Exception:
    cv2 = None

try:
    from pillow_heif import register_heif_opener
except Exception:
    register_heif_opener = None

try:
    from realesrgan import RealESRGANer
    from basicsr.archs.rrdbnet_arch import RRDBNet
except Exception:
    RealESRGANer = None
    RRDBNet = None


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
MODEL_DIRS = [Path.cwd() / "Model", Path.cwd() / "weights"]

for d in (INPUT_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

if register_heif_opener is not None:
    register_heif_opener()

FORMAT_MAP = {
    "png": ("PNG", ".png"),
    "jpeg": ("JPEG", ".jpg"),
    "jpg": ("JPEG", ".jpg"),
    "webp": ("WEBP", ".webp"),
    "bmp": ("BMP", ".bmp"),
    "tiff": ("TIFF", ".tiff"),
    "gif": ("GIF", ".gif"),
    "ico": ("ICO", ".ico"),
}

REALESRGAN_MODEL_CONFIGS = {
    "RealESRGAN_x4plus": {
        "scale": 4,
        "arch": lambda: RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=4,
        ),
    },
    "RealESRGAN_x2plus": {
        "scale": 2,
        "arch": lambda: RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        ),
    },
    "RealESRGAN_x4plus_anime_6B": {
        "scale": 4,
        "arch": lambda: RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=6,
            num_grow_ch=32,
            scale=4,
        ),
    },
}


@dataclass
class JobState:
    id: str
    mode: str
    status: str = "queued"
    total: int = 0
    done: int = 0
    failed: int = 0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)


jobs: Dict[str, JobState] = {}
job_lock = threading.Lock()


app = FastAPI(title="Easy IMG Studio API", version="1.0.0")


def safe_output_path(output_dir: Path, stem: str, extension: str) -> Path:
    candidate = output_dir / f"{stem}{extension}"
    counter = 1
    while candidate.exists():
        candidate = output_dir / f"{stem}_{counter}{extension}"
        counter += 1
    return candidate


def safe_upload_name(filename: Optional[str]) -> str:
    raw_name = (filename or "").strip()
    name = PureWindowsPath(PurePosixPath(raw_name).name).name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")
    return name


def safe_download_name(filename: str) -> str:
    name = filename
    if not name or name in {".", ".."} or name != PurePosixPath(name).name or name != PureWindowsPath(name).name:
        raise HTTPException(status_code=404, detail="File not found")
    return name


def save_uploads(files: List[UploadFile], input_dir: Path) -> List[Path]:
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one image file")

    input_paths: List[Path] = []
    for upload in files:
        upload_name = safe_upload_name(upload.filename)
        upload_path = Path(upload_name)
        dst = safe_output_path(input_dir, upload_path.stem, upload_path.suffix)
        with dst.open("wb") as f:
            shutil.copyfileobj(upload.file, f)
        input_paths.append(dst)
    return input_paths


def resolve_job_output(job_id: str, filename: str) -> Path:
    safe_name = safe_download_name(filename)
    with job_lock:
        job = jobs.get(job_id)
        if not job or safe_name not in job.outputs:
            raise HTTPException(status_code=404, detail="File not found")

    output_dir = (OUTPUT_DIR / job_id).resolve()
    file_path = (output_dir / safe_name).resolve()
    if file_path.parent != output_dir or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return file_path


def prepare_for_format(image: Image.Image, save_format: str) -> Image.Image:
    if save_format in {"JPEG", "BMP"} and image.mode in ("RGBA", "LA", "P"):
        rgba = image.convert("RGBA")
        background = Image.new("RGB", rgba.size, "white")
        background.paste(rgba, mask=rgba.split()[-1])
        return background
    if save_format == "JPEG" and image.mode != "RGB":
        return image.convert("RGB")
    if save_format == "ICO" and image.mode != "RGBA":
        return image.convert("RGBA")
    return image


def detect_weights(model_name: str) -> Optional[Path]:
    for base in MODEL_DIRS:
        exact = base / f"{model_name}.pth"
        if exact.exists():
            return exact
        if base.exists():
            variants = sorted(base.glob(f"{model_name}*.pth"))
            if variants:
                return variants[0]
    return None


def build_upsampler(model_name: str, tile: int):
    if RealESRGANer is None or RRDBNet is None:
        raise RuntimeError("Real-ESRGAN dependencies are missing. Install with: python -m pip install -r requirements.txt")

    if model_name not in REALESRGAN_MODEL_CONFIGS:
        raise RuntimeError(f"Unsupported model: {model_name}")

    weights = detect_weights(model_name)
    if weights is None:
        raise RuntimeError(f"Weights not found for {model_name}. Put .pth file in Model/ or weights/")

    cfg = REALESRGAN_MODEL_CONFIGS[model_name]
    return RealESRGANer(
        scale=cfg["scale"],
        model_path=str(weights),
        model=cfg["arch"](),
        tile=tile,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )


def set_job(update_id: str, **kwargs):
    with job_lock:
        job = jobs[update_id]
        for k, v in kwargs.items():
            setattr(job, k, v)


def finish_job(job_id: str):
    with job_lock:
        job = jobs[job_id]
        job.status = "failed" if job.failed and job.done == 0 else "completed"
        job.finished_at = time.time()


def run_convert_job(job_id: str, input_files: List[Path], output_dir: Path, target_format: str, quality: int):
    set_job(job_id, status="running", started_at=time.time())
    save_format, extension = FORMAT_MAP[target_format]

    for idx, src in enumerate(input_files, start=1):
        try:
            with Image.open(src) as img:
                converted = prepare_for_format(img, save_format)
                out = safe_output_path(output_dir, src.stem, extension)
                kwargs = {}
                if save_format in {"JPEG", "WEBP"}:
                    kwargs["quality"] = quality
                    kwargs["optimize"] = True
                if save_format == "PNG":
                    kwargs["optimize"] = True
                converted.save(out, save_format, **kwargs)
                with job_lock:
                    jobs[job_id].done += 1
                    jobs[job_id].outputs.append(out.name)
        except Exception as exc:
            with job_lock:
                jobs[job_id].failed += 1
                jobs[job_id].errors.append(f"{src.name}: {exc}")

    finish_job(job_id)


def run_enhance_job(job_id: str, input_files: List[Path], output_dir: Path, model_name: str, outscale: int, tile: int):
    set_job(job_id, status="running", started_at=time.time())
    if cv2 is None:
        with job_lock:
            job = jobs[job_id]
            job.status = "failed"
            job.failed = job.total
            job.finished_at = time.time()
            job.errors = ["OpenCV dependency is missing. Install with: python -m pip install -r requirements.txt"]
        return

    try:
        upsampler = build_upsampler(model_name=model_name, tile=tile)
    except Exception as exc:
        with job_lock:
            job = jobs[job_id]
            job.status = "failed"
            job.failed = job.total
            job.finished_at = time.time()
            job.errors = [str(exc)]
        return

    for src in input_files:
        try:
            image = cv2.imread(str(src), cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Could not read image")

            output, _ = upsampler.enhance(image, outscale=outscale)
            out = safe_output_path(output_dir, f"{src.stem}_enhanced_{model_name.lower()}_x{outscale}", ".png")
            ok = cv2.imwrite(str(out), output)
            if not ok:
                raise ValueError("Failed to save output image")

            with job_lock:
                jobs[job_id].done += 1
                jobs[job_id].outputs.append(out.name)
        except Exception as exc:
            with job_lock:
                jobs[job_id].failed += 1
                jobs[job_id].errors.append(f"{src.name}: {exc}")

    finish_job(job_id)


def create_job(mode: str, total: int) -> JobState:
    job_id = str(uuid.uuid4())
    job = JobState(id=job_id, mode=mode, total=total)
    with job_lock:
        jobs[job_id] = job
    return job


@app.get("/api/models")
def list_models():
    return {
        "models": list(REALESRGAN_MODEL_CONFIGS.keys()),
        "format_targets": sorted(list(FORMAT_MAP.keys())),
    }


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "easy-img-studio"}


@app.post("/api/jobs/convert")
async def create_convert_job(
    files: List[UploadFile] = File(...),
    target_format: str = Form("png"),
    quality: int = Form(95),
):
    target_format = target_format.lower()
    if target_format not in FORMAT_MAP:
        raise HTTPException(status_code=400, detail="Unsupported target format")
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one image file")

    quality = max(1, min(100, int(quality)))
    job = create_job(mode="convert", total=len(files))

    job_input_dir = INPUT_DIR / job.id
    job_output_dir = OUTPUT_DIR / job.id
    job_input_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir.mkdir(parents=True, exist_ok=True)

    input_paths = save_uploads(files, job_input_dir)

    t = threading.Thread(
        target=run_convert_job,
        args=(job.id, input_paths, job_output_dir, target_format, quality),
        daemon=True,
    )
    t.start()

    return {"job_id": job.id}


@app.post("/api/jobs/enhance")
async def create_enhance_job(
    files: List[UploadFile] = File(...),
    model_name: str = Form("RealESRGAN_x4plus"),
    outscale: int = Form(4),
    tile: int = Form(400),
):
    if model_name not in REALESRGAN_MODEL_CONFIGS:
        raise HTTPException(status_code=400, detail="Unsupported Real-ESRGAN model")
    if not files:
        raise HTTPException(status_code=400, detail="Choose at least one image file")

    outscale = int(outscale)
    if outscale not in {2, 4}:
        raise HTTPException(status_code=400, detail="Output scale must be 2 or 4")
    tile = max(0, int(tile))

    job = create_job(mode="enhance", total=len(files))

    job_input_dir = INPUT_DIR / job.id
    job_output_dir = OUTPUT_DIR / job.id
    job_input_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir.mkdir(parents=True, exist_ok=True)

    input_paths = save_uploads(files, job_input_dir)

    t = threading.Thread(
        target=run_enhance_job,
        args=(job.id, input_paths, job_output_dir, model_name, outscale, tile),
        daemon=True,
    )
    t.start()

    return {"job_id": job.id}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        download_all = None
        if job.status in {"completed", "failed"} and job.outputs:
            download_all = f"/api/download-zip/{job.id}"
        return {
            "id": job.id,
            "mode": job.mode,
            "status": job.status,
            "total": job.total,
            "done": job.done,
            "failed": job.failed,
            "errors": job.errors[-5:],
            "outputs": [f"/api/download/{job.id}/{quote(name, safe='')}" for name in job.outputs],
            "download_all": download_all,
            "started_at": job.started_at,
            "finished_at": job.finished_at,
        }


@app.get("/api/download/{job_id}/{filename}")
def download_output(job_id: str, filename: str):
    file_path = resolve_job_output(job_id, filename)
    return FileResponse(path=str(file_path), filename=file_path.name)


@app.get("/api/download-zip/{job_id}")
def download_all_outputs(job_id: str):
    with job_lock:
        job = jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status == "running":
            raise HTTPException(status_code=409, detail="Job is still running. Please wait until completion.")
        output_names = list(job.outputs)

    output_dir = (OUTPUT_DIR / job_id).resolve()
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Job output not found")

    files = []
    for name in output_names:
        safe_name = safe_download_name(name)
        file_path = (output_dir / safe_name).resolve()
        if file_path.parent == output_dir and file_path.is_file():
            files.append(file_path)
    if not files:
        raise HTTPException(status_code=404, detail="No output files for this job")

    zip_path = output_dir / "_all_outputs.zip"
    tmp_zip_path = output_dir / "_all_outputs.tmp.zip"
    with zipfile.ZipFile(tmp_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, arcname=f.name)
    os.replace(tmp_zip_path, zip_path)

    return FileResponse(path=str(zip_path), filename=f"easy-img-studio-{job_id}.zip")


# Mount static UI after API routes so /api/* doesn't get shadowed.
app.mount("/", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")
