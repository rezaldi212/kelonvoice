import tempfile
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pygame

import database as db
import composer


class ComposeTab(ctk.CTkFrame):
    def __init__(self, parent, get_active_profile):
        super().__init__(parent, fg_color="transparent")
        self.get_active_profile = get_active_profile
        self._last_wav: bytes | None = None
        pygame.mixer.init()
        self._build_ui()

    def _build_ui(self):
        ctk.CTkLabel(self, text="Compose TTS", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=16, pady=(16, 4))
        prof_frame = ctk.CTkFrame(self)
        prof_frame.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(prof_frame, text="Voice / Karakter:", font=ctk.CTkFont(size=13)).pack(side="left", padx=12, pady=10)
        self.profile_label = ctk.CTkLabel(prof_frame, text="—", font=ctk.CTkFont(size=13, weight="bold"), text_color="#1f77b4")
        self.profile_label.pack(side="left")
        text_frame = ctk.CTkFrame(self)
        text_frame.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(text_frame, text="Kalimat:", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.text_input = ctk.CTkTextbox(text_frame, height=100, font=ctk.CTkFont(size=14))
        self.text_input.pack(fill="x", padx=12, pady=(0, 12))
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=4)
        ctk.CTkButton(btn_frame, text="▶  Generate & Play", height=44, font=ctk.CTkFont(size=14, weight="bold"), command=self._generate).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btn_frame, text="💾  Export MP3", height=44, fg_color="#27ae60", hover_color="#1e8449", command=self._export).pack(side="left")
        ctk.CTkButton(btn_frame, text="⏹", height=44, width=44, fg_color="#7f8c8d", hover_color="#5d6d7e", command=self._stop).pack(side="left", padx=8)
        result_frame = ctk.CTkFrame(self)
        result_frame.pack(fill="both", expand=True, padx=16, pady=8)
        ctk.CTkLabel(result_frame, text="Hasil", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", padx=12, pady=(10, 4))
        self.result_label = ctk.CTkLabel(result_frame, text="Ketik kalimat dan tekan Generate.", font=ctk.CTkFont(size=12), text_color="gray", wraplength=500, justify="left")
        self.result_label.pack(anchor="w", padx=12)
        self.missing_box = ctk.CTkScrollableFrame(result_frame, height=80, label_text="Kata tidak tersedia")
        self.missing_box.pack(fill="x", padx=12, pady=8)

    def refresh_profile(self, profile_id):
        if profile_id:
            p = db.get_profile(profile_id)
            self.profile_label.configure(text=p["name"] if p else "—")
        else:
            self.profile_label.configure(text="—")

    def _generate(self):
        profile_id = self.get_active_profile()
        if not profile_id:
            messagebox.showwarning("Profil", "Pilih profil terlebih dahulu.")
            return
        sentence = self.text_input.get("1.0", "end").strip()
        if not sentence:
            return
        wav_bytes, missing = composer.compose(profile_id, sentence)
        self._last_wav = wav_bytes
        for w in self.missing_box.winfo_children():
            w.destroy()
        if missing:
            self.result_label.configure(text=f"Berhasil dengan {len(missing)} kata yang diganti keheningan.", text_color="#e67e22")
            for word in missing:
                ctk.CTkLabel(self.missing_box, text=word, font=ctk.CTkFont(size=12), fg_color="#c0392b", corner_radius=4, padx=6, pady=2).pack(side="left", padx=3, pady=2)
        else:
            self.result_label.configure(text="Semua kata ditemukan. Audio siap diputar.", text_color="#2ecc71")
        if wav_bytes:
            self._play_bytes(wav_bytes)

    def _play_bytes(self, wav_bytes: bytes):
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(wav_bytes)
            tmp.close()
            pygame.mixer.music.load(tmp.name)
            pygame.mixer.music.play()
        except Exception as e:
            messagebox.showerror("Playback Error", str(e))

    def _stop(self):
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass

    def _export(self):
        if not self._last_wav:
            messagebox.showwarning("Export", "Generate audio terlebih dahulu.")
            return
        path = filedialog.asksaveasfilename(title="Simpan sebagai", defaultextension=".mp3", filetypes=[("MP3", "*.mp3"), ("WAV", "*.wav")])
        if not path:
            return
        try:
            from pydub import AudioSegment
            import io
            audio = AudioSegment.from_wav(io.BytesIO(self._last_wav))
            fmt = "mp3" if path.endswith(".mp3") else "wav"
            audio.export(path, format=fmt)
            messagebox.showinfo("Export", f"Disimpan ke:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
