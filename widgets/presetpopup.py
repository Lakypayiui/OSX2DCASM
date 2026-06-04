import json
import numpy as np
import pygame
import config

from widgets.popup import Popup
from widgets.button import Button

PRESET_PATH = "presets/rules.json"

class PresetPopup(Popup):

    def __init__(self, rect):

        super().__init__(rect, "Rule presets")

        self.presets = []

        self.buttons = []

        self.selected_preset = None

        self.scroll = 0

        self.max_scroll = 0

        self.delete_buttons = []

        self.load_presets()

    def load_presets(self):

        try:

            with open(PRESET_PATH, "r", encoding="utf-8") as f:
                self.presets = json.load(f)

        except Exception:
            self.presets = []

        self.buttons.clear()
        self.delete_buttons.clear()

        visible_height = self.rect.height - 80

        self.max_scroll = max(
            0,
            len(self.presets) * 36 - visible_height
        )
            
        for preset in self.presets:

            load_btn = Button(
                (0, 0, 0, 0),
                preset["name"]
            )

            delete_btn = Button(
                (0, 0, 0, 0),
               "X"
            )

            self.buttons.append((load_btn, preset))
            self.delete_buttons.append((delete_btn, preset))

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

        for i, (btn, preset) in enumerate(self.buttons):

            if btn.handle_event(ev):

                self.selected_preset = preset

                self.close()

                return preset

        for btn, preset in self.delete_buttons:

            if btn.handle_event(ev):

                self.delete_preset(preset)

                return None
            
        if ev.type == pygame.MOUSEWHEEL:

            self.scroll -= ev.y * 30

            self.scroll = max(
                0,
                min(self.scroll, self.max_scroll)
            )

        return None
    
    def delete_preset(self, preset):

        self.presets = [
            p
            for p in self.presets
            if p["name"] != preset["name"]
        ]

        with open(PRESET_PATH, "w", encoding="utf-8") as f:
            json.dump(
                self.presets,
                f,
                indent=4
            )

        self.load_presets()

    def draw(self, screen):

        super().draw(screen)

        if not self.visible:
            return
        
        clip_rect = pygame.Rect(
            self.rect.x + 10,
            self.rect.y + 50,
            self.rect.width - 20,
            self.rect.height - 70
        )

        old_clip = screen.get_clip()

        screen.set_clip(clip_rect)


        list_top = self.rect.y + 60

        for i, ((btn, preset), (del_btn, _)) in enumerate(zip(self.buttons, self.delete_buttons)):

            y = list_top + i * 36 - self.scroll

            if y < list_top - 40:
                continue

            if y > self.rect.bottom:
                continue

            btn.rect = pygame.Rect(
                self.rect.x + 20,
                y,
                self.rect.width - 90,
                30
            )

            del_btn.rect = pygame.Rect(
                self.rect.right - 60,
                y,
                40,
                30
            )

            btn.draw(screen, self.fn)

            del_btn.draw(screen, self.fn)
    
        screen.set_clip(old_clip)

        if self.max_scroll > 0:

            track = pygame.Rect(
                self.rect.right - 12,
                self.rect.y + 60,
                6,
                self.rect.height - 80
            )

            pygame.draw.rect(
                screen,
                (50, 50, 60),
                track,
                border_radius=3
            )

            thumb_h = max(
                30,
                track.height * track.height //
                (track.height + self.max_scroll)
            )

            thumb_y = track.y + (
                (track.height - thumb_h)
                * self.scroll
                // self.max_scroll
            )

            pygame.draw.rect(
                screen,
                (120, 120, 140),
                (
                    track.x,
                    thumb_y,
                    track.width,
                    thumb_h
                ),
                border_radius=3
            )