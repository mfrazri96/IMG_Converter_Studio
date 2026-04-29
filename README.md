# Easy IMG Studio

Production-ready image conversion + Real-ESRGAN enhancement.
This repository includes a desktop app (Tkinter), a local browser app (FastAPI), and Docker support.

## Features

- Local web app with a polished two-column workspace:
  - Job Setup for mode, upload, and processing options
  - Job Monitor for status, progress, errors, and downloads
  - Responsive single-column layout on mobile screens
- Drag-and-drop or file picker uploads in the browser.
- Bulk conversion (single or multiple images).
- `Mode: Convert` output formats:
  - PNG (`.png`)
  - JPEG (`.jpg`)
  - WEBP (`.webp`)
  - BMP (`.bmp`)
  - TIFF (`.tiff`)
  - GIF (`.gif`)
  - ICO (`.ico`)
- `Mode: Enhance` (Real-ESRGAN):
  - speed profile (`Fast`, `Quality`)
  - model selection (`RealESRGAN_x4plus`, `RealESRGAN_x2plus`, `RealESRGAN_x4plus_anime_6B`)
  - output scaling (`x2`, `x4`)
  - tile size control
  - weights file selection (`.pth`)
  - output naming pattern: `filename_enhanced_<model>_x<scale>.png`
- Selected file queue with file names, sizes, remove controls, and total size summary.
- Adjustable quality for JPEG/WEBP (1-100).
- Auto-rename outputs to avoid overwriting (`name_1`, `name_2`, ...).
- Progress bar, `x / total` counter, success/failure counts, and API status.
- Individual output downloads plus **Download All (.zip)** in the web app.
- Desktop app still includes queue management, preview, output folder selection, and **Open Output Folder**.

## Requirements

- Python 3.9+ (recommended)
- Tkinter for the desktop app (included with most standard Python installs)
- Docker Desktop if you want the containerized web app
- Real-ESRGAN `.pth` weights for enhancement mode

Install all local runtime dependencies from the project root:

```bash
pip install -r requirements.txt
```

The Docker image uses the same web dependency set from:

```text
web_app/requirements-web.txt
```

## Run Local Web App

From the `Easy IMG Converter` folder, run:

```bash
python -m pip install -r requirements.txt
python run_web.py
```

Open:

```text
http://127.0.0.1:8000
```

Optional equivalent command:

```bash
python -m uvicorn web_app.app.main:app --host 127.0.0.1 --port 8000
```

Use another port if 8000 is busy:

```bash
python run_web.py --port 8001
```

If you install the project as an editable package, the console script is also available:

```bash
python -m pip install -e .
easy-img-web --port 8000
```

If `python run_web.py` reports a missing local web runtime dependency, rerun:

```bash
python -m pip install -r requirements.txt
```

## Run With Docker

Docker support is preserved. From the project root, run:

```bash
docker compose up --build
```

Open:

```text
http://127.0.0.1:8000
```

Stop the container:

```bash
docker compose down
```

## Run Desktop App

From the `Easy IMG Converter` folder, run:

```bash
python IMG_Converter.py
```

## Test

Run smoke tests:

```bash
python -m pytest
```

If pytest is not installed, run the unittest suite:

```bash
python -m unittest discover -s tests
```

## How To Use

### Web App

1. Open `http://127.0.0.1:8000`.
2. Choose **Convert** or **Enhance**.
3. In **Job Setup**, drop images into the upload area or click **Choose Files**.
4. For **Convert**, choose the output format and JPEG/WEBP quality.
5. For **Enhance**, choose the Real-ESRGAN model, output scale, and tile size.
6. Click **Start Conversion** or **Start Enhancement**.
7. Watch **Job Monitor** for progress, errors, and download links.
8. Download individual outputs or use **Download All (.zip)** when multiple outputs are available.

### Desktop App

1. Click **Add Images** to load one or many files.
2. (Optional) Use **Remove Selected** or **Clear Queue** to manage the list.
3. Choose **Mode**:
   - `Convert` for format conversion
   - `Enhance` for super-resolution
4. If in `Convert` mode:
   - choose **Target Format**
   - (optional) set **Quality** for JPEG/WEBP
5. If in `Enhance` mode:
   - choose **Speed Profile** (`Fast`/`Quality`)
   - choose **Real-ESRGAN Model** and **Output Scale**
   - (optional) adjust **Tile Size** for speed/memory balance
   - pick the weights `.pth` file path
6. Select the **Output Folder**.
7. Click **Start Conversion** or **Start Enhancement**.
8. Click **Open Output Folder** to view outputs.

## Notes

- Formats like JPEG/BMP do not support transparency.
  Transparent images are flattened to a white background automatically.
- If an output file already exists, the app generates a safe new name:
  - `photo.png`
  - `photo_1.png`
  - `photo_2.png`
- Enhancement requires matching Real-ESRGAN `.pth` weights for the selected model.
- App auto-detects weights from `Model/` first, then `weights/`.
- Recommended default weights path:
  `Model/RealESRGAN_x4plus.pth`
- **Open Output Folder** uses `os.startfile`, so it works on Windows.

## Project Structure

```text
Easy IMG Converter/
  IMG_Converter.py
  pyproject.toml
  run_web.py
  requirements.txt
  easy_img_converter/
    app.py
    config/
      constants.py
    features/
      converter.py
      enhancer.py
    services/
      file_queue.py
      output_naming.py
    ui/
      main_window.py
  README.md
  tests/
    test_smoke.py
  web_app/
    cli.py
    app/
      __init__.py
      main.py
      static/index.html
    __init__.py
    Dockerfile
    requirements-web.txt
    README-web.md
  Output/    # optional folder for exported files
```
