import json
import pygame
import config

from widgets.popup import Popup
from widgets.button import Button

class PresetPopup(Popup):

    def __init__(self, rect):

        super().__init__(rect, "Rule presets")

        self.presets = []

        self.buttons = []

        self.selected_preset = None

        self.load_presets()

    def load_presets(self):

        try:

            with open("presets.json", "r") as f:
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

    def handle_event(self, ev):

        if not self.visible:
            return None

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