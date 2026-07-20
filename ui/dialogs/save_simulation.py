import os
from datetime import datetime
from typing import Optional

import numpy as np
import pygame

from core.life2dm import Life2DM
from widgets.popup import Popup
from widgets.button import Button
from widgets.inputbox import InputBox


SAVE_DIR = "saves"

class SaveSimulationPopup(Popup):
    """Popup dialog for saving the current simulation state to a file."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        life: Life2DM,
    ) -> None:
        """Initializes the save simulation popup.

        Args:
            rect: Position and size as (x, y, width, height).
            life: Cellular automaton instance to save state from.
        """

        super().__init__(rect, "Save simulation")

        self.life: Life2DM = life

        self.input_name: InputBox = InputBox(
            (
                self.rect.x + 20,
                self.rect.y + 70,
                self.rect.width - 40,
                32
            )
        )

        self.btn_save: Button = Button(
            (
                self.rect.x + self.rect.width//2 - 60,
                self.rect.bottom - 60,
                120,
                32
            ),
            "Save"
        )

        self.result: Optional[str] = None

        self.state: np.ndarray
        self.rule: np.ndarray
        self.gen: int

    def open(self) -> None:
        """Opens the popup and captures the current automaton state."""

        self.state = self.life.state

        self.rule = np.asarray(
            self.life.rule,
            dtype=np.uint8
        )

        self.gen = self.life.gen

        self.input_name.text = ""

        self.visible = True

    def save_simulation(self, overwrite: bool = False) -> str:
        """Saves the simulation state to a file.

        Args:
            overwrite: If True, overwrite an existing file with the same name.

        Returns:
            ``"empty"`` if no name was entered, ``"exists"`` if the file already
            exists and ``overwrite`` is False, ``"saved"`` on success.
        """

        filename: str = self.input_name.text.strip()

        if not filename :
            return "empty"

        os.makedirs(
            SAVE_DIR,
            exist_ok=True
        )

        path: str = os.path.join(
            SAVE_DIR,
            f"{filename}.txt"
        )

        if os.path.exists(path) and not overwrite:
            return "exists"

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                f"GENERATION:{self.gen}\n\n"
            )

            f.write("RULE:\n")

            f.write(
                "".join(
                    str(int(v))
                    for v in self.rule
                )
            )

            f.write("\n\nSTATE:\n")

            for row in self.state:

                f.write(
                    "".join(
                        str(int(v))
                        for v in row
                    )
                )

                f.write("\n")

        self.result = path

        self.close()

        return "saved"

    def handle_event(self, ev: pygame.event.Event) -> Optional[str]:
        """Processes a pygame event for the save simulation popup.

        Args:
            ev: Pygame event to process.

        Returns:
            The result of ``save_simulation`` if triggered, or the parent result.
        """

        if not self.visible:
            return None

        self.input_name.handle_event(ev)

        if self.btn_save.handle_event(ev):
            return self.save_simulation()

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_RETURN:
                return self.save_simulation()

        return super().handle_event(ev)
    
    def draw(self, screen: pygame.Surface) -> None:
        """Draws the save simulation popup onto the screen.

        Args:
            screen: Pygame display surface.
        """

        super().draw(screen)

        if not self.visible:
            return

        txt: pygame.Surface = self.fn.render(
            "Save name:",
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

        info: pygame.Surface = self.fn.render(
            f"Generation: {self.gen}",
            True,
            self.title_color
        )

        screen.blit(
            info,
            (
                self.rect.x + 20,
                self.rect.y + 130
            )
        )

        size: pygame.Surface = self.fn.render(
            f"Grid: {self.state.shape[1]}x{self.state.shape[0]}",
            True,
            self.title_color
        )

        screen.blit(
            size,
            (
                self.rect.x + 20,
                self.rect.y + 155
            )
        )

        self.btn_save.draw(
            screen,
            self.fn
        )
