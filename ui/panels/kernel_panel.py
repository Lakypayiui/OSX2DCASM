from typing import Optional

import pygame

from core.config import (
    BTN_OFF_BG,
    BTN_OFF_FG,
    BTN_ON_BG,
    BTN_ON_FG,
    P_BORDER,
)
from core.kernel import Kernel


class KernelPanel:
    """Interactive panel used to edit a 3x3 Moore neighborhood kernel."""

    LABELS = [
        "NW", "N", "NE",
        "W", "C", "E",
        "SW", "S", "SE",
    ]

    def __init__(
        self,
        kernel: Kernel,
        x: int,
        y: int,
        cell_size: int = 44,
    ) -> None:
        """Initializes the kernel panel.

        Args:
            kernel: Kernel model displayed by the panel.
            x: X-coordinate of the panel.
            y: Y-coordinate of the panel.
            cell_size: Size in pixels of each kernel cell.
        """

        self.kernel = kernel
        self.active = True

        self.x = x
        self.y = y
        self.cell_size = cell_size

        self.rects = [
            pygame.Rect(
                x + (i % 3) * self.cell_size,
                y + (i // 3) * self.cell_size,
                self.cell_size - 4,
                self.cell_size - 4,
            )
            for i in range(9)
        ]

    def draw(
        self,
        surf: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        """Draws the kernel panel.

        Args:
            surf: Surface where the panel will be rendered.
            font: Base font used to render cell labels.
        """

        big_font = pygame.font.SysFont(
            "monospace",
            font.get_height(),
            bold=True,
        )

        for i, rect in enumerate(self.rects):

            value = self.kernel.bits[i]

            bg = BTN_ON_BG if value else BTN_OFF_BG
            fg = BTN_ON_FG if value else BTN_OFF_FG

            pygame.draw.rect(
                surf,
                bg,
                rect,
                border_radius=6,
            )

            pygame.draw.rect(
                surf,
                P_BORDER,
                rect,
                2,
                border_radius=6,
            )

            label = big_font.render(
                self.LABELS[i],
                True,
                fg,
            )

            surf.blit(
                label,
                (
                    rect.centerx - label.get_width() // 2,
                    rect.centery - label.get_height() // 2,
                ),
            )

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> Optional[int]:
        """Handles a mouse click over the kernel.

        Args:
            pos: Mouse position in screen coordinates.

        Returns:
            The index of the toggled kernel cell, or ``None`` if no cell
            was clicked.
        """

        if not self.active:
            return None

        for i, rect in enumerate(self.rects):

            if rect.collidepoint(pos):
                self.kernel.toggle(i)
                return i

        return None

    @property
    def total_w(self) -> int:
        """Returns the total width of the panel in pixels."""

        return self.cell_size * 3

    @property
    def total_h(self) -> int:
        """Returns the total height of the panel in pixels."""

        return self.cell_size * 3