import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

import database as db
import pipeline as pl


class BuildTab(ctk.CTkFrame):
    def __init__(self, parent, get_active_profile):
        super().__init__(parent, fg_color="transparent")
        self.get_active_profile = get_active_profile
        self._running = False
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Build Word Bank",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=16, pady=(16, 4))
        self.profile_label = ctk.CTkLabel(self, text="Profil aktif: —",
                                           font=ctk.CTkFont(size=13), text_color="gray")
        self.profile_label.pack(anchor="w", padx=16, pady=(0, 12))
        src_frame = ctk.CTkFrame(self)
        src_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(src_frame, text="Sumber Audio", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))
        self.source_var = ctk.StringVar(value="url")
        radio_frame = ctk.CTkFrame(src_frame, fg_color="transparent")
        radio_frame.pack(fill="x", padx=12)
        ctk.CTkRadioButton(radio_frame, text="YouTube URL", variable=self.source_var, value="url", command=self._toggle_source).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(radio_frame, text="File Lokal", variable=self.source_var, value="file", command=self._toggle_source).pack(side="left")
        self.url_frame = ctk.CTkFrame(src_frame, fg_color="transparent")
        self.url_frame.pack(fill="x", padx=12, pady=6)
        self.url_entry = ctk.CTkEntry(self.url_frame, placeholder_text="https://youtube.com/watch?v=...", height=36)
        self.url_entry.pack(fill="x")
        self.file_frame = ctk.CTkFrame(src_frame, fg_color="transparent")
        self.file_path_var = tk.StringVar()
        file_row = ctk.CTkFrame(self.file_frame, fg_color="transparent")
        file_row.pack(fill="x")
        self.file_entry = ctk.CTkEntry(file_row, textvariable=self.file_path_var, placeholder_text="Pilih file video/audio…", height=36)
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(file_row, text="Browse", width=80, command=self._browse_file).pack(side="right")
        ctk.CTkFrame(src_frame, height=8, fg_color="transparent").pack()
        time_frame = ctk.CTkFrame(self)
        time_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(time_frame, text="Rentang Waktu (opsional)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        ctk.CTkLabel(time_frame, text="Format: mm:ss atau hh:mm:ss — kosongkan jika ingin proses seluruh audio", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=12)
        time_row = ctk.CTkFrame(time_frame, fg_color="transparent")
        time_row.pack(fill="x", padx=12, pady=(6, 12))
        ctk.CTkLabel(time_row, text="Mulai:", width=40).pack(side="left")
        self.start_entry = ctk.CTkEntry(time_row, placeholder_text="0:00", width=90, height=32)
        self.start_entry.pack(side="left", padx=(4, 20))
        ctk.CTkLabel(time_row, text="Selesai:", width=50).pack(side="left")
        self.end_entry = ctk.CTkEntry(time_row, placeholder_text="5:30", width=90, height=32)
        self.end_entry.pack(side="left", padx=4)
        self.start_btn = ctk.CTkButton(self, text="▶  Mulai Proses", height=44, font=ctk.CTkFont(size=14, weight="bold"), command=self._start)
        self.start_btn.pack(fill="x", padx=16, pady=12)
        prog_frame = ctk.CTkFrame(self)
        prog_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkLabel(prog_frame, text="Progress", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.progress_bar = ctk.CTkProgressBar(prog_frame)
        self.progress_bar.pack(fill="x", padx=12, pady=4)
        self.progress_bar.set(0)
        self.status_label = ctk.CTkLabel(prog_frame, text="Menunggu…", font=ctk.CTkFont(size=12), text_color="gray")
        self.status_label.pack(anchor="w", padx=12, pady=(0, 12))
        self._toggle_source()

    def _toggle_source(self):
        if self.source_var.get() == "url":
            self.url_frame.pack(fill="x", padx=12, pady=6)
            self.file_frame.pack_forget()
        else:
            self.url_frame.pack_forget()
            self.file_frame.pack(fill="x", padx=12, pady=6)

    def _parse_time(self, text: str) -> float | None:
        if not text:
            return None
        parts = text.split(":")
        try:
            if len(parts) == 1:
                return float(parts[0])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + float(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
        return None

    def _browse_file(self):
        path = filedialog.askopenfilename(
            title="Pilih file video/audio",
            filetypes=[("Video/Audio", "*.mp4 *.mkv *.avi *.mov *.mp3 *.wav *.m4a"), ("Semua", "*.*")]
        )
        if path:
            self.file_path_var.set(path)

    def refresh_profile(self, profile_id):
        if profile_id:
            p = db.get_profile(profile_id)
            self.profile_label.configure(text=f"Profil aktif: {p['name']}")
        else:
            self.profile_label.configure(text="Profil aktif: —")

    def _start(self):
        if self._running:
            return
        profile_id = self.get_active_profile()
        if not profile_id:
            messagebox.showwarning("Profil", "Pilih atau buat profil terlebih dahulu di tab Profiles.")
            return
        is_url = self.source_var.get() == "url"
        if is_url:
            source = self.url_entry.get().strip()
            if not source:
                messagebox.showwarning("URL", "Masukkan URL YouTube.")
                return
        else:
            source = self.file_path_var.get().strip()
            if not source:
                messagebox.showwarning("File", "Pilih file audio/video.")
                return
        start_sec = self._parse_time(self.start_entry.get().strip())
        end_sec = self._parse_time(self.end_entry.get().strip())
        if start_sec is None and self.start_entry.get().strip():
            messagebox.showwarning("Waktu", "Format waktu mulai tidak valid. Gunakan mm:ss atau hh:mm:ss.")
            return
        if end_sec is None and self.end_entry.get().strip():
            messagebox.showwarning("Waktu", "Format waktu selesai tidak valid. Gunakan mm:ss atau hh:mm:ss.")
            return
        if start_sec is not None and end_sec is not None and end_sec <= start_sec:
            messagebox.showwarning("Waktu", "Waktu selesai harus lebih besar dari waktu mulai.")
            return
        self._running = True
        self.start_btn.configure(state="disabled", text="Memproses…")
        self.progress_bar.set(0)
        pl.run_pipeline(profile_id=profile_id, source=source, is_url=is_url, start_sec=start_sec, end_sec=end_sec, progress_cb=self._on_progress, done_cb=self._on_done)

    def _on_progress(self, message: str, percent: int):
        self.after(0, lambda: self._update_progress(message, percent))

    def _update_progress(self, message, percent):
        self.status_label.configure(text=message)
        self.progress_bar.set(percent / 100)

    def _on_done(self, success: bool, message: str):
        self.after(0, lambda: self._finish(success, message))

    def _finish(self, success, message):
        self._running = False
        self.start_btn.configure(state="normal", text="▶  Mulai Proses")
        self.status_label.configure(text=message, text_color="#2ecc71" if success else "#e74c3c")
        if success:
            self.progress_bar.set(1)
