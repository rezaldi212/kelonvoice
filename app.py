import customtkinter as ctk

import database as db
from tabs.profiles_tab import ProfilesTab
from tabs.build_tab import BuildTab
from tabs.wordbank_tab import WordBankTab
from tabs.compose_tab import ComposeTab

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        db.init_db()
        self.title("kelonvoice — Voice Word Bank")
        self.geometry("960x680")
        self.minsize(800, 600)
        self._active_profile: str | None = None
        self._build_ui()

    def _build_ui(self):
        sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        ctk.CTkLabel(sidebar, text="kelonvoice", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(sidebar, text="Voice Word Bank", font=ctk.CTkFont(size=11), text_color="gray").pack(pady=(0, 24))
        self.sidebar_profile = ctk.CTkLabel(sidebar, text="Tidak ada profil aktif", font=ctk.CTkFont(size=11), text_color="gray", wraplength=180)
        self.sidebar_profile.pack(pady=(0, 20), padx=10)
        nav_buttons = {}
        tabs_info = [("profiles", "👤  Profiles"), ("build", "⚙️   Build"), ("wordbank", "📚  Word Bank"), ("compose", "🎙  Compose")]

        def make_nav(key, label):
            btn = ctk.CTkButton(sidebar, text=label, height=40, fg_color="transparent", text_color=("gray10", "gray90"), hover_color=("gray85", "gray25"), anchor="w", font=ctk.CTkFont(size=13), command=lambda k=key: self._switch_tab(k))
            btn.pack(fill="x", padx=10, pady=3)
            nav_buttons[key] = btn

        for k, l in tabs_info:
            make_nav(k, l)
        self._nav_buttons = nav_buttons
        self._main = ctk.CTkFrame(self, corner_radius=0, fg_color=("gray95", "gray10"))
        self._main.pack(side="right", fill="both", expand=True)
        self._tabs = {
            "profiles": ProfilesTab(self._main, self._on_profile_change),
            "build": BuildTab(self._main, lambda: self._active_profile),
            "wordbank": WordBankTab(self._main, lambda: self._active_profile),
            "compose": ComposeTab(self._main, lambda: self._active_profile),
        }
        self._current_tab = None
        self._switch_tab("profiles")

    def _switch_tab(self, key: str):
        if self._current_tab == key:
            return
        if self._current_tab and self._current_tab in self._tabs:
            self._tabs[self._current_tab].pack_forget()
        self._current_tab = key
        tab = self._tabs[key]
        tab.pack(fill="both", expand=True)
        for k, btn in self._nav_buttons.items():
            btn.configure(fg_color="#1f538d" if k == key else "transparent")
        if key == "wordbank":
            tab.refresh(self._active_profile)
        elif key == "build":
            tab.refresh_profile(self._active_profile)
        elif key == "compose":
            tab.refresh_profile(self._active_profile)

    def _on_profile_change(self, profile_id: str | None):
        self._active_profile = profile_id
        if profile_id:
            p = db.get_profile(profile_id)
            label = f"Aktif: {p['name']}" if p else "—"
        else:
            label = "Tidak ada profil aktif"
        self.sidebar_profile.configure(text=label, text_color="#1f77b4" if profile_id else "gray")
        if hasattr(self._tabs.get("build"), "refresh_profile"):
            self._tabs["build"].refresh_profile(profile_id)
        if hasattr(self._tabs.get("compose"), "refresh_profile"):
            self._tabs["compose"].refresh_profile(profile_id)
