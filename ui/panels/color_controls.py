"""Color / theme controls sub-panel — background, grid, cell color selectors."""

from __future__ import annotations

import pygame

from core import config
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

    def __init__(self, theme: dict[str, tuple[int, int, int]]) -> None:
        """Initializes colour controls.

        Args:
            theme: Mapping of theme element names to their default RGB
                values (e.g. ``{"bg": (0,0,0), "grid": ..., "cell": ...}``).
        """
        self._theme = theme

        self.y_theme_lbl: int = 0
        self.bg_color_selectors: list[RGBSelector] = []

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

        # Compute column width so selectors span the panel width.
        csw = (config.PANEL_W - config.PAD) // len(self._THEME_KEYS) - 2

        for idx, key in enumerate(self._THEME_KEYS):
            bx = config.PAD + idx * (csw + 2)
            initial = self._theme[key]
            self.bg_color_selectors.append(
                RGBSelector((bx, y, csw, 80), initial=initial)
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
        csw = (config.PANEL_W - config.PAD) // len(self._THEME_KEYS)

        for idx, label in enumerate(self._THEME_LABELS):
            config.draw_text(
                surface,
                fonts["medium"],
                label,
                (
                    config.PAD + idx * ((config.PANEL_W - config.PAD) // 3),
                    self.y_theme_lbl,
                ),
                config.P_LABEL,
            )

        for selector in self.bg_color_selectors:
            selector.draw(surface, fonts["small"])
