import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import pathlib
import shutil
import threading
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
import image_parser

DIRECTIONS = ["up", "left", "right", "down"]


class SetupTab(ttk.Frame):
    def __init__(self, parent, base_dir):
        super().__init__(parent)
        self._base_dir = pathlib.Path(base_dir)
        self._qc_options = self._load_qc_options()
        self._phrase_to_id = {v: k for k, v in self._qc_options.items()}
        self._cells = {}  # (row_dir, col_dir) -> ttk.Combobox

        self._build_ui()
        self._refresh_mapping_display()

    def _load_qc_options(self):
        p = self._base_dir / "qc_options.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _load_image_filled(self):
        p = self._base_dir / "image_filled.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        # --- Section A: Screenshot upload ---
        upload_frame = ttk.LabelFrame(self, text="Setup from Screenshot (OCR)")
        upload_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        upload_frame.columnconfigure(1, weight=1)

        ttk.Button(upload_frame, text="Upload Screenshot", command=self._on_upload).grid(
            row=0, column=0, padx=8, pady=8
        )
        self._ocr_status = ttk.Label(upload_frame, text="No screenshot processed yet.")
        self._ocr_status.grid(row=0, column=1, padx=8, pady=8, sticky="w")
        self._progress = ttk.Progressbar(upload_frame, mode="indeterminate")
        self._progress.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))

        # --- Section B: Manual 4x4 grid editor ---
        grid_frame = ttk.LabelFrame(self, text="Manual Mapping Editor")
        grid_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=4)

        phrases = list(self._qc_options.values())

        # Header row
        ttk.Label(grid_frame, text="1st \\ 2nd", font=("", 9, "bold")).grid(
            row=0, column=0, padx=4, pady=4
        )
        for ci, col_dir in enumerate(DIRECTIONS):
            ttk.Label(grid_frame, text=col_dir.upper(), font=("", 9, "bold")).grid(
                row=0, column=ci + 1, padx=4, pady=4
            )

        for ri, row_dir in enumerate(DIRECTIONS):
            ttk.Label(grid_frame, text=row_dir.upper(), font=("", 9, "bold")).grid(
                row=ri + 1, column=0, padx=4, pady=4
            )
            for ci, col_dir in enumerate(DIRECTIONS):
                cb = ttk.Combobox(grid_frame, values=phrases, width=22, state="readonly")
                cb.grid(row=ri + 1, column=ci + 1, padx=3, pady=3)
                self._cells[(row_dir, col_dir)] = cb

        ttk.Button(grid_frame, text="Save Mapping", command=self._on_save_mapping).grid(
            row=len(DIRECTIONS) + 1, column=0, columnspan=len(DIRECTIONS) + 1,
            pady=8
        )

        self._populate_grid_from_file()

        # --- Section C: Current mapping display ---
        display_frame = ttk.LabelFrame(self, text="Current Mapping")
        display_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(4, 10))
        self.rowconfigure(2, weight=1)
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(0, weight=1)

        cols = ("first", "second", "chat")
        self._tree = ttk.Treeview(display_frame, columns=cols, show="headings", height=8)
        self._tree.heading("first", text="First Press")
        self._tree.heading("second", text="Second Press")
        self._tree.heading("chat", text="Quick Chat")
        self._tree.column("first", width=90, anchor="center")
        self._tree.column("second", width=90, anchor="center")
        self._tree.column("chat", width=260)
        self._tree.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(display_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

    def _populate_grid_from_file(self):
        mapping = self._load_image_filled()
        for (row_dir, col_dir), cb in self._cells.items():
            qc_id = mapping.get(row_dir, {}).get(col_dir)
            phrase = self._qc_options.get(qc_id, "")
            if phrase in cb["values"]:
                cb.set(phrase)
            else:
                cb.set("")

    def _refresh_mapping_display(self):
        for row in self._tree.get_children():
            self._tree.delete(row)
        mapping = self._load_image_filled()
        for row_dir in DIRECTIONS:
            for col_dir in DIRECTIONS:
                qc_id = mapping.get(row_dir, {}).get(col_dir)
                phrase = self._qc_options.get(qc_id, "?") if qc_id else "—"
                self._tree.insert("", "end", values=(row_dir, col_dir, phrase))

    def _on_upload(self):
        path = filedialog.askopenfilename(
            title="Select Quick Chat Screenshot",
            filetypes=[("Images", "*.png *.jpg *.bmp *.jpeg"), ("All files", "*.*")]
        )
        if not path:
            return

        dest = self._base_dir / "image.png"
        if pathlib.Path(path).resolve() != dest.resolve():
            shutil.copy(path, dest)
        self._ocr_status.config(text="Running OCR… this may take a few seconds.")
        self._progress.start(10)

        def _run():
            try:
                image_parser.parse(
                    str(dest),
                    str(self._base_dir / "qc_options.json"),
                    str(self._base_dir / "image_filled.json"),
                )
                self.after(0, self._on_ocr_done, True, None)
            except Exception as e:
                self.after(0, self._on_ocr_done, False, str(e))

        threading.Thread(target=_run, daemon=True).start()

    def _on_ocr_done(self, success, error):
        self._progress.stop()
        if success:
            self._ocr_status.config(text="OCR complete — mapping updated.")
            self._populate_grid_from_file()
            self._refresh_mapping_display()
        else:
            self._ocr_status.config(text=f"OCR failed: {error}")
            messagebox.showerror("OCR Error", f"Screenshot parsing failed:\n{error}")

    def _on_save_mapping(self):
        mapping = {}
        for (row_dir, col_dir), cb in self._cells.items():
            phrase = cb.get()
            qc_id = self._phrase_to_id.get(phrase)
            if row_dir not in mapping:
                mapping[row_dir] = {}
            mapping[row_dir][col_dir] = qc_id

        out = self._base_dir / "image_filled.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=4)

        self._refresh_mapping_display()
        messagebox.showinfo("Saved", "Mapping saved to image_filled.json")
