"""Population controls sub-panel — random config, clear view, density slider."""

from __future__ import annotations

from typing import Callable

import pygame

from core import config
from widgets.button import Button
from widgets.label import Label
from widgets.slider import Slider


class PopulationControls:
    """Controls for configuring the cell population.

    Exposes buttons and the density slider as instance attributes so that
    the parent :class:`SimulationPanel` can copy references for backward
    compatibility.

    Attributes:
        y_population_hdr: Y-position of the "Population" section header.
        y_density_lbl: Y-position of the density label.
        btn_random_config: Randomize-config button.
        btn_clear_view: Clear-view button.
        slider_density: Density slider widget.
    """

    BUTTON_WIDTH = 183
    BUTTON_HEIGHT = 22
    BUTTON_GAP = 4

    def __init__(
        self,
        create_button: Callable[..., Button],
        buttons_list: list[Button],
        width: int
    ) -> None:
        """Initializes population controls.

        Args:
            create_button: Factory callable with the same signature as
                :meth:`SimulationPanel._create_button`.
            buttons_list: The panel's global button list that every created
                button is appended to (for hit-testing).
            width: width of the panel.
        """
        self.width = width

        self._create_button = create_button
        self._buttons_list = buttons_list

        self.y_population_hdr: int = 0
        self.y_density_lbl: int = 0

        self.btn_random_config: Button | None = None
        self.btn_clear_view: Button | None = None
        self.slider_density: Slider | None = None

        self._header_label: Label | None = None
        self._density_label: Label | None = None

    def _create_population_section(self, y: int) -> int:
        """Builds population control widgets at the given y offset.

        Args:
            y: Starting vertical position (pixels from top of panel).

        Returns:
            The next available y position after the section.
        """
        self.y_population_hdr = y

        y += 25

        self.btn_random_config = self._create_button("Random config", 0, y)
        self._buttons_list.append(self.btn_random_config)

        self.btn_clear_view = self._create_button("Clear view", 1, y)
        self._buttons_list.append(self.btn_clear_view)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP + 4

        # --- Density slider ---
        self.y_density_lbl = y

        self._header_label = Label(
            (config.PAD, self.y_population_hdr), "Population", config.P_FG
        )
        y += 13

        self._density_label = Label(
            (config.PAD, self.y_density_lbl), "Density Population", config.P_LABEL
        )

        self.slider_density = Slider(
            (config.PAD, y, self.width - 65, 12),
            value=0.5,
        )

        y += 40 + config.PAD

        return y

    def draw(
        self,
        surface: pygame.Surface,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        """Draws the population section onto *surface*.

        Args:
            surface: Target surface to render onto (the panel surface).
            fonts: Mapping of font names (``"bold"``, ``"medium"``,
                ``"small"``) to :class:`pygame.font.Font` instances.
        """
        # --- Section header ---
        assert self._header_label is not None
        self._header_label.draw(surface, fonts["bold"])

        pygame.draw.line(
            surface,
            config.P_BORDER,
            (config.PAD, self.y_population_hdr + 16),
            (self.width - config.PAD, self.y_population_hdr + 16),
        )

        # --- Buttons ---
        assert self.btn_random_config is not None
        assert self.btn_clear_view is not None
        assert self.slider_density is not None

        self.btn_random_config.draw(surface, fonts["medium"])
        self.btn_clear_view.draw(surface, fonts["medium"])

        # --- Density label + slider ---
        assert self._density_label is not None
        self._density_label.draw(surface, fonts["small"])
        self.slider_density.draw(surface, fonts["small"])
