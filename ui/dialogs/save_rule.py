import json
import numpy as np
import pygame
from typing import Optional

from widgets.popup import Popup
from widgets.button import Button
from widgets.inputbox import InputBox

PRESET_PATH = "presets/rules.json"


class SaveRulePopup(Popup):
    """Popup dialog for saving a rule as a named preset."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        rule: np.ndarray,
    ) -> None:
        """Initializes the save rule popup.

        Args:
            rect: Position and size as (x, y, width, height).
            rule: The 512-element rule array to save.
        """

        super().__init__(rect, "Save rule")

        self.rule: np.ndarray = np.asarray(rule, dtype=np.uint8)

        self.input_name: InputBox = InputBox(
            (
                self.rect.x + 20,
                self.rect.y + 70,
                self.rect.width - 40,
                32
            ),
            self.fn,
        )

        self.btn_save: Button = Button(
            (
                self.rect.x + 20,
                self.rect.bottom - 60,
                120,
                32
            ),
            "Save",
            self.fn,
        )

        self.result: Optional[str] = None

    def load_data(self) -> list[dict]:
        """Loads the rules preset data from the JSON file.

        Returns:
            List of preset dictionaries, or an empty list on failure.
        """

        try:
            with open(PRESET_PATH, "r", encoding="utf-8") as f:
                return json.load(f)

        except:
            return []
        
    def save_rule(self, overwrite: bool = False) -> str:
        """Saves the rule to the presets file.

        Args:
            overwrite: If True, overwrite an existing preset with the same name.

        Returns:
            ``"empty"`` if no name was entered, ``"exists"`` if the name already
            exists and ``overwrite`` is False, ``"saved"`` on success.
        """

        name: str = self.input_name.text.strip()

        if not name:
            return "empty"

        data: list[dict] = self.load_data()

        existing: Optional[dict] = None

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
    
    def handle_event(self, ev: pygame.event.Event) -> Optional[str]:
        """Processes a pygame event for the save rule popup.

        Args:
            ev: Pygame event to process.

        Returns:
            The result of ``save_rule`` if triggered, or the parent result.
        """

        if not self.visible:
            return None

        self.input_name.handle_event(ev)

        if self.btn_save.handle_event(ev):
            return self.save_rule()

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_RETURN:
                return self.save_rule()

        return super().handle_event(ev)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draws the save rule popup onto the screen.

        Args:
            screen: Pygame display surface.
        """

        super().draw(screen)

        if not self.visible:
            return

        txt: pygame.Surface = self.fn.render(
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

        self.input_name.draw(screen)

        cell_size: int = 12

        start_x: int = self.rect.x + 20
        start_y: int = self.rect.y + 120

        for row in range(16):

            for col in range(32):

                idx: int = row * 32 + col

                value: int = int(self.rule[idx])

                color: tuple[int, int, int] = (
                    (220, 220, 220)
                    if value
                    else
                    (40, 40, 50)
                )

                r: pygame.Rect = pygame.Rect(
                    start_x + col * cell_size,
                    start_y + row * cell_size,
                    cell_size - 1,
                    cell_size - 1
                )

                pygame.draw.rect(screen, color, r)

        self.btn_save.draw(screen)
