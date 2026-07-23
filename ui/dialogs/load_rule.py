import json
import numpy as np
import pygame
from core import config
import os
import sys
from typing import Optional

from widgets.popup import Popup
from widgets.button import Button

def resource_path(relative_path: str) -> str:
    """Resolves a resource path for both development and PyInstaller builds.

    Args:
        relative_path: Path relative to the application root.

    Returns:
        Absolute path to the resource.
    """
    try:
        base_path: str = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

PRESET_PATH: str = resource_path("presets/rules.json")

class LoadRulePopup(Popup):
    """Popup dialog for browsing and loading saved rule presets."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
    ) -> None:
        """Initializes the load rule popup.

        Args:
            rect: Position and size as (x, y, width, height).
        """

        super().__init__(rect, "Rule presets")

        self.presets: list[dict] = []

        self.buttons: list[tuple[Button, dict]] = []

        self.selected_preset: Optional[dict] = None

        self.scroll: int = 0

        self.max_scroll: int = 0

        self.delete_buttons: list[tuple[Button, dict]] = []

        self.load_presets()

    def load_presets(self) -> None:
        """Loads rule presets from the JSON file and builds button lists."""

        try:

            with open(PRESET_PATH, "r", encoding="utf-8") as f:
                self.presets = json.load(f)

        except Exception:
            self.presets = []

        self.buttons.clear()
        self.delete_buttons.clear()

        visible_height: int = self.rect.height - 80

        self.max_scroll = max(
            0,
            len(self.presets) * 36 - visible_height
        )
            
        for preset in self.presets:

            load_btn: Button = Button(
                (0, 0, 0, 0),
                preset["name"],
                self.fn,
            )

            delete_btn: Button = Button(
                (0, 0, 0, 0),
               "X",
                self.fn,
            )

            self.buttons.append((load_btn, preset))
            self.delete_buttons.append((delete_btn, preset))

    def load_preset(
        self,
        name: str,
        rule_matrix,
        life,
    ) -> None:
        """Loads a preset rule into the automaton.

        Args:
            name: Name of the preset to load.
            rule_matrix: RuleMatrix instance to update.
            life: Life2DM automaton to update.
        """

        with open(PRESET_PATH, "r", encoding="utf-8") as f:
            data: list[dict] = json.load(f)

        preset: dict = data[name]

        # Restore numpy rule
        life.rule = np.array(
            preset["rule"],
            dtype=np.uint8
        )

        # Rebuild 16x32 matrix
        for idx, value in enumerate(life.rule):

            row: int = idx // 32
            col: int = idx % 32

            rule_matrix.data[row][col] = int(value)

    def handle_event(self, ev: pygame.event.Event) -> Optional[dict]:
        """Processes a pygame event for the load rule popup.

        Args:
            ev: Pygame event to process.

        Returns:
            The selected preset dictionary, or ``None``.
        """

        if not self.visible:
            return None

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

        return super().handle_event(ev)
    
    def delete_preset(self, preset: dict) -> None:
        """Deletes a preset from the JSON file.

        Args:
            preset: The preset dictionary to delete.
        """

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

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the load rule popup onto the screen.

        Args:
            screen: Pygame display surface.
        """

        super().draw(screen)

        if not self.visible:
            return
        
        clip_rect: pygame.Rect = pygame.Rect(
            self.rect.x + 10,
            self.rect.y + 50,
            self.rect.width - 20,
            self.rect.height - 70
        )

        old_clip: pygame.Rect = screen.get_clip()

        screen.set_clip(clip_rect)


        list_top: int = self.rect.y + 60

        for i, ((btn, preset), (del_btn, _)) in enumerate(zip(self.buttons, self.delete_buttons)):

            y: int = list_top + i * 36 - self.scroll

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

            btn.draw(screen)

            del_btn.draw(screen)
    
        screen.set_clip(old_clip)

        if self.max_scroll > 0:

            track: pygame.Rect = pygame.Rect(
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

            thumb_h: int = max(
                30,
                track.height * track.height //
                (track.height + self.max_scroll)
            )

            thumb_y: int = track.y + (
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
