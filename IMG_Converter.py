import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image


class ImageFormatConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Image Format Converter")
        self.root.geometry("860x620")
        self.root.minsize(780, 560)
        self.root.configure(bg="#eef3f7")

        self.selected_files = []

        self.format_map = {
            "PNG (.png)": ("PNG", ".png"),
            "JPEG (.jpg)": ("JPEG", ".jpg"),
            "WEBP (.webp)": ("WEBP", ".webp"),
            "BMP (.bmp)": ("BMP", ".bmp"),
            "TIFF (.tiff)": ("TIFF", ".tiff"),
            "GIF (.gif)": ("GIF", ".gif"),
            "ICO (.ico)": ("ICO", ".ico"),
        }

        self.output_folder = tk.StringVar(value=str(Path.cwd()))
        self.target_format = tk.StringVar(value="PNG (.png)")
        self.quality = tk.IntVar(value=95)
        self.status_text = tk.StringVar(value="Ready")
        self.progress_value = tk.DoubleVar(value=0)

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Header.TLabel", background="#eef3f7", foreground="#112a46", font=("Segoe UI", 20, "bold"))
        style.configure("SubHeader.TLabel", background="#eef3f7", foreground="#516278", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#1e3a5f", font=("Segoe UI", 11, "bold"))
        style.configure("Info.TLabel", background="#ffffff", foreground="#30475f", font=("Segoe UI", 9))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=18)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Universal Image Format Converter", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            main,
            text="Convert one image or many images to the format you choose.",
            style="SubHeader.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        files_card = ttk.Frame(main, style="Card.TFrame", padding=14)
        files_card.pack(fill="both", expand=True, pady=(0, 10))
        ttk.Label(files_card, text="1) Select Image Files", style="CardTitle.TLabel").pack(anchor="w")
        ttk.Label(
            files_card,
            text="You can select one image or multiple images in a single step.",
            style="Info.TLabel",
        ).pack(anchor="w", pady=(0, 8))

        file_btn_row = ttk.Frame(files_card, style="Card.TFrame")
        file_btn_row.pack(fill="x", pady=(0, 8))
        ttk.Button(file_btn_row, text="Add Images", command=self.add_images, style="Accent.TButton").pack(side="left")
        ttk.Button(file_btn_row, text="Clear List", command=self.clear_images).pack(side="left", padx=(8, 0))

        list_frame = ttk.Frame(files_card, style="Card.TFrame")
        list_frame.pack(fill="both", expand=True)
        self.file_listbox = tk.Listbox(list_frame, height=11, font=("Consolas", 10), selectmode=tk.EXTENDED)
        self.file_listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scroll.pack(side="right", fill="y")
        self.file_listbox.configure(yscrollcommand=scroll.set)

        options_card = ttk.Frame(main, style="Card.TFrame", padding=14)
        options_card.pack(fill="x", pady=(0, 10))
        ttk.Label(options_card, text="2) Choose Output Settings", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )

        ttk.Label(options_card, text="Target format:", style="Info.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 5))
        format_combo = ttk.Combobox(
            options_card,
            textvariable=self.target_format,
            values=list(self.format_map.keys()),
            state="readonly",
            width=20,
        )
        format_combo.grid(row=1, column=1, sticky="w", pady=(10, 5))

        ttk.Label(options_card, text="JPEG/WEBP quality:", style="Info.TLabel").grid(
            row=1, column=2, sticky="w", padx=(16, 4), pady=(10, 5)
        )
        quality_spin = ttk.Spinbox(options_card, from_=1, to=100, textvariable=self.quality, width=5)
        quality_spin.grid(row=1, column=2, sticky="e", pady=(10, 5))

        ttk.Label(options_card, text="Output folder:", style="Info.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
        self.output_entry = ttk.Entry(options_card, textvariable=self.output_folder, width=62)
        self.output_entry.grid(row=2, column=1, columnspan=2, sticky="we", pady=(8, 0))
        ttk.Button(options_card, text="Browse", command=self.select_output_folder).grid(row=2, column=3, padx=(8, 0), pady=(8, 0))

        options_card.columnconfigure(1, weight=1)
        options_card.columnconfigure(2, weight=1)

        action_card = ttk.Frame(main, style="Card.TFrame", padding=14)
        action_card.pack(fill="x")
        ttk.Label(action_card, text="3) Convert", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        ttk.Button(action_card, text="Start Conversion", command=self.start_conversion, style="Accent.TButton").grid(
            row=0, column=1, sticky="e"
        )
        action_card.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(action_card, variable=self.progress_value, maximum=100)
        self.progress.grid(row=1, column=0, columnspan=2, sticky="we", pady=(10, 6))

        self.status_label = ttk.Label(action_card, textvariable=self.status_text, style="Info.TLabel")
        self.status_label.grid(row=2, column=0, columnspan=2, sticky="w")

    def add_images(self):
        files = filedialog.askopenfilenames(
            title="Choose image files",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.tif *.webp *.ico"),
                ("All files", "*.*"),
            ],
        )
        if not files:
            return

        existing = set(self.selected_files)
        for file_path in files:
            if file_path not in existing:
                self.selected_files.append(file_path)
                self.file_listbox.insert(tk.END, file_path)

        self.status_text.set(f"Loaded {len(self.selected_files)} file(s).")

    def clear_images(self):
        self.selected_files = []
        self.file_listbox.delete(0, tk.END)
        self.progress_value.set(0)
        self.status_text.set("Ready")

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)

    def _safe_output_path(self, output_dir, stem, extension):
        candidate = Path(output_dir) / f"{stem}{extension}"
        counter = 1
        while candidate.exists():
            candidate = Path(output_dir) / f"{stem}_{counter}{extension}"
            counter += 1
        return str(candidate)

    def _prepare_image_for_format(self, image, save_format):
        # Flatten alpha for formats that do not support transparency.
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

    def start_conversion(self):
        if not self.selected_files:
            messagebox.showerror("No Images Selected", "Please add at least one image file.")
            return

        output_dir = self.output_folder.get().strip()
        if not output_dir:
            messagebox.showerror("No Output Folder", "Please choose an output folder.")
            return

        if not os.path.isdir(output_dir):
            messagebox.showerror("Invalid Folder", "The selected output folder does not exist.")
            return

        format_name = self.target_format.get()
        if format_name not in self.format_map:
            messagebox.showerror("Invalid Format", "Please choose a valid target format.")
            return

        save_format, extension = self.format_map[format_name]
        total = len(self.selected_files)
        converted = 0
        failed = 0
        quality = max(1, min(100, int(self.quality.get())))

        self.progress_value.set(0)
        self.root.update_idletasks()

        for index, input_file in enumerate(self.selected_files, start=1):
            file_name = Path(input_file).name
            self.status_text.set(f"Converting {index}/{total}: {file_name}")
            self.root.update_idletasks()

            try:
                with Image.open(input_file) as img:
                    converted_img = self._prepare_image_for_format(img, save_format)
                    output_path = self._safe_output_path(output_dir, Path(input_file).stem, extension)

                    save_kwargs = {}
                    if save_format in {"JPEG", "WEBP"}:
                        save_kwargs["quality"] = quality
                        save_kwargs["optimize"] = True

                    if save_format == "PNG":
                        save_kwargs["optimize"] = True

                    converted_img.save(output_path, save_format, **save_kwargs)
                    converted += 1

            except Exception:
                failed += 1

            progress_percent = (index / total) * 100
            self.progress_value.set(progress_percent)
            self.root.update_idletasks()

        self.status_text.set(f"Completed. Converted: {converted}, Failed: {failed}")
        messagebox.showinfo(
            "Conversion Finished",
            f"Done.\n\nTotal files: {total}\nConverted: {converted}\nFailed: {failed}\nOutput folder: {output_dir}",
        )

    def run(self):
        self.root.mainloop()


def main():
    app = ImageFormatConverterApp()
    app.run()


if __name__ == "__main__":
    main()
