import pygame
from typing import Optional

from widgets.base_widget import BaseWidget


class InputBox(BaseWidget):
    """A single-line text input widget for keyboard entry."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        font: pygame.font.Font,
        text: str = "",
        numeric_only: bool = False,
    ) -> None:
        """Initializes the input box.

        Args:
            rect: Position and size as (x, y, width, height).
            font: Font used to render the text.
            text: Initial text content.
            numeric_only: If True, only digits are accepted.
        """
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.font: pygame.font.Font = font
        self.text: str = text
        self.active: bool = False
        self.numeric_only: bool = numeric_only

        self.bg: tuple[int, int, int] = (28, 28, 36)
        self.border: tuple[int, int, int] = (70, 70, 90)
        self.border_active: tuple[int, int, int] = (120, 180, 255)
        self.fg: tuple[int, int, int] = (230, 230, 240)

    def handle_event(self, ev: pygame.event.Event) -> None:
        """Processes a pygame event for the input box.

        Args:
            ev: Pygame event to process.
        """
        if not self.enabled:
            return

        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(ev.pos)

        if ev.type == pygame.KEYDOWN and self.active:

            if ev.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            elif ev.key == pygame.K_RETURN:
                pass

            else:
                if self.numeric_only:
                    if ev.unicode.isdigit():
                        self.text += ev.unicode
                else:
                    if ev.unicode.isprintable():
                        self.text += ev.unicode

    def draw(self, surf: pygame.Surface) -> None:
        """Draws the input box onto a surface.

        Args:
            surf: Target surface to draw on.
        """
        pygame.draw.rect(surf, self.bg, self.rect, border_radius=6)

        border_color: tuple[int, int, int] = self.border_active if self.active else self.border
        pygame.draw.rect(
            surf,
            border_color,
            self.rect,
            width=2,
            border_radius=6
        )

        txt: pygame.Surface = self.font.render(self.text, True, self.fg)
        surf.blit(
            txt,
            (
                self.rect.x + 10,
                self.rect.y + (self.rect.height - txt.get_height()) // 2
            )
        )

    def value(self, default: int = 128) -> int:
        """Returns the current text as an integer.

        Args:
            default: Value returned if the text cannot be parsed.

        Returns:
            The integer value of the text, clamped to a minimum of 1.
        """
        try:
            return max(1, int(self.text))
        except:
            return default
