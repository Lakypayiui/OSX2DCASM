"""Evolution controls sub-panel — Start/Stop, Step, Pause, Save, Load, 3D View."""

from __future__ import annotations

from typing import Callable

import pygame

from core import config
from widgets.button import Button


class EvolutionControls:
    """Controls for running and managing the evolutionary simulation.

    Exposes buttons as instance attributes so that the parent
    :class:`SimulationPanel` can copy references for backward
    compatibility with external callers (e.g. ``simulationscene.py``).

    Attributes:
        y_evolution_hdr: Y-position of the "Evolution" section header.
        btn_evolution: Start/Stop toggle button.
        btn_step: Single-step button.
        btn_pause: Pause/Resume toggle button.
        btn_save: Save-state button.
        btn_load: Load-state button.
        btn_view_3d: Open 3D view button.
    """

    def __init__(
        self,
        create_button: Callable[..., Button],
        buttons_list: list[Button],
        width: int
    ) -> None:
        """Initializes evolution controls.

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

        self.y_evolution_hdr: int = 0

        self.btn_evolution: Button | None = None
        self.btn_step: Button | None = None
        self.btn_pause: Button | None = None
        self.btn_save: Button | None = None
        self.btn_load: Button | None = None
        self.btn_view_3d: Button | None = None

    def _create_evolution_section(self, y: int) -> int:
        """Builds the evolution control buttons at the given y offset.

        Args:
            y: Starting vertical position (pixels from top of panel).

        Returns:
            The next available y position after the section.
        """
        self.y_evolution_hdr = y

        y += 25

        self.btn_evolution = self._create_button(
            "Start", 0, y, toggle=True, bg=(45, 120, 60)
        )
        self._buttons_list.append(self.btn_evolution)

        self.btn_step = self._create_button("Step", 1, y)
        self._buttons_list.append(self.btn_step)

        y += self._button_h() + self._button_gap()

        self.btn_pause = self._create_button("Pause", 0, y, toggle=True)
        self._buttons_list.append(self.btn_pause)

        self.btn_view_3d = self._create_button("3D View", 1, y)
        self._buttons_list.append(self.btn_view_3d)

        y += self._button_h() + self._button_gap()

        self.btn_save = self._create_button("Save", 0, y)
        self._buttons_list.append(self.btn_save)

        self.btn_load = self._create_button("Load", 1, y)
        self._buttons_list.append(self.btn_load)

        y += 40

        return y

    def draw(
        self,
        surface: pygame.Surface,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        """Draws the evolution section onto *surface*.

        Args:
            surface: Target surface to render onto (the panel surface).
            fonts: Mapping of font names (``"bold"``, ``"medium"``, …)
                to :class:`pygame.font.Font` instances.
        """
        # --- Section header ---
        config.draw_text(
            surface,
            fonts["bold"],
            "Evolution",
            (config.PAD, self.y_evolution_hdr),
            config.P_FG,
        )

        pygame.draw.line(
            surface,
            config.P_BORDER,
            (config.PAD, self.y_evolution_hdr + 16),
            (self.width - config.PAD, self.y_evolution_hdr + 16),
        )

        # --- Buttons ---
        assert self.btn_evolution is not None
        assert self.btn_step is not None
        assert self.btn_pause is not None
        assert self.btn_save is not None
        assert self.btn_load is not None
        assert self.btn_view_3d is not None

        self.btn_evolution.draw(surface, fonts["medium"])
        self.btn_step.draw(surface, fonts["medium"])
        self.btn_pause.draw(surface, fonts["medium"])
        self.btn_save.draw(surface, fonts["medium"])
        self.btn_view_3d.draw(surface, fonts["medium"])
        self.btn_load.draw(surface, fonts["medium"])

    # ------------------------------------------------------------------
    # Internal helpers that delegate sizing to the button factory so
    # layout arithmetic stays consistent with the parent panel.
    # ------------------------------------------------------------------

    def _button_h(self) -> int:
        """Button height used for y-advance calculations."""
        return 22

    def _button_gap(self) -> int:
        """Vertical gap between button rows."""
        return 4
