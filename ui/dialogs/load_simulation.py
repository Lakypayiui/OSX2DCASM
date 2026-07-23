import os
from typing import Optional

import numpy as np
import pygame

from widgets.popup import Popup
from widgets.button import Button

SAVE_DIR = "saves"


class LoadSimulationPopup(Popup):
    """Popup dialog for browsing and loading saved simulation files."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
    ) -> None:
        """Initializes the load simulation popup.

        Args:
            rect: Position and size as (x, y, width, height).
        """

        super().__init__(rect, "Load simulation")

        self.simulations: list[str] = []
        self.buttons: list[tuple[Button, str]] = []
        self.delete_buttons: list[tuple[Button, str]] = []

        self.selected: Optional[dict] = None

        self.scroll: int = 0
        self.max_scroll: int = 0

        self.load_simulations()

    def load_simulations(self) -> None:
        """Scans the saves directory and builds the button list."""

        os.makedirs(
            SAVE_DIR,
            exist_ok=True
        )

        self.simulations.clear()
        self.buttons.clear()
        self.delete_buttons.clear()

        files: list[str] = sorted(
            [
                f for f in os.listdir(SAVE_DIR)
                if f.endswith(".txt")
            ]
        )

        for filename in files:

            self.simulations.append(filename)

            self.buttons.append(
                (
                    Button((0, 0, 0, 0), filename[:-4], self.fn),
                    filename
                )
            )

            self.delete_buttons.append(
                (
                    Button((0, 0, 0, 0), "X", self.fn),
                    filename
                )
            )

        visible_height: int = self.rect.height - 80

        self.max_scroll = max(
            0,
            len(self.simulations) * 36 - visible_height
        )

    def read_simulation(self, filename: str) -> dict:
        """Reads a simulation state from a save file.

        Args:
            filename: Name of the save file.

        Returns:
            Dictionary with keys ``"generation"``, ``"rule"``, and ``"state"``.
        """

        path: str = os.path.join(
            SAVE_DIR,
            filename
        )

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            lines: list[str] = [
                line.strip()
                for line in f.readlines()
            ]

        generation: int = 0
        rule: Optional[np.ndarray] = None
        state: list[list[int]] = []

        mode: Optional[str] = None

        for line in lines:

            if not line:
                continue

            if line.startswith("GENERATION:"):

                generation = int(
                    line.split(":")[1]
                )

            elif line == "RULE:":

                mode = "rule"

            elif line == "STATE:":

                mode = "state"

            elif mode == "rule":

                rule = np.array(
                    [int(c) for c in line],
                    dtype=np.uint8
                )

            elif mode == "state":

                state.append(
                    [int(c) for c in line]
                )

        state_arr: np.ndarray = np.array(
            state,
            dtype=np.uint8
        )

        return {
            "generation": generation,
            "rule": rule,
            "state": state_arr
        }

    def delete_simulation(self, filename: str) -> None:
        """Deletes a saved simulation file.

        Args:
            filename: Name of the file to delete.
        """

        path: str = os.path.join(
            SAVE_DIR,
            filename
        )

        if os.path.exists(path):
            os.remove(path)

        self.load_simulations()

    def handle_event(self, ev: pygame.event.Event) -> Optional[dict]:
        """Processes a pygame event for the load simulation popup.

        Args:
            ev: Pygame event to process.

        Returns:
            The loaded simulation data dictionary, or ``None``.
        """

        if not self.visible:
            return None

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_ESCAPE:
                self.close()

        for btn, filename in self.buttons:

            if btn.handle_event(ev):

                self.selected = self.read_simulation(
                    filename
                )

                self.close()

                return self.selected

        for btn, filename in self.delete_buttons:

            if btn.handle_event(ev):

                self.delete_simulation(
                    filename
                )

                return None

        if ev.type == pygame.MOUSEWHEEL:

            self.scroll -= ev.y * 30

            self.scroll = max(
                0,
                min(
                    self.scroll,
                    self.max_scroll
                )
            )

        return super().handle_event(ev)

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the load simulation popup onto the screen.

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

        for i, ((btn, file), (del_btn, _)) in enumerate(
            zip(self.buttons, self.delete_buttons)
        ):

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
