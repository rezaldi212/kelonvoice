import customtkinter as ctk
import pygame
from pathlib import Path

import database as db


class WordBankTab(ctk.CTkFrame):
    def __init__(self, parent, get_active_profile):
        super().__init__(parent, fg_color="transparent")
        self.get_active_profile = get_active_profile
        self._current_words = []
        pygame.mixer.init()
        self._build_ui()

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 4))
        ctk.CTkLabel(top, text="Word Bank", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        self.count_label = ctk.CTkLabel(top, text="", font=ctk.CTkFont(size=13), text_color="gray")
        self.count_label.pack(side="left", padx=12)
        self.profile_label = ctk.CTkLabel(top, text="Profil: —", font=ctk.CTkFont(size=13), text_color="#1f77b4")
        self.profile_label.pack(side="right")
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=6)
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter())
        ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Cari kata…", height=36).pack(fill="x")
        self.word_list = ctk.CTkScrollableFrame(self, label_text="")
        self.word_list.pack(fill="both", expand=True, padx=16, pady=8)

    def refresh(self, profile_id=None):
        pid = profile_id or self.get_active_profile()
        if not pid:
            self._show_empty("Pilih profil terlebih dahulu.")
            return
        p = db.get_profile(pid)
        self.profile_label.configure(text=f"Profil: {p['name']}" if p else "Profil: —")
        self._current_words = db.get_words_for_profile(pid)
        self._render_words(self._current_words)

    def _filter(self):
        query = self.search_var.get().strip().lower()
        pid = self.get_active_profile()
        if not pid:
            return
        filtered = db.get_words_for_profile(pid, query)
        self._render_words(filtered)

    def _render_words(self, words: list):
        for w in self.word_list.winfo_children():
            w.destroy()
        unique = {}
        for w in words:
            unique.setdefault(w["word"], []).append(w)
        self.count_label.configure(text=f"{len(unique)} kata unik")
        if not unique:
            self._show_empty("Tidak ada kata ditemukan.")
            return
        for i, (word, instances) in enumerate(sorted(unique.items())):
            row = ctk.CTkFrame(self.word_list, corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=word, font=ctk.CTkFont(size=13, weight="bold"), width=160, anchor="w").pack(side="left", padx=(12, 0), pady=8)
            ctk.CTkLabel(row, text=f"{len(instances)} instance", font=ctk.CTkFont(size=11), text_color="gray", width=80).pack(side="left")
            best = max(instances, key=lambda x: x.get("confidence", 0))
            conf = best.get("confidence", 0)
            ctk.CTkLabel(row, text=f"conf: {conf:.2f}", font=ctk.CTkFont(size=11), text_color="gray").pack(side="left", padx=8)
            ctk.CTkButton(row, text="▶ Play", width=70, command=lambda fp=best["file_path"]: self._play(fp)).pack(side="right", padx=8, pady=6)

    def _play(self, file_path: str):
        p = Path(file_path)
        if not p.exists():
            return
        try:
            pygame.mixer.music.load(str(p))
            pygame.mixer.music.play()
        except Exception:
            pass

    def _show_empty(self, msg: str):
        for w in self.word_list.winfo_children():
            w.destroy()
        ctk.CTkLabel(self.word_list, text=msg, font=ctk.CTkFont(size=14), text_color="gray").pack(pady=40)
