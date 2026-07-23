import pygame
from typing import Optional

from core.config import *

from widgets.base_widget import BaseWidget


class RGBSelector(BaseWidget):
    """A widget with three sliders for selecting an RGB color."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        font: pygame.font.Font,
        initial: tuple[int, int, int] = (128, 128, 128),
    ) -> None:
        """Initializes the RGB selector.

        Args:
            rect: Position and size as (x, y, width, height).
            font: Font used to render labels.
            initial: Initial RGB color tuple.
        """
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.font: pygame.font.Font = font

        # Sub-rects para sliders
        h: int = self.rect.height // 4
        self.r_rect: pygame.Rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, h)
        self.g_rect: pygame.Rect = pygame.Rect(self.rect.x, self.rect.y + h, self.rect.width, h)
        self.b_rect: pygame.Rect = pygame.Rect(self.rect.x, self.rect.y + 2*h, self.rect.width, h)
        self.preview_rect: pygame.Rect = pygame.Rect(self.rect.x, self.rect.y + 3*h, self.rect.width, h)

        self.r: int
        self.g: int
        self.b: int
        self.r, self.g, self.b = initial
        self.dragging: Optional[str] = None  # "r", "g", "b"

    def _get_value_from_pos(self, rect: pygame.Rect, x: int) -> int:
        """Converts a mouse x-coordinate to a color channel value.

        Args:
            rect: Rectangle of the slider.
            x: Mouse x-coordinate.

        Returns:
            Integer value in the range [0, 255].
        """
        rel: float = (x - rect.x) / rect.width
        return max(0, min(255, int(rel * 255)))

    def handle_event(self, ev: pygame.event.Event) -> None:
        """Processes a pygame event for the RGB selector.

        Args:
            ev: Pygame event to process.
        """
        if not self.enabled:
            return

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.r_rect.collidepoint(ev.pos):
                self.dragging = "r"
            elif self.g_rect.collidepoint(ev.pos):
                self.dragging = "g"
            elif self.b_rect.collidepoint(ev.pos):
                self.dragging = "b"

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dragging = None

        elif ev.type == pygame.MOUSEMOTION:
            if self.dragging:
                x: int = ev.pos[0]
                if self.dragging == "r":
                    self.r = self._get_value_from_pos(self.r_rect, x)
                elif self.dragging == "g":
                    self.g = self._get_value_from_pos(self.g_rect, x)
                elif self.dragging == "b":
                    self.b = self._get_value_from_pos(self.b_rect, x)

    def get_color(self) -> tuple[int, int, int]:
        """Returns the currently selected RGB color.

        Returns:
            Tuple of (R, G, B) values.
        """
        return (self.r, self.g, self.b)

    def draw_slider(
        self,
        surf: pygame.Surface,
        rect: pygame.Rect,
        value: int,
        color: tuple[int, int, int],
        label: str,
        font: pygame.font.Font,
    ) -> None:
        """Draws a single color channel slider.

        Args:
            surf: Target surface to draw on.
            rect: Rectangle of the slider.
            value: Current value of the channel (0-255).
            color: Display color for the slider bar.
            label: Label text (e.g., "R", "G", "B").
            font: Font used to render the label.
        """
        # Fondo
        pygame.draw.rect(surf, BTN_OFF_BG, rect, border_radius=4)
        pygame.draw.rect(surf, P_BORDER, rect, 1, border_radius=4)

        # Barra de color
        fill_w: int = int((value / 255) * rect.width)
        fill_rect: pygame.Rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surf, color, fill_rect, border_radius=4)

        # Texto
        txt: str = f"{label}: {value}"
        t: pygame.Surface = font.render(txt, True, P_FG)
        surf.blit(t, (rect.x + 6, rect.y + rect.height // 2 - t.get_height() // 2))

    def draw(self, surf: pygame.Surface) -> None:
        """Draws the RGB selector onto a surface.

        Args:
            surf: Target surface to draw on.
        """
        # Sliders
        self.draw_slider(surf, self.r_rect, self.r, (255, 0, 0), "R", self.font)
        self.draw_slider(surf, self.g_rect, self.g, (0, 255, 0), "G", self.font)
        self.draw_slider(surf, self.b_rect, self.b, (0, 0, 255), "B", self.font)

        # Preview color
        color: tuple[int, int, int] = self.get_color()
        pygame.draw.rect(surf, color, self.preview_rect, border_radius=4)
        pygame.draw.rect(surf, P_BORDER, self.preview_rect, 1, border_radius=4)

        # Texto del color
        txt: str = f"RGB{color}"
        t: pygame.Surface = self.font.render(txt, True, P_FG)
        surf.blit(t, (self.preview_rect.centerx - t.get_width() // 2,
                      self.preview_rect.centery - t.get_height() // 2))
