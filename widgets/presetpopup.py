import json
import numpy as np
import pygame
import config
import os
import sys

from widgets.popup import Popup
from widgets.button import Button

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

PRESET_PATH = resource_path("presets/rules.json")

class PresetPopup(Popup):

    def __init__(self, rect):

        super().__init__(rect, "Rule presets")

        self.presets = []

        self.buttons = []

        self.selected_preset = None

        self.load_presets()

    def load_presets(self):

        try:

            with open(PRESET_PATH, "r", encoding="utf-8") as f:
                self.presets = json.load(f)

        except Exception:
            self.presets = []

        self.buttons.clear()

        y = self.rect.y + 60

        for preset in self.presets:

            btn = Button(
                (
                    self.rect.x + 20,
                    y,
                    self.rect.width - 40,
                    30
                ),
                preset["name"]
            )

            self.buttons.append((btn, preset))

            y += 36

    def load_preset(self, name, matriz_regla, life):

        with open(PRESET_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        preset = data[name]

        # Restaurar regla numpy
        life.rule = np.array(
            preset["rule"],
            dtype=np.uint8
        )

        # Reconstruir matriz 16x32
        for idx, value in enumerate(life.rule):

            row = idx // 32
            col = idx % 32

            matriz_regla.data[row][col] = int(value)

    def handle_event(self, ev):

        if not self.visible:
            return None

        super().handle_event(ev)

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_ESCAPE:
                self.close()

        for btn, preset in self.buttons:

            if btn.handle_event(ev):

                self.selected_preset = preset

                self.close()

                return preset

        return None

    def draw(self, screen):

        super().draw(screen)

        if not self.visible:
            return

        for btn, _ in self.buttons:
            btn.draw(screen, self.fn)