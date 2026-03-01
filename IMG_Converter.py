import os
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk


class ImageFormatConverterApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Easy IMG Converter")
        self.root.geometry("1080x680")
        self.root.minsize(980, 620)

        self.colors = {
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

        self.root.configure(bg=self.colors["bg"])
        self.selected_files = []
        self.row_map = {}
        self.preview_image_ref = None
        self.last_output_dir = None

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
        self.progress_text = tk.StringVar(value="0 / 0")
        self.progress_value = tk.DoubleVar(value=0)
        self.preview_meta = tk.StringVar(value="No image selected")

        self._setup_style()
        self._build_ui()

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Root.TFrame", background=self.colors["bg"])
        style.configure("Card.TFrame", background=self.colors["surface"], borderwidth=1, relief="solid")

        style.configure(
            "Header.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text_main"],
            font=("Segoe UI Semibold", 22),
        )
        style.configure(
            "SubHeader.TLabel",
            background=self.colors["bg"],
            foreground=self.colors["text_muted"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text_main"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Info.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text_muted"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "PreviewMeta.TLabel",
            background=self.colors["surface"],
            foreground=self.colors["text_muted"],
            font=("Consolas", 9),
        )
        style.configure(
            "Primary.TButton",
            font=("Segoe UI Semibold", 10),
            foreground="#ffffff",
            background=self.colors["primary"],
            bordercolor=self.colors["primary"],
            focusthickness=0,
            padding=(12, 7),
        )
        style.map("Primary.TButton", background=[("active", self.colors["primary_hover"])])
        style.configure("Soft.TButton", font=("Segoe UI", 9), padding=(10, 6))
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=26, fieldbackground=self.colors["surface"])
        style.configure("Treeview.Heading", font=("Segoe UI Semibold", 9))
        style.configure("Accent.Horizontal.TProgressbar", troughcolor="#e8eef6", background=self.colors["accent"])

    def _build_ui(self):
        main = ttk.Frame(self.root, style="Root.TFrame", padding=18)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Easy IMG Converter", style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            main,
            text="Batch-convert images to any supported format with live status and preview.",
            style="SubHeader.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 14))

        workspace = ttk.Frame(main, style="Root.TFrame")
        workspace.grid(row=2, column=0, sticky="nsew")
        workspace.columnconfigure(0, weight=3)
        workspace.columnconfigure(1, weight=2)
        workspace.rowconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)
        main.columnconfigure(0, weight=1)

        self._build_left_panel(workspace)
        self._build_right_panel(workspace)

    def _build_left_panel(self, parent):
        left_card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_card.columnconfigure(0, weight=1)
        left_card.rowconfigure(2, weight=1)

        ttk.Label(left_card, text="File Queue", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(left_card, text="Select one or many files. Click a row to preview.", style="Info.TLabel").grid(
            row=1, column=0, sticky="w", pady=(0, 10)
        )

        table_frame = ttk.Frame(left_card, style="Card.TFrame")
        table_frame.grid(row=2, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("name", "size", "from", "to", "status")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.table.heading("name", text="File")
        self.table.heading("size", text="Size")
        self.table.heading("from", text="From")
        self.table.heading("to", text="To")
        self.table.heading("status", text="Status")

        self.table.column("name", width=290, anchor="w")
        self.table.column("size", width=90, anchor="e")
        self.table.column("from", width=70, anchor="center")
        self.table.column("to", width=70, anchor="center")
        self.table.column("status", width=100, anchor="center")

        self.table.grid(row=0, column=0, sticky="nsew")
        table_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        table_scroll.grid(row=0, column=1, sticky="ns")
        self.table.configure(yscrollcommand=table_scroll.set)
        self.table.bind("<<TreeviewSelect>>", self.on_row_select)

        self.table.tag_configure("queued", foreground=self.colors["pending"])
        self.table.tag_configure("converting", foreground=self.colors["warn"])
        self.table.tag_configure("done", foreground=self.colors["ok"])
        self.table.tag_configure("failed", foreground=self.colors["bad"])

        actions = ttk.Frame(left_card, style="Card.TFrame")
        actions.grid(row=3, column=0, sticky="we", pady=(10, 0))
        ttk.Button(actions, text="Add Images", command=self.add_images, style="Primary.TButton").pack(side="left")
        ttk.Button(actions, text="Remove Selected", command=self.remove_selected, style="Soft.TButton").pack(
            side="left", padx=(8, 0)
        )
        ttk.Button(actions, text="Clear Queue", command=self.clear_images, style="Soft.TButton").pack(side="left", padx=(8, 0))

    def _build_right_panel(self, parent):
        right = ttk.Frame(parent, style="Root.TFrame")
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(0, weight=2)
        right.rowconfigure(1, weight=3)
        right.columnconfigure(0, weight=1)

        preview_card = ttk.Frame(right, style="Card.TFrame", padding=14)
        preview_card.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        preview_card.rowconfigure(1, weight=1)
        preview_card.columnconfigure(0, weight=1)

        ttk.Label(preview_card, text="Preview", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        self.preview_canvas = tk.Canvas(
            preview_card,
            height=210,
            bg="#eaf0f7",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            bd=0,
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        self.preview_canvas.create_text(
            180,
            105,
            text="Select a file to preview",
            fill="#75879f",
            font=("Segoe UI", 10),
            tags="preview_text",
        )

        ttk.Label(preview_card, textvariable=self.preview_meta, style="PreviewMeta.TLabel").grid(
            row=2, column=0, sticky="w"
        )

        settings_card = ttk.Frame(right, style="Card.TFrame", padding=14)
        settings_card.grid(row=1, column=0, sticky="nsew")
        settings_card.columnconfigure(1, weight=1)

        ttk.Label(settings_card, text="Settings", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(settings_card, text="Target Format", style="Info.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 4))
        format_combo = ttk.Combobox(
            settings_card,
            textvariable=self.target_format,
            values=list(self.format_map.keys()),
            state="readonly",
            width=18,
        )
        format_combo.grid(row=1, column=1, sticky="w", pady=(10, 4))
        format_combo.bind("<<ComboboxSelected>>", self.on_target_change)

        ttk.Label(settings_card, text="Quality (JPEG/WEBP)", style="Info.TLabel").grid(
            row=2, column=0, sticky="w", pady=(6, 4)
        )
        ttk.Spinbox(settings_card, from_=1, to=100, textvariable=self.quality, width=6).grid(
            row=2, column=1, sticky="w", pady=(6, 4)
        )

        ttk.Label(settings_card, text="Output Folder", style="Info.TLabel").grid(row=3, column=0, sticky="w", pady=(6, 4))
        ttk.Entry(settings_card, textvariable=self.output_folder).grid(row=3, column=1, sticky="we", pady=(6, 4))
        ttk.Button(settings_card, text="Browse", command=self.select_output_folder, style="Soft.TButton").grid(
            row=3, column=2, padx=(8, 0), pady=(6, 4)
        )

        ttk.Separator(settings_card).grid(row=4, column=0, columnspan=3, sticky="we", pady=10)

        ttk.Button(settings_card, text="Start Conversion", command=self.start_conversion, style="Primary.TButton").grid(
            row=5, column=0, columnspan=3, sticky="we"
        )
        ttk.Button(settings_card, text="Open Output Folder", command=self.open_output_folder, style="Soft.TButton").grid(
            row=6, column=0, columnspan=3, sticky="we", pady=(8, 0)
        )

        self.progress = ttk.Progressbar(
            settings_card,
            variable=self.progress_value,
            maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self.progress.grid(row=7, column=0, columnspan=3, sticky="we", pady=(12, 6))

        status_row = ttk.Frame(settings_card, style="Card.TFrame")
        status_row.grid(row=8, column=0, columnspan=3, sticky="we")
        status_row.columnconfigure(0, weight=1)
        ttk.Label(status_row, textvariable=self.status_text, style="Info.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(status_row, textvariable=self.progress_text, style="Info.TLabel").grid(row=0, column=1, sticky="e")

    def _format_size(self, size_bytes):
        value = float(size_bytes)
        units = ["B", "KB", "MB", "GB"]
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} {unit}"
            value /= 1024
        return f"{int(size_bytes)} B"

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

        target_ext = self.format_map[self.target_format.get()][1].replace(".", "").upper()
        existing = set(self.selected_files)
        added = 0
        for file_path in files:
            if file_path in existing:
                continue

            file_info = Path(file_path)
            source_ext = file_info.suffix.replace(".", "").upper() or "-"
            size = self._format_size(file_info.stat().st_size) if file_info.exists() else "-"
            row_id = self.table.insert(
                "",
                "end",
                values=(file_info.name, size, source_ext, target_ext, "Queued"),
                tags=("queued",),
            )
            self.selected_files.append(file_path)
            self.row_map[file_path] = row_id
            added += 1

        self.status_text.set(f"Added {added} new file(s).")
        self.progress_text.set(f"{len(self.selected_files)} queued")

    def remove_selected(self):
        selection = self.table.selection()
        if not selection:
            return

        for item_id in selection:
            row_values = self.table.item(item_id, "values")
            file_name = row_values[0]
            match = next((p for p in self.selected_files if Path(p).name == file_name), None)
            if match:
                self.selected_files.remove(match)
                self.row_map.pop(match, None)
            self.table.delete(item_id)

        self.status_text.set("Selected file removed.")
        self.progress_text.set(f"{len(self.selected_files)} queued")

    def clear_images(self):
        self.selected_files = []
        self.row_map = {}
        for item in self.table.get_children():
            self.table.delete(item)
        self.progress_value.set(0)
        self.progress_text.set("0 / 0")
        self.status_text.set("Queue cleared.")
        self.preview_meta.set("No image selected")
        self._clear_preview()

    def select_output_folder(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self.output_folder.set(folder)

    def open_output_folder(self):
        output_dir = self.last_output_dir or self.output_folder.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Invalid Folder", "Output folder does not exist.")
            return
        os.startfile(output_dir)

    def on_target_change(self, _event=None):
        target_ext = self.format_map[self.target_format.get()][1].replace(".", "").upper()
        for path in self.selected_files:
            row_id = self.row_map.get(path)
            if not row_id:
                continue
            values = list(self.table.item(row_id, "values"))
            values[3] = target_ext
            self.table.item(row_id, values=values)

    def on_row_select(self, _event=None):
        selection = self.table.selection()
        if not selection:
            return

        file_name = self.table.item(selection[0], "values")[0]
        file_path = next((p for p in self.selected_files if Path(p).name == file_name), None)
        if file_path:
            self._show_preview(file_path)

    def _clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            180,
            105,
            text="Select a file to preview",
            fill="#75879f",
            font=("Segoe UI", 10),
        )
        self.preview_image_ref = None

    def _show_preview(self, file_path):
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                img_copy = img.convert("RGBA")
                img_copy.thumbnail((330, 200))

                self.preview_image_ref = ImageTk.PhotoImage(img_copy)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(165, 105, image=self.preview_image_ref)
                self.preview_meta.set(
                    f"{Path(file_path).name} | {width}x{height}px | {self._format_size(Path(file_path).stat().st_size)}"
                )
        except Exception:
            self.preview_meta.set("Preview unavailable")
            self._clear_preview()

    def _safe_output_path(self, output_dir, stem, extension):
        candidate = Path(output_dir) / f"{stem}{extension}"
        counter = 1
        while candidate.exists():
            candidate = Path(output_dir) / f"{stem}_{counter}{extension}"
            counter += 1
        return str(candidate)

    def _prepare_image_for_format(self, image, save_format):
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

    def _set_row_status(self, input_file, status):
        row_id = self.row_map.get(input_file)
        if not row_id:
            return

        values = list(self.table.item(row_id, "values"))
        values[4] = status

        tag = "queued"
        if status == "Converting":
            tag = "converting"
        elif status == "Done":
            tag = "done"
        elif status == "Failed":
            tag = "failed"

        self.table.item(row_id, values=values, tags=(tag,))

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
        start_time = time.time()

        self.progress_value.set(0)
        self.progress_text.set(f"0 / {total}")
        self.root.update_idletasks()

        for path in self.selected_files:
            self._set_row_status(path, "Queued")

        for index, input_file in enumerate(self.selected_files, start=1):
            file_name = Path(input_file).name
            self._set_row_status(input_file, "Converting")
            self.status_text.set(f"Converting {file_name} ({index}/{total})")
            self.progress_text.set(f"{index - 1} / {total}")
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
                    self._set_row_status(input_file, "Done")
            except Exception:
                failed += 1
                self._set_row_status(input_file, "Failed")

            self.progress_value.set((index / total) * 100)

            elapsed = time.time() - start_time
            per_file = elapsed / index
            eta = int(per_file * (total - index))
            self.status_text.set(f"Converted {index}/{total} | ETA: {eta}s")
            self.progress_text.set(f"{index} / {total}")
            self.root.update_idletasks()

        self.last_output_dir = output_dir
        self.status_text.set(f"Completed. Success: {converted}, Failed: {failed}")
        messagebox.showinfo(
            "Conversion Finished",
            f"Completed.\n\nTotal files: {total}\nConverted: {converted}\nFailed: {failed}\nOutput folder: {output_dir}",
        )

    def run(self):
        self.root.mainloop()


def main():
    app = ImageFormatConverterApp()
    app.run()


if __name__ == "__main__":
    main()
