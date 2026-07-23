"""Evolution controls sub-panel — Start/Stop, Step, Pause, Save, Load, 3D View."""

from __future__ import annotations

from typing import Callable

import pygame

from core import config
from widgets.accordion import Accordion
from widgets.button import Button
from widgets.label import Label


class EvolutionControls:
    """Controls for running and managing the evolutionary simulation.

    Exposes buttons as instance attributes so that the parent
    :class:`SimulationPanel` can copy references for backward
    compatibility with external callers (e.g. ``simulationscene.py``).

    Attributes:
        y_evolution_hdr: Y-position of the "Evolution" section header.
        _height: Total height of this sub-panel.
        btn_evolution: Start/Stop toggle button.
        btn_step: Single-step button.
        btn_pause: Pause/Resume toggle button.
        btn_save: Save-state button.
        btn_load: Load-state button.
        btn_view_3d: Open 3D view button.
    """

    _BUTTON_H = 22
    _BUTTON_GAP = 4

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
        self.y_evolution_hdr: int = 0

        self.btn_evolution: Button | None = None
        self.btn_step: Button | None = None
        self.btn_pause: Button | None = None
        self.btn_save: Button | None = None
        self.btn_load: Button | None = None
        self.btn_view_3d: Button | None = None
        self._header_label: Label | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_evolution_section(self, y: int) -> int:
        """Build widgets at *y* and return the next free y."""
        return self.update_layout(y, True)

    def update_layout(self, y: int, create: bool = False) -> int:
        """Reposition all widgets starting at *y*, recalculate height and return the next free y.

        Args:
            y: Top-edge y-coordinate for the section header.
        """
        start_y = y
        self.y_evolution_hdr = y

        self.evolution_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Evolution",
            font=self.fonts["bold"],
            widgets=[],
            expanded=False if create else self.evolution_accordion.expanded,
        )

        y += 50

        self.btn_evolution = self._create_button("Start", 0, y, toggle=True, bg=(45, 120, 60))
        self._buttons_list.append(self.btn_evolution)
        self.evolution_accordion.add_widget(self.btn_evolution)

        self.btn_step = self._create_button("Step", 1, y)
        self._buttons_list.append(self.btn_step)
        self.evolution_accordion.add_widget(self.btn_step)
        y += self._BUTTON_H + self._BUTTON_GAP

        self.btn_pause = self._create_button("Pause", 0, y, toggle=True)
        self._buttons_list.append(self.btn_pause)
        self.evolution_accordion.add_widget(self.btn_pause)

        self.btn_view_3d = self._create_button("3D View", 1, y)
        self._buttons_list.append(self.btn_view_3d)
        self.evolution_accordion.add_widget(self.btn_view_3d)
        y += self._BUTTON_H + self._BUTTON_GAP

        self.btn_save = self._create_button("Save", 0, y)
        self._buttons_list.append(self.btn_save)
        self.evolution_accordion.add_widget(self.btn_save)

        self.btn_load = self._create_button("Load", 1, y)
        self._buttons_list.append(self.btn_load)
        self.evolution_accordion.add_widget(self.btn_load)

        self._height = self._calc_height()

        return start_y + self._height

    def _calc_height(self) -> int:
        """Return the total pixel height of this sub-panel."""
        return 25 + self.evolution_accordion.rect.height

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the evolution section onto *surface*."""

        self.evolution_accordion.draw(surface)
