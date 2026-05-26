import tkinter as tk
from tkinter import ttk, messagebox
import queue
import threading
import pathlib
from datetime import datetime

from .recording_thread import RecordingThread

MAX_FEED_LINES = 50


class RecordingTab(ttk.Frame):
    def __init__(self, parent, base_dir):
        super().__init__(parent)
        self._base_dir = pathlib.Path(base_dir)
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = None
        self._session_count = 0
        self._after_id = None

        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)

        # Controller status
        status_frame = ttk.LabelFrame(self, text="Controller Status")
        status_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        status_frame.columnconfigure(0, weight=1)
        self._status_label = ttk.Label(status_frame, text="No controller connected.")
        self._status_label.grid(row=0, column=0, padx=8, pady=6, sticky="w")

        # Controls
        ctrl_frame = ttk.Frame(self)
        ctrl_frame.grid(row=1, column=0, pady=6)
        self._toggle_btn = ttk.Button(ctrl_frame, text="Start Recording", command=self._toggle_recording, width=20)
        self._toggle_btn.grid(row=0, column=0, padx=6)
        ttk.Button(ctrl_frame, text="Clear History", command=self._clear_history).grid(row=0, column=1, padx=6)

        # Session stats
        stats_frame = ttk.LabelFrame(self, text="Session Stats")
        stats_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=4)
        stats_frame.columnconfigure(0, weight=1)
        self._count_label = ttk.Label(stats_frame, text="Chats this session: 0", font=("", 11))
        self._count_label.grid(row=0, column=0, padx=8, pady=6, sticky="w")

        # Live feed
        feed_frame = ttk.LabelFrame(self, text="Live Feed")
        feed_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=(4, 10))
        feed_frame.columnconfigure(0, weight=1)
        feed_frame.rowconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._feed = tk.Text(feed_frame, state="disabled", wrap="word", height=16, font=("Consolas", 10))
        self._feed.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        sb = ttk.Scrollbar(feed_frame, orient="vertical", command=self._feed.yview)
        self._feed.configure(yscrollcommand=sb.set)
        sb.grid(row=0, column=1, sticky="ns")

    def _toggle_recording(self):
        if self._thread and self._thread.is_alive():
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        self._stop_event.clear()
        self._queue = queue.Queue()
        self._session_count = 0
        self._count_label.config(text="Chats this session: 0")
        self._thread = RecordingThread(self._queue, self._stop_event, self._base_dir)
        self._thread.start()
        self._toggle_btn.config(text="Stop Recording")
        self._status_label.config(text="Starting…")
        self._after_id = self.after(100, self._poll_queue)

    def _stop_recording(self):
        self._stop_event.set()
        self._toggle_btn.config(text="Start Recording", state="disabled")
        self._status_label.config(text="Stopping…")
        # poll will re-enable the button once "stopped" message arrives

    def _set_stopped_state(self):
        self._toggle_btn.config(text="Start Recording", state="normal")
        self._status_label.config(text="Recording stopped.")
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None

    def _poll_queue(self):
        try:
            while True:
                kind, data = self._queue.get_nowait()
                if kind == "chat":
                    self._session_count += 1
                    ts = datetime.now().strftime("%H:%M:%S")
                    self._append_feed(f"[{ts}] {data}")
                    self._count_label.config(text=f"Chats this session: {self._session_count}")
                elif kind == "controller":
                    self._status_label.config(text=f"Controller: {data}")
                elif kind == "autosave":
                    self._append_feed("[autosaved to recorded.txt]")
                elif kind == "error":
                    messagebox.showerror("Recording Error", data)
                    self._set_stopped_state()
                    return
                elif kind == "stopped":
                    self._set_stopped_state()
                    return
        except queue.Empty:
            pass

        if self._thread and self._thread.is_alive():
            self._after_id = self.after(100, self._poll_queue)

    def _append_feed(self, text):
        self._feed.config(state="normal")
        self._feed.insert("end", text + "\n")
        # Trim to MAX_FEED_LINES
        lines = int(self._feed.index("end-1c").split(".")[0])
        if lines > MAX_FEED_LINES:
            self._feed.delete("1.0", f"{lines - MAX_FEED_LINES}.0")
        self._feed.see("end")
        self._feed.config(state="disabled")

    def _clear_history(self):
        recorded = self._base_dir / "recorded.txt"
        try:
            open(recorded, "w").close()
        except Exception as e:
            messagebox.showerror("Error", f"Could not clear history:\n{e}")
            return
        self._feed.config(state="normal")
        self._feed.delete("1.0", "end")
        self._feed.config(state="disabled")
        self._session_count = 0
        self._count_label.config(text="Chats this session: 0")

    def stop_if_running(self):
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=3)
