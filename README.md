# Easy IMG Converter

A desktop image converter built with Python + Tkinter.
Convert or enhance one image or many images in bulk, with live queue status and preview.

## Features

- Modern two-panel UI:
  - Left: file queue table
  - Right: image preview + conversion settings
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
- Queue table columns:
  - File name
  - File size
  - Source format
  - Target/Action
  - Status (`Queued`, `Converting`, `Done`, `Failed`)
- Click a queued file to preview thumbnail and metadata.
- Adjustable quality for JPEG/WEBP (1-100).
- Auto-rename outputs to avoid overwriting (`name_1`, `name_2`, ...).
- Progress bar, `x / total` counter, and ETA during conversion.
- Quick button to open output folder after conversion.

## Requirements

- Python 3.9+ (recommended)
- Pillow
- OpenCV (`opencv-python`)
- PyTorch (`torch`)
- Real-ESRGAN (`realesrgan`, `basicsr`)
- Tkinter (included with most standard Python installs)

Install dependency:

```bash
pip install -r requirements.txt
```

## Run

From the `Easy IMG Converter` folder, run:

```bash
python IMG_Converter.py
```

## Test

Run smoke tests:

```bash
python -m unittest discover -s tests
```

## How To Use

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
  Output/    # optional folder for exported files
```
