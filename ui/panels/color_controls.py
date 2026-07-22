"""Color / theme controls sub-panel — background, grid, cell color selectors."""

from __future__ import annotations

import pygame

from core import config
from widgets.accordion import Accordion
from widgets.label import Label
from widgets.rgbselector import RGBSelector


class ColorControls:
    """RGB color selectors for background, grid, and cell colours.

    Exposes the ``bg_color_selectors`` list and ``y_theme_lbl`` so the
    parent :class:`SimulationPanel` can copy references for backward
    compatibility.

    Attributes:
        y_theme_lbl: Y-position of the theme colour labels.
        bg_color_selectors: List of :class:`RGBSelector` widgets, one per
            theme element (Background, Grid, Cell).
    """

    # Theme keys for lookup; display labels used in draw().
    _THEME_KEYS = ["bg", "grid", "cell"]
    _THEME_LABELS = ["Background", "Grid", "Cell"]

    def __init__(self, theme: dict[str, tuple[int, int, int]], width: int) -> None:
        """Initializes colour controls.

        Args:
            theme: Mapping of theme element names to their default RGB
                values (e.g. ``{"bg": (0,0,0), "grid": ..., "cell": ...}``).
            width: width of the panel.
        """
        self._theme = theme
        self.width = width

        self.y_theme_lbl: int = 0
        self.bg_color_selectors: list[RGBSelector] = []
        self._labels: list[Label] = []

    def _create_theme_section(self, y: int) -> int:
        """Builds the colour-selector widgets at the given y offset.

        Args:
            y: Starting vertical position (pixels from top of panel).

        Returns:
            The next available y position after the section.
        """
        self.y_theme_lbl = y

        y += 13

        self.bg_color_selectors = []
        self._labels.clear()

        # Compute column width so selectors span the panel width.
        csw = (self.width - config.PAD) // len(self._THEME_KEYS) - 2

        for idx, key in enumerate(self._THEME_KEYS):
            bx = config.PAD + idx * (csw + 2)
            initial = self._theme[key]
            self.bg_color_selectors.append(
                RGBSelector((bx, y + 50, csw, 80), initial=initial)
            )
            self._labels.append(
                Label(
                    (config.PAD + idx * ((self.width - config.PAD) // 3), y),
                    self._THEME_LABELS[idx],
                    config.P_LABEL,
                )
            )

        self.color_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Color",
            widgets=self.bg_color_selectors,
            expanded=False,
        )

        y += 17 + config.PAD
        return y

    def draw(
        self,
        surface: pygame.Surface,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        """Draws the theme colour-selector section onto *surface*.

        Args:
            surface: Target surface to render onto (the panel surface).
            fonts: Mapping of font names (``"medium"``, ``"small"``) to
                :class:`pygame.font.Font` instances.
        """
        for label in self._labels:
            label.draw(surface, fonts["medium"])

        self.color_accordion.draw(surface, fonts["small"])
