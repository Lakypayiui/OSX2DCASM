import pygame
from typing import Optional

from core.config import *


class Slider:
    """A draggable horizontal slider widget for selecting numerical values."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        vmin: float = 0.0,
        vmax: float = 1.0,
        value: float = 0.5,
    ) -> None:
        """Initializes the slider.

        Args:
            rect: Position and size as (x, y, width, height).
            vmin: Minimum value of the slider range.
            vmax: Maximum value of the slider range.
            value: Initial value of the slider.
        """
        self.rect: pygame.Rect  = pygame.Rect(rect)
        self.vmin: float  = vmin
        self.vmax: float = vmax
        self.value: float = value
        self._drag: bool = False

    @property
    def norm(self) -> float:
        """Returns the normalized slider value in the range [0.0, 1.0]."""
        return (self.value - self.vmin) / max(self.vmax - self.vmin, 1e-9)

    def handle_event(self, ev: pygame.event.Event) -> None:
        """Processes a pygame event for the slider.

        Args:
            ev: Pygame event to process.
        """
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self._drag = True; self._set(ev.pos[0])
        if ev.type == pygame.MOUSEBUTTONUP   and ev.button == 1:
            self._drag = False
        if ev.type == pygame.MOUSEMOTION and self._drag:
            self._set(ev.pos[0])

    def _set(self, mx: int) -> None:
        """Updates the slider value based on a mouse x-coordinate.

        Args:
            mx: Mouse x-coordinate.
        """
        t: float = (mx - self.rect.x) / max(self.rect.width, 1)
        self.value = self.vmin + max(0.0, min(1.0, t)) * (self.vmax - self.vmin)

    def draw(
        self,
        surf: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        """Draws the slider onto a surface.

        Args:
            surf: Target surface to draw on.
            font: Font used to render the value label.
        """
        pygame.draw.rect(surf, (45, 45, 52), self.rect, border_radius=4)
        fw: int = int(self.norm * self.rect.width)
        if fw > 0:
            pygame.draw.rect(surf, P_ACCENT,
                             (self.rect.x, self.rect.y, fw, self.rect.height),
                             border_radius=4)
        tx: int = self.rect.x + fw
        pygame.draw.circle(surf, (215, 215, 215), (tx, self.rect.centery), 7)
        pygame.draw.circle(surf, P_BORDER,         (tx, self.rect.centery), 7, 1)
        t: pygame.Surface = font.render(f"{self.value:.2f}", True, P_LABEL)
        surf.blit(t, (self.rect.right + 6,
                      self.rect.centery - t.get_height() // 2))
