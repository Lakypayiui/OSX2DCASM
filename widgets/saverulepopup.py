import json
import numpy as np
import pygame

from widgets.popup import Popup
from widgets.button import Button
from widgets.inputbox import InputBox

PRESET_PATH = "presets/rules.json"


class SaveRulePopup(Popup):

    def __init__(self, rect, rule):

        super().__init__(rect, "Save rule")

        self.rule = np.asarray(rule, dtype=np.uint8)

        self.input_name = InputBox(
            (
                self.rect.x + 20,
                self.rect.y + 70,
                self.rect.width - 40,
                32
            )
        )

        self.btn_save = Button(
            (
                self.rect.x + 20,
                self.rect.bottom - 60,
                120,
                32
            ),
            "Save"
        )

        self.result = None

    def load_data(self):

        try:
            with open(PRESET_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        except:
            return []
        
    def save_rule(self, overwrite=False):

        name = self.input_name.text.strip()

        if not name:
            return "empty"

        data = self.load_data()

        existing = None

        for item in data:

            if item["name"] == name:
                existing = item
                break

        if existing:

            if not overwrite:
                return "exists"

            existing["rule"] = self.rule.tolist()

        else:

            data.append(
                {
                    "name": name,
                    "rule": self.rule.tolist()
                }
            )

        with open(PRESET_PATH, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=4
            )

        self.result = name

        self.close()

        return "saved"
    
    def handle_event(self, ev):

        if not self.visible:
            return None

        super().handle_event(ev)

        self.input_name.handle_event(ev)

        if self.btn_save.handle_event(ev):
            return self.save_rule()

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_RETURN:
                return self.save_rule()

        return None
    
    def draw(self, screen):

        super().draw(screen)

        if not self.visible:
            return

        txt = self.fn.render(
            "Rule name:",
            True,
            self.title_color
        )

        screen.blit(
            txt,
            (
                self.rect.x + 20,
                self.rect.y + 45
            )
        )

        self.input_name.draw(
            screen,
            self.fn
        )

        cell_size = 12

        start_x = self.rect.x + 20
        start_y = self.rect.y + 120

        for row in range(16):

            for col in range(32):

                idx = row * 32 + col

                value = int(self.rule[idx])

                color = (
                    (220, 220, 220)
                    if value
                    else
                    (40, 40, 50)
                )

                r = pygame.Rect(
                    start_x + col * cell_size,
                    start_y + row * cell_size,
                    cell_size - 1,
                    cell_size - 1
                )

                pygame.draw.rect(screen, color, r)

        self.btn_save.draw(
            screen,
            self.fn
        )