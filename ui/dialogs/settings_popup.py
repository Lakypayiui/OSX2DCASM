"""Settings popup — UI volume, music volume, background animation toggle.

Settings are persisted to ``settings.json`` in the project root.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

import pygame

from widgets.button import Button, set_ui_volume
from widgets.label import Label
from widgets.popup import Popup
from widgets.slider import Slider

_SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "settings.json"


def load_settings() -> dict:
    """Return the current settings dict, loading defaults if no file exists."""
    defaults = {"ui_volume": 0.5, "music_volume": 0.5, "bg_animation": True}
    try:
        with open(_SETTINGS_PATH) as fh:
            data = json.load(fh)
        return {**defaults, **data}
    except (FileNotFoundError, json.JSONDecodeError):
        return defaults


def save_settings(data: dict) -> None:
    """Persist *data* to the settings JSON file."""
    with open(_SETTINGS_PATH, "w") as fh:
        json.dump(data, fh, indent=2)


def apply_music_volume(volume: float) -> None:
    """Set the volume of the pygame music channel."""
    try:
        pygame.mixer.music.set_volume(volume)
    except Exception:
        pass


class SettingsPopup(Popup):
    """Modal popup for changing volume, music, and background animation."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        on_close: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(rect)
        self.on_close = on_close

        settings = load_settings()
        self.ui_vol: float = settings["ui_volume"]
        self.music_vol: float = settings["music_volume"]
        self.bg_animation: bool = settings["bg_animation"]

        self._build_widgets()

        # Apply persisted volumes immediately
        set_ui_volume(self.ui_vol)
        apply_music_volume(self.music_vol)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_widgets(self) -> None:
        rx, ry = self.rect.x, self.rect.y

        self._title = Label(
            (rx + 20, ry + 50), "Settings", self.fb, (230, 230, 240),
        )

        # --- UI volume ---
        self._ui_label = Label(
            (rx + 20, ry + 90), "UI Volume", self.fn, (210, 210, 220),
        )
        self.slider_ui = Slider(
            (rx + 20, ry + 115, 310, 12), self.fn, value=self.ui_vol,
        )

        # --- Music volume ---
        self._music_label = Label(
            (rx + 20, ry + 145), "Music Volume", self.fn, (210, 210, 220),
        )
        self.slider_music = Slider(
            (rx + 20, ry + 170, 310, 12), self.fn, value=self.music_vol,
        )

        # --- Mute toggle ---
        self.btn_mute = Button(
            (rx + 20, ry + 200, 140, 30), "Mute", self.fn, toggle=True,
            bg=(120, 40, 40), fg=(255, 255, 255),
            bg_on=(180, 60, 60), fg_on=(255, 255, 255),
        )

        # --- Background animation toggle ---
        self.btn_bg_anim = Button(
            (rx + 180, ry + 200, 150, 30),
            "Anim: ON" if self.bg_animation else "Anim: OFF",
            self.fn, toggle=True,
            bg=(45, 120, 60), fg=(255, 255, 255),
            bg_on=(60, 160, 80), fg_on=(255, 255, 255),
        )
        self.btn_bg_anim.active = self.bg_animation

        # --- Save ---
        self.btn_save = Button(
            (rx + self.rect.width // 2 - 60, ry + 255, 120, 30),
            "Save", self.fn,
        )

        # --- Close (overwrite Popup's btn_close) ---
        self.btn_close = Button(
            (rx + self.rect.width - 58, ry + 8, 30, 30), "X", self.fb,
        )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def handle_events(self, ev: pygame.event.Event) -> None:
        """Process events for sliders and buttons."""

        self.slider_ui.handle_event(ev)
        self.slider_music.handle_event(ev)

        if self.btn_mute.handle_event(ev):
            if self.btn_mute.active:
                self.ui_vol, self.music_vol = 0.0, 0.0
            else:
                self.ui_vol = self.slider_ui.value
                self.music_vol = self.slider_music.value
            self.slider_ui.value = self.ui_vol
            self.slider_music.value = self.music_vol

        if self.btn_bg_anim.handle_event(ev):
            self.bg_animation = self.btn_bg_anim.active
            self.btn_bg_anim.label = "Anim: ON" if self.bg_animation else "Anim: OFF"

        if self.btn_save.handle_event(ev):
            self.ui_vol = self.slider_ui.value
            self.music_vol = self.slider_music.value
            save_settings({
                "ui_volume": self.ui_vol,
                "music_volume": self.music_vol,
                "bg_animation": self.bg_animation,
            })
            set_ui_volume(self.ui_vol)
            apply_music_volume(self.music_vol)

        if self.btn_close.handle_event(ev):
            self.visible = False
            if self.on_close:
                self.on_close()

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible:
            return

        super().draw(screen)

        self._title.draw(screen)
        self._ui_label.draw(screen)
        self.slider_ui.draw(screen)
        self._music_label.draw(screen)
        self.slider_music.draw(screen)
        self.btn_mute.draw(screen)
        self.btn_bg_anim.draw(screen)
        self.btn_save.draw(screen)
        self.btn_close.draw(screen)
