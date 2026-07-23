from typing import Dict, List
import pygame

from core import config
from core.kernel import Kernel
from core.life2dm import Life2DM
from core.rule_matrix import RuleMatrix
from widgets.button import Button
from widgets.graph import GraphWidget
from ui.panels.color_controls import ColorControls
from ui.panels.evolution_controls import EvolutionControls
from ui.panels.info_controls import InfoControls
from ui.panels.population_controls import PopulationControls
from ui.panels.rule_controls import RuleControls


class SimulationPanel:
    """Right-hand control panel for the OSX2DCASM simulator.

    Composes four sub-panels — :class:`RuleControls`,
    :class:`PopulationControls`, :class:`EvolutionControls`, and
    :class:`ColorControls` — alongside inline graph widgets.  All
    button references are copied to ``self`` for backward
    compatibility with ``simulationscene.py``.
    """

    BUTTON_WIDTH = 183
    BUTTON_HEIGHT = 22
    BUTTON_GAP = 4

    def __init__(
        self,
        rule_matrix: RuleMatrix,
        kernel: Kernel,
        life: Life2DM,
        theme: Dict[str, tuple[int, int, int]],
        fonts: Dict[str, pygame.font.Font],
        width: int,
        height: int,
    ) -> None:
        self.rule_matrix = rule_matrix
        self.kernel = kernel
        self.theme = theme
        self.life = life
        self.width = width
        self.height = height

        self.visible = True
        self.font_normal = fonts["normal"]
        self.font_medium = fonts["medium"]
        self.font_bold = fonts["bold"]
        self.font_small = fonts["small"]
        self.fonts = fonts

        self.buttons: list[Button] = []
        self.scroll_y: int = 0
        self.content_height: int = 0
        self.content_surface = None

        self._build_layout()
        self.surface = pygame.Surface((self.width, self.height))

    # ------------------------------------------------------------------
    # Button factory
    # ------------------------------------------------------------------

    def _create_button(
        self, label: str, column: int, y: int, toggle: bool = False,
        bg: tuple = config.BTN_OFF_BG, bg_on: tuple = config.BTN_ON_BG,
    ) -> Button:
        return Button(
            (config.PAD * 2 + column * (self.BUTTON_WIDTH + self.BUTTON_GAP), y,
             self.BUTTON_WIDTH, self.BUTTON_HEIGHT),
            label, self.font_medium, toggle=toggle, bg=bg, bg_on=bg_on,
        )

    # ------------------------------------------------------------------
    # Hide button
    # ------------------------------------------------------------------

    def _create_hide_button(self) -> None:
        self.btn_hide_panel = Button(
            (self.width - config.PAD - 40, config.PAD, 40, 20),
            "<<", self.font_bold, toggle=False,
            bg=config.BTN_OFF_BG, bg_on=config.BTN_ON_BG,
        )

    # ------------------------------------------------------------------
    # Layout orchestration
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self._create_hide_button()

        # --- Rule sub-panel ---
        self.rule_controls = RuleControls(
            self.rule_matrix, self.kernel, self._create_button,
            self.buttons, self.width, self.fonts,
        )
        y = self.rule_controls._create_rule_section(self.btn_hide_panel.rect.height + config.PAD)

        # --- Population sub-panel ---
        self.population_controls = PopulationControls(
            self._create_button, self.buttons, self.width, self.fonts,
        )
        y = self.population_controls._create_population_section(y)

        # --- Evolution sub-panel ---
        self.evolution_controls = EvolutionControls(
            self._create_button, self.buttons, self.width, self.fonts,
        )
        y = self.evolution_controls._create_evolution_section(y)

        # --- Color sub-panel ---
        self.color_controls = ColorControls(self.theme, self.width, self.fonts)
        y = self.color_controls._create_theme_section(y)

        # --- Information sub-panel ---
        self.info_controls = InfoControls(self.life, self.width, self.fonts)
        y = self.info_controls._create_info_section(y)

        # --- Graph widgets ---
        self.graph_population = GraphWidget(
            rect=(config.PAD, y, self.width - config.PAD * 2, 400),
            data_ref=self.life.data_population, font=self.font_small,
            title="Population", ylabel="Alive Cells", line_color=(255, 120, 80),
        )
        y += 420

        self.graph_global_entropy = GraphWidget(
            rect=(config.PAD, y, self.width - config.PAD * 2, 400),
            data_ref=self.life.data_global_entropy, font=self.font_small,
            title="Global Entropy", ylabel="H Entropy (bits)", line_color=(255, 120, 80),
        )

        self.content_height = y + 440
        self.content_surface = pygame.Surface((self.width, self.content_height))
        self.content_surface.fill(config.P_BG)

        self._copy_rule_attrs()
        self._copy_population_attrs()
        self._copy_evolution_attrs()
        self._copy_color_attrs()

    # ------------------------------------------------------------------
    # Attribute forwarding
    # ------------------------------------------------------------------

    def _copy_rule_attrs(self) -> None:
        rc = self.rule_controls
        self.y_rule_hdr = rc.y_rule_hdr
        self.y_rule_density_lbl = rc.y_rule_density_lbl
        self.x_rule_density_lbl = rc.x_rule_density_lbl
        self.x_kernel_info = rc.x_kernel_info
        self.y_kernel_info = rc.y_kernel_info
        self.rule_panel = rc.rule_panel
        self.kernel_panel = rc.kernel_panel
        self.btn_add_kernel = rc.btn_add_kernel
        self.btn_random_rule = rc.btn_random_rule
        self.btn_clear_rule = rc.btn_clear_rule
        self.btn_load_rule = rc.btn_load_rule
        self.btn_save_rule = rc.btn_save_rule
        self.slider_rule_density = rc.slider_rule_density
        self.rule_accordion = rc.rule_accordion

    def _copy_population_attrs(self) -> None:
        pc = self.population_controls
        self.y_population_hdr = pc.y_population_hdr
        self.y_density_lbl = pc.y_density_lbl
        self.btn_random_config = pc.btn_random_config
        self.btn_clear_view = pc.btn_clear_view
        self.slider_density = pc.slider_density
        self.population_accordion = pc.population_accordion

    def _copy_evolution_attrs(self) -> None:
        ec = self.evolution_controls
        self.y_evolution_hdr = ec.y_evolution_hdr
        self.btn_evolution = ec.btn_evolution
        self.btn_step = ec.btn_step
        self.btn_pause = ec.btn_pause
        self.btn_save = ec.btn_save
        self.btn_load = ec.btn_load
        self.btn_view_3d = ec.btn_view_3d
        self.evolution_accordion = ec.evolution_accordion

    def _copy_color_attrs(self) -> None:
        cc = self.color_controls
        self.y_theme_lbl = cc.y_theme_lbl
        self.bg_color_selectors = cc.bg_color_selectors
        self.color_accordion = cc.color_accordion

    # ------------------------------------------------------------------
    # Resize / scroll
    # ------------------------------------------------------------------

    def _on_resize(self, height: int) -> None:
        self.height = height

    def _update_layout(self) -> None:

        y = self.rule_controls.update_layout(self.btn_hide_panel.rect.height + config.PAD)

        # --- Population sub-panel ---
        y = self.population_controls.update_layout(y)

        # --- Evolution sub-panel ---
        y = self.evolution_controls.update_layout(y)

        # --- Color sub-panel ---
        y = self.color_controls.update_layout(y)

        y = self.info_controls.update_layout(y)

        # --- Graph widgets ---
        self.graph_population = GraphWidget(
            rect=(config.PAD, y, self.width - config.PAD * 2, 400),
            data_ref=self.life.data_population, font=self.font_small,
            title="Population", ylabel="Alive Cells", line_color=(255, 120, 80),
        )
        y += 420

        self.graph_global_entropy = GraphWidget(
            rect=(config.PAD, y, self.width - config.PAD * 2, 400),
            data_ref=self.life.data_global_entropy, font=self.font_small,
            title="Global Entropy", ylabel="H Entropy (bits)", line_color=(255, 120, 80),
        )

        self.content_height = y + 440
        self.content_surface = pygame.Surface((self.width, self.content_height))
        self.content_surface.fill(config.P_BG)

        self._copy_rule_attrs()
        self._copy_population_attrs()
        self._copy_evolution_attrs()
        self._copy_color_attrs()

    def _clamp_scroll(self) -> None:
        max_scroll = max(0, self.content_height - self.height)
        self.scroll_y = max(0, min(self.scroll_y, max_scroll))

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        if not self.visible:
            self.btn_hide_panel.draw(screen)
            return

        self.content_surface.fill(config.P_BG)

        self.rule_controls.draw(self.content_surface)
        self.population_controls.draw(self.content_surface)
        self.evolution_controls.draw(self.content_surface)
        self.color_controls.draw(self.content_surface)
        self.info_controls.draw(self.content_surface)

        self.graph_population.draw(self.content_surface)
        self.graph_global_entropy.draw(self.content_surface)

        pygame.draw.rect(
            self.content_surface, config.P_BORDER,
            (0, 0, self.width, self.content_height), 1,
        )
        self.btn_hide_panel.draw(self.content_surface)

        self.surface.fill(config.P_BG)
        visible_rect = pygame.Rect(0, self.scroll_y, self.width, self.height)
        self.surface.blit(self.content_surface, (0, 0), visible_rect)

        pygame.draw.line(
            screen, config.P_BORDER, (self.width, 0), (self.width, self.height), 2,
        )
        screen.blit(self.surface, (0, 0))
