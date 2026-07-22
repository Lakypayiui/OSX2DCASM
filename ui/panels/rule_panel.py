from typing import Optional

import pygame

from core.config import (
    BTN_OFF_BG,
    BTN_OFF_FG,
    BTN_ON_BG,
    BTN_ON_FG,
)
from core.rule_matrix import RuleMatrix


class RulePanel:
    """Interactive panel used to edit a 512-bit rule matrix."""

    ROWS = 16
    COLS = 32

    def __init__(
        self,
        rule_matrix: RuleMatrix,
        x: int,
        y: int,
        width: int
    ) -> None:
        """Initializes the rule matrix panel.

        Args:
            rule_matrix: Rule matrix model displayed by the panel.
            x: X-coordinate of the panel.
            y: Y-coordinate of the panel.
            width: width of the panel.
        """

        self.rule_matrix = rule_matrix

        self.active = True

        self.x = x
        self.y = y

        self.width = width
        self.cell_size = self.width // self.COLS
        self.cell_margin = int(self.cell_size * 0.1)

        self.rects: list[list[pygame.Rect]] = (
            self._build_rects()
        )

    def _build_rects(
        self,
    ) -> list[list[pygame.Rect]]:
        """Creates all rectangles used for hit detection.

        Returns:
            A 16x32 matrix of pygame.Rect objects.
        """

        return [
            [
                pygame.Rect(
                    self.x + col * (
                        self.cell_size +
                        self.cell_margin
                    ),
                    self.y + row * (
                        self.cell_size +
                        self.cell_margin
                    ),
                    self.cell_size,
                    self.cell_size,
                )
                for col in range(self.COLS)
            ]
            for row in range(self.ROWS)
        ]

    @property
    def total_w(self) -> int:
        """Returns the total panel width in pixels."""

        return self.COLS * (
            self.cell_size +
            self.cell_margin
        )

    @property
    def total_h(self) -> int:
        """Returns the total panel height in pixels."""

        return self.ROWS * (
            self.cell_size +
            self.cell_margin
        )

    def handle_click(
        self,
        pos: tuple[int, int],
    ) -> Optional[int]:
        """Handles a mouse click on the rule matrix.

        Args:
            pos: Mouse position in screen coordinates.

        Returns:
            The rule index that was toggled, or None if
            no cell was clicked.
        """

        if not self.active:
            return None

        for row in range(self.ROWS):
            for col in range(self.COLS):

                if self.rects[row][col].collidepoint(pos):

                    self.rule_matrix.toggle(
                        row,
                        col,
                    )

                    return row * self.COLS + col

        return None

    def draw(
        self,
        surf: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        """Draws the rule matrix panel.

        Args:
            surf: Surface where the matrix will be rendered.
            font: Font used to render cell values.
        """

        for row in range(self.ROWS):
            for col in range(self.COLS):

                value = self.rule_matrix.data[row][col]

                bg_color = (
                    BTN_ON_BG
                    if value
                    else BTN_OFF_BG
                )

                fg_color = (
                    BTN_ON_FG
                    if value
                    else BTN_OFF_FG
                )

                rect = self.rects[row][col]

                pygame.draw.rect(
                    surf,
                    bg_color,
                    rect,
                    border_radius=1,
                )

                text = font.render(
                    str(value),
                    True,
                    fg_color,
                )

                surf.blit(
                    text,
                    (
                        rect.centerx
                        - text.get_width() // 2,
                        rect.centery
                        - text.get_height() // 2,
                    ),
                )