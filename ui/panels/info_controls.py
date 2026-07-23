"""Information sub-panel — displays automaton state: width, height, generation, running."""

from __future__ import annotations

import pygame

from core import config
from core.life2dm import Life2DM
from widgets.label import Label


class InfoControls:
    """Read-only display of the automaton's current state.

    Attributes:
        y_info_hdr: Y-position of the section header.
        _height: Total height of this sub-panel.
    """

    def __init__(
        self,
        life: Life2DM,
        width: int,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        self._life = life
        self.width = width
        self.fonts = fonts

        self._height: int = 0
        self.y_info_hdr: int = 0
        self._header_label: Label | None = None
        self._info_labels: list[Label] = []

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_info_section(self, y: int) -> int:
        """Build widgets at *y* and return the next free y."""
        return self.update_layout(y)

    def update_layout(self, y: int) -> int:
        """Reposition all widgets starting at *y*, recalculate height and return the next free y."""
        self.y_info_hdr = y
        self._header_label = Label(
            (config.PAD, y), "Information", self.fonts["bold"], config.P_FG,
        )
        y += 25

        self._info_labels = [
            Label((config.PAD + 16, y + i * 18), "", self.fonts["normal"], config.P_LABEL)
            for i in range(4)
        ]
        y += 4 * 18 + config.PAD

        self._height = y - self.y_info_hdr
        return self.y_info_hdr + self._height

    def _calc_height(self) -> int:
        return 25 + 4 * 18 + config.PAD

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the information section onto *surface*."""
        assert self._header_label is not None
        self._header_label.draw(surface)

        pygame.draw.line(
            surface, config.P_BORDER,
            (config.PAD, self.y_info_hdr + 16),
            (self.width - config.PAD, self.y_info_hdr + 16),
        )

        values = [
            f"Width: {self._life.width}",
            f"Height: {self._life.height}",
            f"Generation: {self._life.gen}",
            f"Running: {self._life.running}",
        ]
        for label, text in zip(self._info_labels, values):
            label.text = text
            label.draw(surface)
