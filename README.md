# Easy IMG Converter

A desktop image converter built with Python + Tkinter.  
Convert one image or bulk images into a format you choose with a simple UI.

## Features

- Convert single or multiple images at once.
- Choose output format:
  - PNG (`.png`)
  - JPEG (`.jpg`)
  - WEBP (`.webp`)
  - BMP (`.bmp`)
  - TIFF (`.tiff`)
  - GIF (`.gif`)
  - ICO (`.ico`)
- Select custom output folder.
- Adjustable quality (for JPEG and WEBP).
- Auto-rename output files to avoid overwriting.
- Progress bar and conversion summary.

## Requirements

- Python 3.9+ (recommended)
- Pillow
- Tkinter (included with most standard Python installs)

Install dependency:

```bash
pip install pillow
```

## Run

From the `Easy IMG Converter` folder:

```bash
python IMG_Converter.py
```

## How To Use

1. Click **Add Images** and select one or many image files.
2. Choose the **Target format**.
3. (Optional) Set **JPEG/WEBP quality** (1-100).
4. Choose **Output folder**.
5. Click **Start Conversion**.

## Notes

- Some formats (like JPEG/BMP) do not support transparency.  
  Transparent images are automatically flattened to a white background.
- If an output filename already exists, the app creates a new name like:
  - `photo.png`
  - `photo_1.png`
  - `photo_2.png`

## Project Structure

```text
Easy IMG Converter/
  IMG_Converter.py
  README.md
  Output/
```

