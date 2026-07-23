"""Population controls sub-panel — random config, clear view, density slider."""

from __future__ import annotations

from typing import Callable

import pygame

from core import config
from widgets.accordion import Accordion
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
        _height: Total height of this sub-panel.
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
        width: int,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        self.width = width
        self.fonts = fonts
        self._create_button = create_button
        self._buttons_list = buttons_list

        self._height: int = 0
        self.y_population_hdr: int = 0
        self.y_density_lbl: int = 0

        self.btn_random_config: Button | None = None
        self.btn_clear_view: Button | None = None
        self.slider_density: Slider | None = None
        self._density_label: Label | None = None
        self.population_accordion: Accordion | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_population_section(self, y: int) -> int:
        """Build widgets at *y* and return the next free y."""
        return self.update_layout(y, True)

    def update_layout(self, y: int, create: bool = False) -> int:
        """Reposition all widgets starting at *y*, recalculate height and return the next free y."""
        start_y = y

        self.population_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Population",
            font=self.fonts["bold"],
            widgets=[],
            expanded=False if create else self.population_accordion.expanded,
        )
        self.y_population_hdr = y

        y += 50

        self.btn_random_config = self._create_button("Random config", 0, y)
        self._buttons_list.append(self.btn_random_config)
        self.population_accordion.add_widget(self.btn_random_config)

        self.btn_clear_view = self._create_button("Clear view", 1, y)
        self._buttons_list.append(self.btn_clear_view)
        self.population_accordion.add_widget(self.btn_clear_view)
        y += self.BUTTON_HEIGHT + self.BUTTON_GAP + 4

        self.y_density_lbl = y
        self._density_label = Label(
            (config.PAD * 2, self.y_density_lbl), "Density Population",
            self.fonts["small"], config.P_LABEL,
        )
        self.population_accordion.add_widget(self._density_label)

        y += 13

        self.slider_density = Slider(
            (config.PAD * 2, y, self.width - 68, 12),
            self.fonts["small"],
            value=0.5 if create else self.slider_density.value,
        )
        self.population_accordion.add_widget(self.slider_density)

        self._height = self._calc_height()
        return start_y + self._height

    def _calc_height(self) -> int:
        """Return the total pixel height of this sub-panel."""
        return 25 + self.population_accordion.rect.height

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the population section onto *surface*."""
        if self.population_accordion is not None:
            self.population_accordion.draw(surface)
