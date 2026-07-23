import pygame
from typing import Optional

from core import config
from widgets.button import Button


class Popup:
    """Base class for popup dialog windows with an overlay and close button."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        title: str = "Popup",
    ) -> None:
        """Initializes the popup.

        Args:
            rect: Position and size as (x, y, width, height).
            title: Title text displayed at the top of the popup.
        """

        self.rect: pygame.Rect = pygame.Rect(rect)

        self.title: str = title

        self.visible: bool = False

        self.bg: tuple[int, int, int] = (28, 28, 34)

        self.border: tuple[int, int, int] = config.P_BORDER

        self.title_color: tuple[int, int, int] = config.P_FG

        self.overlay: tuple[int, int, int, int] = (0, 0, 0, 180)

        self.fn: pygame.font.Font = pygame.font.SysFont("monospace", 14)
        self.fb: pygame.font.Font = pygame.font.SysFont("monospace", 18, bold=True)

        self.btn_close: Button = Button(
            (
                self.rect.right - 38,
                self.rect.y + 8,
                30,
                30
            ),
            "X",
            self.fb,
        )

    def open(self) -> None:
        """Opens (shows) the popup."""

        self.visible = True

    def close(self) -> None:
        """Closes (hides) the popup."""

        self.visible = False

    def handle_event(self, ev: pygame.event.Event) -> Optional[str]:
        """Processes a pygame event for the popup.

        Args:
            ev: Pygame event to process.

        Returns:
            ``"closed"`` if the close button was pressed, ``None`` otherwise.
        """

        if not self.visible:
            return None

        if self.btn_close.handle_event(ev):
            self.close()
            return "closed"

        return None

    def draw(self, screen: pygame.Surface) -> None:
        """Draws the popup onto the screen.

        Args:
            screen: Pygame display surface.
        """

        if not self.visible:
            return

        overlay: pygame.Surface = pygame.Surface(
            screen.get_size(),
            pygame.SRCALPHA
        )

        overlay.fill(self.overlay)

        screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            screen,
            self.bg,
            self.rect,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            self.border,
            self.rect,
            2,
            border_radius=8
        )

        title: pygame.Surface = self.fb.render(
            self.title,
            True,
            self.title_color
        )

        screen.blit(
            title,
            (
                self.rect.x + 16,
                self.rect.y + 12
            )
        )

        self.btn_close.draw(screen)
