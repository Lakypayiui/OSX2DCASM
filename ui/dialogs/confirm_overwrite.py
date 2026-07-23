import pygame
from typing import Optional

from widgets.popup import Popup
from widgets.button import Button


class ConfirmOverwritePopup(Popup):
    """Popup dialog confirming whether to overwrite an existing file or rule."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        object_type: str,
    ) -> None:
        """Initializes the confirm overwrite popup.

        Args:
            rect: Position and size as (x, y, width, height).
            object_type: Type of object to overwrite (e.g., ``"Rule"`` or ``"File"``).
        """

        super().__init__(rect)

        self.rule_name: str = ""

        self.result: Optional[bool] = None

        self.object_type: str = object_type

        self.file_name: str = ""

        self.btn_overwrite: Button = Button(
            (
                self.rect.x + 20,
                self.rect.bottom - 60,
                140,
                32
            ),
            "Overwrite",
            self.fn,
        )

        self.btn_cancel: Button = Button(
            (
                self.rect.x + 180,
                self.rect.bottom - 60,
                140,
                32
            ),
            "Cancel",
            self.fn,
        )

    def open(self) -> None:
        """Opens the popup and updates the title based on the object type."""

        self.result = None

        self.visible = True

        if self.object_type == "Rule":
            self.title = "Rule already exists"
        else:
            self.title = "Title already exists"

    def handle_event(self, ev: pygame.event.Event) -> Optional[bool]:
        """Processes a pygame event for the confirm overwrite popup.

        Args:
            ev: Pygame event to process.

        Returns:
            ``True`` if overwrite was confirmed, ``False`` if cancelled,
            or ``None`` if the popup is not visible.
        """

        if not self.visible:
            return None

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_ESCAPE:

                self.result = False

                self.close()

                return False

        if self.btn_overwrite.handle_event(ev):

            self.result = True

            self.close()

            return True

        if self.btn_cancel.handle_event(ev):

            self.result = False

            self.close()

            return False

        return super().handle_event(ev)

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the confirm overwrite popup onto the screen.

        Args:
            screen: Pygame display surface.
        """

        super().draw(screen)

        if not self.visible:
            return
        if self.object_type == "Rule":
            text1: pygame.Surface = self.fn.render(
                "A rule with this name already exists.",
                True,
                self.title_color
            )
        else:
            text1 = self.fn.render(
                "A file with this name already exists.",
                True,
                self.title_color
            )
            

        screen.blit(
            text1,
            (
                self.rect.x + 20,
                self.rect.y + 70
            )
        )

        text2: pygame.Surface = self.fn.render(
            f'"{self.rule_name}"',
            True,
            self.title_color
        )

        screen.blit(
            text2,
            (
                self.rect.x + 20,
                self.rect.y + 95
            )
        )

        text3: pygame.Surface = self.fn.render(
            "Do you want to overwrite it?",
            True,
            self.title_color
        )

        screen.blit(
            text3,
            (
                self.rect.x + 20,
                self.rect.y + 125
            )
        )

        self.btn_overwrite.draw(screen)

        self.btn_cancel.draw(screen)
