"""Graph controls sub-panel — population, entropy, and block-entropy graphs."""

from __future__ import annotations

import pygame

from core import config
from core.life2dm import Life2DM
from widgets.accordion import Accordion
from widgets.graph import GraphWidget


class GraphControls:
    """Collapsible graph section with three time-series charts.

    Each graph lives inside its own :class:`Accordion`, and all three
    are grouped under a parent "Graphs" accordion.

    Attributes:
        graph_population: Population time-series widget.
        graph_global_entropy: Global-entropy time-series widget.
        graph_block_entropy: Block-entropy time-series widget.
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

        self.graph_population: GraphWidget | None = None
        self.graph_global_entropy: GraphWidget | None = None
        self.graph_block_entropy: GraphWidget | None = None

        self._graphs_accordion: Accordion | None = None
        self._population_accordion: Accordion | None = None
        self._entropy_accordion: Accordion | None = None
        self._block_accordion: Accordion | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_graph_section(self, y: int) -> int:
        """Build widgets at *y* and return the next free y."""
        return self.update_layout(y, True)

    def update_layout(self, y: int, create: bool = False) -> int:
        """Reposition all graphs starting at *y* and return the next free y."""
        start_y = y
        font = self.fonts["small"]

        # --- Three child accordions, each with one graph ---

        y += 50

        self.graph_population = GraphWidget(
            rect=(config.PAD * 2, y + 50, self.width - config.PAD * 4, 450),
            data_ref=self._life.data_population,
            font=font,
            title="Population",
            ylabel="Alive Cells",
            line_color=(255, 120, 80),
        )

        self._population_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Population",
            font=self.fonts["bold"],
            widgets=[self.graph_population],
            expanded=False if create else self._population_accordion.expanded,
        )

        y += self._population_accordion.rect.height + 20

        self.graph_global_entropy = GraphWidget(
            rect=(config.PAD * 2, y + 50, self.width - config.PAD * 4, 450),
            data_ref=self._life.data_global_entropy,
            font=font,
            title="Global Entropy",
            ylabel="H Entropy (bits)",
            line_color=(100, 180, 255),
        )

        self._entropy_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Global Entropy",
            font=self.fonts["bold"],
            widgets=[self.graph_global_entropy],
            expanded=False if create else self._entropy_accordion.expanded,
        )

        y += self._entropy_accordion.rect.height + 20

        self.graph_block_entropy = GraphWidget(
            rect=(config.PAD * 2, y + 50, self.width - config.PAD * 4, 450),
            data_ref=self._life.data_block_entropy,
            font=font,
            title="Block Entropy",
            ylabel="H Entropy (bits by block)",
            line_color=(180, 255, 100),
        )
        self._block_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Block Entropy",
            font=self.fonts["bold"],
            widgets=[self.graph_block_entropy],
            expanded=False if create else self._block_accordion.expanded,
        )

        y += self._block_accordion.rect.height + 20

        # --- Parent accordion wrapping all three ---
        self._graphs_accordion = Accordion(
            rect=pygame.Rect(config.PAD, start_y, self.width - config.PAD * 2, 40),
            label="Graphs",
            font=self.fonts["bold"],
            widgets=[
                self._population_accordion,
                self._entropy_accordion,
                self._block_accordion,
            ],
            expanded=False if create else self._graphs_accordion.expanded,
        )

        self._height = self._calc_height()
        return start_y + self._height

    def _calc_height(self) -> int:
        """Return the total pixel height of this sub-panel."""
        if self._graphs_accordion is None:
            return 25 + config.PAD
        return self._graphs_accordion.rect.height + config.PAD

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the graphs section onto *surface*."""
        if self._graphs_accordion is not None:
            self._graphs_accordion.draw(surface)
