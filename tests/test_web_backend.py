import io
import tempfile
import time
import unittest
from importlib import import_module
from pathlib import Path


def load_backend():
    try:
        from fastapi.testclient import TestClient

        backend = import_module("web_app.app.main")
    except ModuleNotFoundError as exc:
        raise unittest.SkipTest(f"Web runtime dependency is not installed: {exc.name}") from exc
    return backend, TestClient


def png_bytes():
    try:
        from PIL import Image
    except ModuleNotFoundError as exc:
        raise unittest.SkipTest(f"Image dependency is not installed: {exc.name}") from exc

    buffer = io.BytesIO()
    Image.new("RGBA", (8, 8), (40, 90, 160, 180)).save(buffer, "PNG")
    return buffer.getvalue()


class WebBackendApiTests(unittest.TestCase):
    def setUp(self):
        self.backend, test_client = load_backend()
        self.client = test_client(self.backend.app)
        self.tmp = tempfile.TemporaryDirectory()
        self.old_input_dir = self.backend.INPUT_DIR
        self.old_output_dir = self.backend.OUTPUT_DIR
        root = Path(self.tmp.name)
        self.backend.INPUT_DIR = root / "input"
        self.backend.OUTPUT_DIR = root / "output"
        self.backend.INPUT_DIR.mkdir(parents=True)
        self.backend.OUTPUT_DIR.mkdir(parents=True)
        with self.backend.job_lock:
            self.backend.jobs.clear()

    def tearDown(self):
        with self.backend.job_lock:
            self.backend.jobs.clear()
        self.backend.INPUT_DIR = self.old_input_dir
        self.backend.OUTPUT_DIR = self.old_output_dir
        self.tmp.cleanup()

    def test_health_and_model_metadata_endpoints(self):
        health = self.client.get("/api/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

        metadata = self.client.get("/api/models")
        self.assertEqual(metadata.status_code, 200)
        self.assertIn("png", metadata.json()["format_targets"])

    def test_convert_job_preserves_duplicate_upload_names(self):
        image = png_bytes()
        response = self.client.post(
            "/api/jobs/convert",
            data={"target_format": "jpg", "quality": "80"},
            files=[
                ("files", ("sample.png", io.BytesIO(image), "image/png")),
                ("files", ("sample.png", io.BytesIO(image), "image/png")),
            ],
        )
        self.assertEqual(response.status_code, 200)
        job_id = response.json()["job_id"]

        job = None
        for _ in range(25):
            status = self.client.get(f"/api/jobs/{job_id}")
            self.assertEqual(status.status_code, 200)
            job = status.json()
            if job["status"] in {"completed", "failed"}:
                break
            time.sleep(0.1)

        self.assertIsNotNone(job)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["done"], 2)
        self.assertEqual(len(job["outputs"]), 2)
        self.assertNotEqual(job["outputs"][0], job["outputs"][1])

    def test_download_endpoint_rejects_untracked_or_nested_names(self):
        job_id = "job-safe"
        output_dir = self.backend.OUTPUT_DIR / job_id
        output_dir.mkdir(parents=True)
        (output_dir / "safe.png").write_bytes(b"image")
        with self.backend.job_lock:
            self.backend.jobs[job_id] = self.backend.JobState(
                id=job_id,
                mode="convert",
                status="completed",
                total=1,
                done=1,
                outputs=["safe.png"],
            )

        safe = self.client.get(f"/api/download/{job_id}/safe.png")
        self.assertEqual(safe.status_code, 200)

        nested = self.client.get(f"/api/download/{job_id}/..%5Csecret.png")
        self.assertEqual(nested.status_code, 404)

        untracked = self.client.get(f"/api/download/{job_id}/other.png")
        self.assertEqual(untracked.status_code, 404)

    def test_job_outputs_percent_encode_download_filenames(self):
        job_id = "job-encoded"
        special_name = " cover #1%.png"
        output_dir = self.backend.OUTPUT_DIR / job_id
        output_dir.mkdir(parents=True)
        (output_dir / special_name).write_bytes(b"image")
        with self.backend.job_lock:
            self.backend.jobs[job_id] = self.backend.JobState(
                id=job_id,
                mode="convert",
                status="completed",
                total=1,
                done=1,
                outputs=[special_name],
            )

        status = self.client.get(f"/api/jobs/{job_id}")
        self.assertEqual(status.status_code, 200)
        output_url = status.json()["outputs"][0]
        self.assertEqual(output_url, f"/api/download/{job_id}/%20cover%20%231%25.png")

        download = self.client.get(output_url)
        self.assertEqual(download.status_code, 200)


if __name__ == "__main__":
    unittest.main()
