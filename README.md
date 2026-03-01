# Easy IMG Converter

A desktop image converter built with Python + Tkinter.
Convert one image or many images in bulk to a format you choose, with live queue status and preview.

## Features

- Modern two-panel UI:
  - Left: file queue table
  - Right: image preview + conversion settings
- Bulk conversion (single or multiple images).
- Supported output formats:
  - PNG (`.png`)
  - JPEG (`.jpg`)
  - WEBP (`.webp`)
  - BMP (`.bmp`)
  - TIFF (`.tiff`)
  - GIF (`.gif`)
  - ICO (`.ico`)
- Queue table columns:
  - File name
  - File size
  - Source format
  - Target format
  - Status (`Queued`, `Converting`, `Done`, `Failed`)
- Click a queued file to preview thumbnail and metadata.
- Adjustable quality for JPEG/WEBP (1-100).
- Auto-rename outputs to avoid overwriting (`name_1`, `name_2`, ...).
- Progress bar, `x / total` counter, and ETA during conversion.
- Quick button to open output folder after conversion.

## Requirements

- Python 3.9+ (recommended)
- Pillow
- Tkinter (included with most standard Python installs)

Install dependency:

```bash
pip install pillow
```

## Run

From the `Easy IMG Converter` folder, run:

```bash
python IMG_Converter.py
```

## How To Use

1. Click **Add Images** to load one or many files.
2. (Optional) Use **Remove Selected** or **Clear Queue** to manage the list.
3. Choose your **Target Format**.
4. (Optional) Set **Quality** for JPEG/WEBP.
5. Select the **Output Folder**.
6. Click **Start Conversion**.
7. Click **Open Output Folder** to view converted files.

## Notes

- Formats like JPEG/BMP do not support transparency.
  Transparent images are flattened to a white background automatically.
- If an output file already exists, the app generates a safe new name:
  - `photo.png`
  - `photo_1.png`
  - `photo_2.png`
- **Open Output Folder** uses `os.startfile`, so it works on Windows.

## Project Structure

```text
Easy IMG Converter/
  IMG_Converter.py
  README.md
  Output/    # optional folder for exported files
```
