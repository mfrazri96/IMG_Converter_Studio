import os
import time
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from easy_img_converter.config.constants import (
    APP_TITLE,
    COLORS,
    DEFAULT_REALESRGAN_WEIGHTS,
    ENHANCE_PROFILES,
    FORMAT_MAP,
    MIN_WINDOW_SIZE,
    REALESRGAN_MODELS,
    WINDOW_SIZE,
)
from easy_img_converter.features.converter import process_convert
from easy_img_converter.features.enhancer import (
    build_upsampler,
    process_enhance,
    validate_enhance_ready,
)
from easy_img_converter.services.file_queue import FileQueue
from easy_img_converter.services.output_naming import format_size


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_TITLE)
        self.root.geometry(WINDOW_SIZE)
        self.root.minsize(*MIN_WINDOW_SIZE)

        self.colors = COLORS
        self.root.configure(bg=self.colors["bg"])

        self.queue = FileQueue()
        self.preview_image_ref = None
        self.last_output_dir = None
        self.is_processing = False
        self.worker_thread = None
        self.busy_controls = []

        self.format_map = FORMAT_MAP

        self.mode = tk.StringVar(value="Convert")
        self.output_folder = tk.StringVar(value=str(Path.cwd()))
        self.target_format = tk.StringVar(value="PNG (.png)")
        self.quality = tk.IntVar(value=95)

        self.sr_model_name = tk.StringVar(value="RealESRGAN_x4plus")
        self.enhance_scale = tk.IntVar(value=4)
        self.enhance_profile = tk.StringVar(value="Quality")
        self.tile_size = tk.IntVar(value=400)
        self.model_path = tk.StringVar(value=str(DEFAULT_REALESRGAN_WEIGHTS))

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

        ttk.Label(main, text=APP_TITLE, style="Header.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            main,
            text="Convert or enhance images in bulk with live queue status and preview.",
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
        self._apply_mode_to_ui()
        self._apply_enhance_profile_to_settings(force=True)
        self._sync_model_path_with_selection(force=True)

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

        self.table.column("name", width=300, anchor="w")
        self.table.column("size", width=90, anchor="e")
        self.table.column("from", width=80, anchor="center")
        self.table.column("to", width=95, anchor="center")
        self.table.column("status", width=110, anchor="center")

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
        self.add_button = ttk.Button(actions, text="Add Images", command=self.add_images, style="Primary.TButton")
        self.add_button.pack(side="left")
        self.remove_button = ttk.Button(actions, text="Remove Selected", command=self.remove_selected, style="Soft.TButton")
        self.remove_button.pack(
            side="left", padx=(8, 0)
        )
        self.clear_button = ttk.Button(actions, text="Clear Queue", command=self.clear_images, style="Soft.TButton")
        self.clear_button.pack(
            side="left", padx=(8, 0)
        )

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
            height=220,
            bg="#eaf0f7",
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            bd=0,
        )
        self.preview_canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 8))
        self.preview_canvas.create_text(
            180,
            110,
            text="Select a file to preview",
            fill="#75879f",
            font=("Segoe UI", 10),
        )

        ttk.Label(preview_card, textvariable=self.preview_meta, style="PreviewMeta.TLabel").grid(row=2, column=0, sticky="w")

        settings_card = ttk.Frame(right, style="Card.TFrame", padding=14)
        settings_card.grid(row=1, column=0, sticky="nsew")
        settings_card.columnconfigure(1, weight=1)

        ttk.Label(settings_card, text="Settings", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(settings_card, text="Mode", style="Info.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 4))
        self.mode_combo = ttk.Combobox(
            settings_card, textvariable=self.mode, values=["Convert", "Enhance"], state="readonly", width=16
        )
        self.mode_combo.grid(row=1, column=1, sticky="w", pady=(10, 4))
        self.mode_combo.bind("<<ComboboxSelected>>", self.on_mode_change)

        self.convert_frame = ttk.Frame(settings_card, style="Card.TFrame")
        self.convert_frame.grid(row=2, column=0, columnspan=3, sticky="we", pady=(6, 0))
        self.convert_frame.columnconfigure(1, weight=1)

        ttk.Label(self.convert_frame, text="Target Format", style="Info.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        format_combo = ttk.Combobox(
            self.convert_frame,
            textvariable=self.target_format,
            values=list(self.format_map.keys()),
            state="readonly",
            width=18,
        )
        format_combo.grid(row=0, column=1, sticky="w", pady=(0, 4))
        format_combo.bind("<<ComboboxSelected>>", self.on_target_change)

        ttk.Label(self.convert_frame, text="Quality (JPEG/WEBP)", style="Info.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Spinbox(self.convert_frame, from_=1, to=100, textvariable=self.quality, width=6).grid(row=1, column=1, sticky="w")

        self.enhance_frame = ttk.Frame(settings_card, style="Card.TFrame")
        self.enhance_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=(8, 0))
        self.enhance_frame.columnconfigure(1, weight=1)

        ttk.Label(self.enhance_frame, text="Speed Profile", style="Info.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 4))
        self.profile_combo = ttk.Combobox(
            self.enhance_frame,
            textvariable=self.enhance_profile,
            values=ENHANCE_PROFILES,
            state="readonly",
            width=14,
        )
        self.profile_combo.grid(row=0, column=1, sticky="w", pady=(0, 4))
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_change)

        ttk.Label(self.enhance_frame, text="Real-ESRGAN Model", style="Info.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 4))
        self.model_combo = ttk.Combobox(
            self.enhance_frame,
            textvariable=self.sr_model_name,
            values=REALESRGAN_MODELS,
            state="readonly",
            width=24,
        )
        self.model_combo.grid(row=1, column=1, sticky="w", pady=(0, 4))
        self.model_combo.bind("<<ComboboxSelected>>", self.on_enhance_selection_change)

        ttk.Label(self.enhance_frame, text="Output Scale", style="Info.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 4))
        self.scale_combo = ttk.Combobox(
            self.enhance_frame, textvariable=self.enhance_scale, values=[2, 4], state="readonly", width=10
        )
        self.scale_combo.grid(
            row=2, column=1, sticky="w", pady=(0, 4)
        )
        self.scale_combo.bind("<<ComboboxSelected>>", self.on_enhance_scale_change)

        ttk.Label(self.enhance_frame, text="Tile Size", style="Info.TLabel").grid(row=3, column=0, sticky="w", pady=(0, 4))
        self.tile_spinbox = ttk.Spinbox(
            self.enhance_frame, from_=200, to=1200, increment=100, textvariable=self.tile_size, width=10
        )
        self.tile_spinbox.grid(
            row=3, column=1, sticky="w", pady=(0, 4)
        )

        ttk.Label(self.enhance_frame, text="Weights .pth path", style="Info.TLabel").grid(row=4, column=0, sticky="w", pady=(0, 4))
        self.weights_entry = ttk.Entry(self.enhance_frame, textvariable=self.model_path)
        self.weights_entry.grid(row=4, column=1, sticky="we", pady=(0, 4))
        self.weights_browse_button = ttk.Button(
            self.enhance_frame, text="Browse", command=self.select_model_file, style="Soft.TButton"
        )
        self.weights_browse_button.grid(
            row=4, column=2, padx=(8, 0), pady=(0, 4)
        )

        ttk.Label(settings_card, text="Output Folder", style="Info.TLabel").grid(row=4, column=0, sticky="w", pady=(8, 4))
        self.output_entry = ttk.Entry(settings_card, textvariable=self.output_folder)
        self.output_entry.grid(row=4, column=1, sticky="we", pady=(8, 4))
        self.output_browse_button = ttk.Button(settings_card, text="Browse", command=self.select_output_folder, style="Soft.TButton")
        self.output_browse_button.grid(
            row=4, column=2, padx=(8, 0), pady=(8, 4)
        )

        ttk.Separator(settings_card).grid(row=5, column=0, columnspan=3, sticky="we", pady=10)

        self.run_button = ttk.Button(settings_card, text="Start Conversion", command=self.start_jobs, style="Primary.TButton")
        self.run_button.grid(row=6, column=0, columnspan=3, sticky="we")
        self.open_output_button = ttk.Button(
            settings_card, text="Open Output Folder", command=self.open_output_folder, style="Soft.TButton"
        )
        self.open_output_button.grid(
            row=7, column=0, columnspan=3, sticky="we", pady=(8, 0)
        )

        self.progress = ttk.Progressbar(
            settings_card,
            variable=self.progress_value,
            maximum=100,
            style="Accent.Horizontal.TProgressbar",
        )
        self.progress.grid(row=8, column=0, columnspan=3, sticky="we", pady=(12, 6))

        status_row = ttk.Frame(settings_card, style="Card.TFrame")
        status_row.grid(row=9, column=0, columnspan=3, sticky="we")
        status_row.columnconfigure(0, weight=1)
        ttk.Label(status_row, textvariable=self.status_text, style="Info.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(status_row, textvariable=self.progress_text, style="Info.TLabel").grid(row=0, column=1, sticky="e")

        self.busy_controls = [
            self.add_button,
            self.remove_button,
            self.clear_button,
            self.mode_combo,
            self.profile_combo,
            self.model_combo,
            self.scale_combo,
            self.tile_spinbox,
            self.weights_entry,
            self.weights_browse_button,
            self.output_entry,
            self.output_browse_button,
            self.run_button,
        ]

    def _target_display(self):
        if self.mode.get() == "Convert":
            return self.format_map[self.target_format.get()][1].replace(".", "").upper()
        return "ENHANCE"

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

        target = self._target_display()
        added = 0
        for file_path in files:
            if self.queue.contains(file_path):
                continue

            file_info = Path(file_path)
            source_ext = file_info.suffix.replace(".", "").upper() or "-"
            size = format_size(file_info.stat().st_size) if file_info.exists() else "-"
            row_id = self.table.insert(
                "",
                "end",
                values=(file_info.name, size, source_ext, target, "Queued"),
                tags=("queued",),
            )
            self.queue.add(file_path, row_id)
            added += 1

        self.status_text.set(f"Added {added} new file(s).")
        self.progress_text.set(f"{len(self.queue)} queued")

    def remove_selected(self):
        selection = self.table.selection()
        if not selection:
            return

        for item_id in selection:
            self.queue.remove_by_row(item_id)
            self.table.delete(item_id)

        self.status_text.set("Selected file removed.")
        self.progress_text.set(f"{len(self.queue)} queued")

    def clear_images(self):
        self.queue.clear()
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

    def select_model_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Real-ESRGAN weights (.pth)",
            filetypes=[("PTH weights", "*.pth"), ("All files", "*.*")],
        )
        if file_path:
            self.model_path.set(file_path)

    def _suggest_model_path(self):
        model_name = self.sr_model_name.get()
        project_root = Path.cwd()
        model_dir = project_root / "Model"
        weights_dir = project_root / "weights"

        # Priority 1: exact filename match.
        exact_model = model_dir / f"{model_name}.pth"
        if exact_model.exists():
            return exact_model
        exact_weights = weights_dir / f"{model_name}.pth"
        if exact_weights.exists():
            return exact_weights

        # Priority 2: first matching variant (e.g. "RealESRGAN_x2plus (1).pth").
        for base_dir in (model_dir, weights_dir):
            if not base_dir.exists():
                continue
            candidates = sorted(base_dir.glob(f"{model_name}*.pth"))
            if candidates:
                return candidates[0]

        # Fallback path to show user the expected location.
        return exact_model

    def _sync_model_path_with_selection(self, force=False):
        suggested = self._suggest_model_path()
        current = Path(self.model_path.get()).expanduser() if self.model_path.get().strip() else None

        if force:
            self.model_path.set(str(suggested))
            return

        if current is None or current.name.startswith(self.sr_model_name.get()) or not current.exists():
            if suggested.exists():
                self.model_path.set(str(suggested))
            elif current is None:
                self.model_path.set(str(suggested))

    def open_output_folder(self):
        output_dir = self.last_output_dir or self.output_folder.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Invalid Folder", "Output folder does not exist.")
            return
        os.startfile(output_dir)

    def on_mode_change(self, _event=None):
        self._apply_mode_to_ui()
        self._refresh_target_column()

    def on_target_change(self, _event=None):
        if self.mode.get() == "Convert":
            self._refresh_target_column()

    def on_enhance_selection_change(self, _event=None):
        model_name = self.sr_model_name.get()
        if "x2plus" in model_name:
            self.enhance_scale.set(2)
        else:
            self.enhance_scale.set(4)
        self._sync_model_path_with_selection(force=True)
        self._sync_profile_from_settings()

    def on_enhance_scale_change(self, _event=None):
        # Keep model scale coherent with the selected output scale.
        if int(self.enhance_scale.get()) == 2 and self.sr_model_name.get() != "RealESRGAN_x2plus":
            self.sr_model_name.set("RealESRGAN_x2plus")
            self._sync_model_path_with_selection(force=True)
        elif int(self.enhance_scale.get()) == 4 and self.sr_model_name.get() == "RealESRGAN_x2plus":
            self.sr_model_name.set("RealESRGAN_x4plus")
            self._sync_model_path_with_selection(force=True)
        self._sync_profile_from_settings()

    def _apply_enhance_profile_to_settings(self, force=False):
        profile = self.enhance_profile.get()
        if profile == "Fast":
            self.sr_model_name.set("RealESRGAN_x2plus")
            self.enhance_scale.set(2)
            self.tile_size.set(800)
        else:
            self.sr_model_name.set("RealESRGAN_x4plus")
            self.enhance_scale.set(4)
            self.tile_size.set(400)

        self._sync_model_path_with_selection(force=force)
        self._refresh_target_column()

    def _sync_profile_from_settings(self):
        model = self.sr_model_name.get()
        scale = int(self.enhance_scale.get())
        if model == "RealESRGAN_x2plus" and scale == 2:
            self.enhance_profile.set("Fast")
        elif model == "RealESRGAN_x4plus" and scale == 4:
            self.enhance_profile.set("Quality")

    def on_profile_change(self, _event=None):
        self._apply_enhance_profile_to_settings(force=False)

    def _apply_mode_to_ui(self):
        if self.mode.get() == "Convert":
            self.convert_frame.grid()
            self.enhance_frame.grid_remove()
            self.run_button.configure(text="Start Conversion")
        else:
            self.convert_frame.grid_remove()
            self.enhance_frame.grid()
            self.run_button.configure(text="Start Enhancement")

    def _refresh_target_column(self):
        target = self._target_display()
        for row_id in self.table.get_children():
            values = list(self.table.item(row_id, "values"))
            values[3] = target
            self.table.item(row_id, values=values)

    def on_row_select(self, _event=None):
        selection = self.table.selection()
        if not selection:
            return

        row_id = selection[0]
        file_path = self.queue.path_for_row(row_id)
        if file_path:
            self._show_preview(file_path)

    def _clear_preview(self):
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            180,
            110,
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
                img_copy.thumbnail((340, 210))

                self.preview_image_ref = ImageTk.PhotoImage(img_copy)
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(170, 105, image=self.preview_image_ref)
                self.preview_meta.set(
                    f"{Path(file_path).name} | {width}x{height}px | {format_size(Path(file_path).stat().st_size)}"
                )
        except Exception:
            self.preview_meta.set("Preview unavailable")
            self._clear_preview()

    def _set_row_status(self, input_file, status):
        row_id = self.queue.row_for_path(input_file)
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

    def _set_busy_state(self, busy):
        self.is_processing = busy
        for control in self.busy_controls:
            try:
                control.configure(state="disabled" if busy else "normal")
            except tk.TclError:
                pass

        # Keep readonly combobox behavior when re-enabled.
        if not busy:
            for combo in (self.mode_combo, self.profile_combo, self.model_combo, self.scale_combo):
                combo.configure(state="readonly")

    def _finish_jobs(self, mode, total, completed, failed, skipped, output_dir):
        self.last_output_dir = output_dir
        self.status_text.set(f"Completed. Success: {completed}, Failed: {failed}, Skipped: {skipped}")
        self._set_busy_state(False)
        messagebox.showinfo(
            "Job Finished",
            f"Mode: {mode}\n\nTotal files: {total}\nSuccess: {completed}\nSkipped: {skipped}\nFailed: {failed}\nOutput folder: {output_dir}",
        )

    def _handle_worker_error(self, title, error_text):
        self.status_text.set("Failed to start processing.")
        self._set_busy_state(False)
        messagebox.showerror(title, error_text)

    def _run_jobs_worker(self, job):
        mode = job["mode"]
        files = job["files"]
        output_dir = job["output_dir"]
        total = len(files)
        completed = 0
        failed = 0
        skipped = 0
        start_time = time.time()

        upsampler = None
        if mode == "Enhance":
            try:
                upsampler = build_upsampler(
                    weights_path=job["weights_path"],
                    model_name=job["model_name"],
                    tile=job["tile_size"],
                )
            except Exception as exc:
                self.root.after(0, self._handle_worker_error, "Enhancement Setup Error", str(exc))
                return

        for index, input_file in enumerate(files, start=1):
            file_name = Path(input_file).name
            self.root.after(0, self._set_row_status, input_file, "Converting")
            self.root.after(0, self.status_text.set, f"{mode}: {file_name} ({index}/{total})")
            self.root.after(0, self.progress_text.set, f"{index - 1} / {total}")

            try:
                if mode == "Convert":
                    process_convert(
                        input_file=input_file,
                        output_dir=output_dir,
                        save_format=job["save_format"],
                        extension=job["extension"],
                        quality=job["quality"],
                    )
                    completed += 1
                else:
                    process_enhance(
                        input_file=input_file,
                        output_dir=output_dir,
                        upsampler=upsampler,
                        model_name=job["model_name"],
                        outscale=job["outscale"],
                    )
                    completed += 1
                self.root.after(0, self._set_row_status, input_file, "Done")
            except Exception:
                failed += 1
                self.root.after(0, self._set_row_status, input_file, "Failed")

            progress_percent = (index / total) * 100
            elapsed = time.time() - start_time
            per_file = elapsed / index
            eta = int(per_file * (total - index))
            self.root.after(0, self.progress_value.set, progress_percent)
            self.root.after(0, self.status_text.set, f"Processed {index}/{total} | ETA: {eta}s")
            self.root.after(0, self.progress_text.set, f"{index} / {total}")

        self.root.after(0, self._finish_jobs, mode, total, completed, failed, skipped, output_dir)

    def start_jobs(self):
        if self.is_processing:
            messagebox.showinfo("Processing", "A job is already running. Please wait until it finishes.")
            return

        if not self.queue.selected_files:
            messagebox.showerror("No Images Selected", "Please add at least one image file.")
            return

        output_dir = self.output_folder.get().strip()
        if not output_dir:
            messagebox.showerror("No Output Folder", "Please choose an output folder.")
            return

        if not os.path.isdir(output_dir):
            messagebox.showerror("Invalid Folder", "The selected output folder does not exist.")
            return

        mode = self.mode.get()
        if mode == "Convert":
            format_name = self.target_format.get()
            if format_name not in self.format_map:
                messagebox.showerror("Invalid Format", "Please choose a valid target format.")
                return

        job = {
            "mode": mode,
            "output_dir": output_dir,
            "files": list(self.queue.selected_files),
        }

        if mode == "Enhance":
            try:
                selected_model = self.sr_model_name.get()
                selected_weights = Path(self.model_path.get().strip())
                if selected_weights.name and selected_model not in selected_weights.name:
                    suggested = self._suggest_model_path()
                    if suggested.exists():
                        self.model_path.set(str(suggested))
                        selected_weights = suggested
                    else:
                        raise RuntimeError(
                            f"Selected model '{selected_model}' does not match weights file '{selected_weights.name}'. "
                            "Please choose matching weights."
                        )

                validate_enhance_ready(
                    weights_path=str(selected_weights),
                    model_name=selected_model,
                )
                job.update(
                    {
                        "model_name": selected_model,
                        "weights_path": str(selected_weights),
                        "outscale": int(self.enhance_scale.get()),
                        "tile_size": int(self.tile_size.get()),
                    }
                )
            except Exception as exc:
                messagebox.showerror("Enhancement Setup Error", str(exc))
                return
        else:
            format_name = self.target_format.get()
            save_format, extension = self.format_map[format_name]
            quality = max(1, min(100, int(self.quality.get())))
            job.update(
                {
                    "save_format": save_format,
                    "extension": extension,
                    "quality": quality,
                }
            )

        total = len(job["files"])
        self._set_busy_state(True)

        self.progress_value.set(0)
        self.progress_text.set(f"0 / {total}")
        self.status_text.set("Starting...")

        for path in job["files"]:
            self._set_row_status(path, "Queued")

        self.worker_thread = threading.Thread(
            target=self._run_jobs_worker,
            args=(job,),
            daemon=True,
        )
        self.worker_thread.start()

    def run(self):
        self.root.mainloop()
