"""Color / theme controls sub-panel — background, grid, cell color selectors."""

from __future__ import annotations

import pygame

from core import config
from widgets.accordion import Accordion
from widgets.label import Label
from widgets.rgbselector import RGBSelector


class ColorControls:
    """RGB color selectors for background, grid, and cell colours.

    Attributes:
        y_theme_lbl: Y-position of the theme colour labels.
        _height: Total height of this sub-panel.
        bg_color_selectors: List of :class:`RGBSelector` widgets.
    """

    _THEME_KEYS = ["bg", "grid", "cell"]
    _THEME_LABELS = ["Background", "Grid", "Cell"]

    def __init__(
        self,
        theme: dict[str, tuple[int, int, int]],
        width: int,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        self._theme = theme
        self.width = width
        self.fonts = fonts

        self._height: int = 0
        self.y_theme_lbl: int = 0
        self.bg_color_selectors: list[RGBSelector] = []
        self._labels: list[Label] = []
        self.color_accordion: Accordion | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_theme_section(self, y: int) -> int:
        """Build widgets at *y* and return the next free y."""
        return self.update_layout(y, True)
        

    def update_layout(self, y: int, create: bool = False) -> int:
        """Reposition all widgets starting at *y*, recalculate height and return the next free y."""
        self.y_theme_lbl = y

        self.bg_color_selectors.clear()
        self._labels.clear()

        csw = (self.width - config.PAD * 4) // len(self._THEME_KEYS) - 2

        for idx, key in enumerate(self._THEME_KEYS):
            bx = config.PAD * 2 + idx * (csw + 2)
            self.bg_color_selectors.append(
                RGBSelector((bx, y + 70, csw, 80), font=self.fonts["medium"], initial=self._theme[key])
            )
            self._labels.append(
                Label((bx, y + 50), self._THEME_LABELS[idx], self.fonts["bold"], config.P_LABEL)
            )

        self.color_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Theme",
            font=self.fonts["bold"],
            widgets=self._labels + self.bg_color_selectors,
            expanded=False if create else self.color_accordion.expanded,
        )

        self._height = self._calc_height()
        return self.y_theme_lbl + self._height

    def _calc_height(self) -> int:
        """Return the total pixel height of this sub-panel."""
        return 25 + self.color_accordion.rect.height

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the theme colour-selector section onto *surface*."""
        if self.color_accordion is not None:
            self.color_accordion.draw(surface)
