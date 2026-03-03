from pathlib import Path

APP_TITLE = "Easy IMG Converter"
WINDOW_SIZE = "1120x700"
MIN_WINDOW_SIZE = (1000, 640)
DEFAULT_REALESRGAN_WEIGHTS = Path.cwd() / "Model" / "RealESRGAN_x4plus.pth"

COLORS = {
    "bg": "#f2f6fb",
    "surface": "#ffffff",
    "primary": "#0f5fa8",
    "primary_hover": "#0b4e8a",
    "accent": "#ff7a18",
    "text_main": "#142437",
    "text_muted": "#5a6d84",
    "border": "#dce5f0",
    "ok": "#18794e",
    "warn": "#ad6800",
    "bad": "#b42318",
    "pending": "#475467",
}

FORMAT_MAP = {
    "PNG (.png)": ("PNG", ".png"),
    "JPEG (.jpg)": ("JPEG", ".jpg"),
    "WEBP (.webp)": ("WEBP", ".webp"),
    "BMP (.bmp)": ("BMP", ".bmp"),
    "TIFF (.tiff)": ("TIFF", ".tiff"),
    "GIF (.gif)": ("GIF", ".gif"),
    "ICO (.ico)": ("ICO", ".ico"),
}

REALESRGAN_MODELS = [
    "RealESRGAN_x4plus",
    "RealESRGAN_x2plus",
    "RealESRGAN_x4plus_anime_6B",
]

ENHANCE_PROFILES = ["Fast", "Quality"]
