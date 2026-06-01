import customtkinter as ctk
from tkinter import simpledialog, messagebox

import database as db


class ProfilesTab(ctk.CTkFrame):
    def __init__(self, parent, on_profile_change):
        super().__init__(parent, fg_color="transparent")
        self.on_profile_change = on_profile_change
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(top, text="Voice Profiles", font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        ctk.CTkButton(top, text="+ Profil Baru", width=120, command=self._add_profile).pack(side="right")

        self.cards_frame = ctk.CTkScrollableFrame(self, label_text="")
        self.cards_frame.pack(fill="both", expand=True, padx=16, pady=8)
        self.cards_frame.grid_columnconfigure((0, 1, 2), weight=1)

    def refresh(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

        profiles = db.get_all_profiles()
        if not profiles:
            ctk.CTkLabel(
                self.cards_frame,
                text="Belum ada profil.\nKlik '+ Profil Baru' untuk memulai.",
                font=ctk.CTkFont(size=14),
                text_color="gray",
            ).grid(row=0, column=0, columnspan=3, pady=60)
            return

        for i, p in enumerate(profiles):
            self._make_card(p, i)

    def _make_card(self, profile: dict, index: int):
        card = ctk.CTkFrame(self.cards_frame, corner_radius=12)
        card.grid(row=index // 3, column=index % 3, padx=8, pady=8, sticky="nsew")

        avatar = ctk.CTkFrame(card, width=60, height=60, corner_radius=30, fg_color="#1f538d")
        avatar.pack(pady=(16, 8))
        ctk.CTkLabel(avatar, text=profile["name"][0].upper(),
                     font=ctk.CTkFont(size=24, weight="bold")).place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=profile["name"],
                     font=ctk.CTkFont(size=14, weight="bold"),
                     wraplength=160).pack()

        word_count = profile.get("word_count", 0)
        ctk.CTkLabel(card, text=f"{word_count} kata",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(pady=2)

        created = profile.get("created_at", "")[:10]
        ctk.CTkLabel(card, text=created,
                     font=ctk.CTkFont(size=11), text_color="gray").pack()

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=12)

        ctk.CTkButton(btn_frame, text="Pilih", width=80,
                      command=lambda pid=profile["id"]: self._select(pid)).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Hapus", width=80, fg_color="#c0392b", hover_color="#922b21",
                      command=lambda pid=profile["id"], name=profile["name"]: self._delete(pid, name)
                      ).pack(side="left", padx=4)

    def _add_profile(self):
        name = simpledialog.askstring("Profil Baru", "Nama profil (contoh: Jokowi, Prabowo):")
        if name and name.strip():
            pid = db.create_profile(name.strip())
            self.refresh()
            self.on_profile_change(pid)

    def _select(self, profile_id: str):
        self.on_profile_change(profile_id)

    def _delete(self, profile_id: str, name: str):
        if messagebox.askyesno("Hapus Profil", f"Hapus profil '{name}' beserta semua kata?\nAksi ini tidak bisa dibatalkan."):
            import shutil
            from paths import data_dir
            wdir = data_dir() / "profiles" / profile_id
            if wdir.exists():
                shutil.rmtree(wdir)
            db.delete_profile(profile_id)
            self.refresh()
            self.on_profile_change(None)
