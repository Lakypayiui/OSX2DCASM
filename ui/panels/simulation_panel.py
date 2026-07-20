import pygame

from core import config

from core.kernel import Kernel
from core.rule_matrix import RuleMatrix

from widgets.button import Button
from widgets.slider import Slider

from ui.panels import (
    KernelPanel,
    RulePanel,
)
from ui.panels.color_controls import ColorControls
from ui.panels.evolution_controls import EvolutionControls
from ui.panels.population_controls import PopulationControls


class SimulationPanel:
    """Right-hand control panel for the OSX2DCASM simulator.

    Composes three sub-panels — :class:`PopulationControls`,
    :class:`EvolutionControls`, and :class:`ColorControls` — alongside
    the inline rule-matrix / kernel sections.  All button references
    are copied to ``self`` for backward compatibility with
    ``simulationscene.py``.
    """

    BUTTON_WIDTH = 183
    BUTTON_HEIGHT = 22
    BUTTON_GAP = 4

    def __init__(
        self,
        rule_matrix: RuleMatrix,
        kernel: Kernel,
        theme: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        """Initializes the simulation control panel.

        Args:
            rule_matrix: Rule matrix model displayed by the rule panel.
            kernel: Kernel model displayed by the kernel panel.
            theme: Mapping of theme element names to RGB colors.
            fonts: Fonts used to render the panel.
        """
        self.rule_matrix = rule_matrix
        self.kernel = kernel
        self.theme = theme

        self.visible = True

        # Fonts
        self.font_normal = fonts["normal"]
        self.font_medium = fonts["medium"]
        self.font_bold = fonts["bold"]
        self.font_small = fonts["small"]

        self.buttons: list[Button] = []
        self._build_layout()

        self.surface = pygame.Surface((config.PANEL_W, config.WIN_H))

    # ------------------------------------------------------------------
    # Button factory (shared with sub-panels)
    # ------------------------------------------------------------------

    def _create_button(
        self,
        label: str,
        column: int,
        y: int,
        toggle: bool = False,
        bg: tuple = config.BTN_OFF_BG,
        bg_on: tuple = config.BTN_ON_BG,
    ) -> Button:
        """Creates a button positioned by column and y.

        Args:
            label: Button text.
            column: 0-based column index.
            y: Top-edge y-coordinate.
            toggle: Whether the button is a toggle.
            bg: Off-state background colour.
            bg_on: On-state background colour.

        Returns:
            A new :class:`Button` instance.
        """
        return Button(
            (
                config.PAD + column * (self.BUTTON_WIDTH + self.BUTTON_GAP),
                y,
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT,
            ),
            label,
            toggle=toggle,
            bg=bg,
            bg_on=bg_on,
        )

    # ------------------------------------------------------------------
    # Hide button
    # ------------------------------------------------------------------

    def _create_hide_button(self) -> None:
        """Creates the small hide/show toggle in the top-right corner."""
        self.btn_hide_panel = Button(
            (config.PANEL_W - config.PAD - 40, config.PAD, 40, 20),
            "<<",
            toggle=False,
            bg=config.BTN_OFF_BG,
            bg_on=config.BTN_ON_BG,
        )
        self.buttons.append(self.btn_hide_panel)

    # ------------------------------------------------------------------
    # Rule-matrix + kernel section (stays inline)
    # ------------------------------------------------------------------

    def _create_rule_section(self) -> int:
        """Builds the rule-matrix and kernel subsections.

        Returns:
            The next available y position after the section.
        """
        y = config.PAD

        self.y_rule_hdr = y
        y += 28

        matrix_x = config.PAD + 16
        self.rule_panel = RulePanel(self.rule_matrix, matrix_x, y)
        y += self.rule_panel.total_h + config.PAD + 18

        kernel_x = matrix_x
        self.kernel_panel = KernelPanel(self.kernel, kernel_x, y)

        self.x_kernel_info = kernel_x + self.kernel_panel.total_w + 16
        self.y_kernel_info = y

        self.btn_add_kernel = self._create_button("Add kernel", 2, y)
        self.buttons.append(self.btn_add_kernel)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_random_rule = self._create_button("Random rule", 2, y)
        self.buttons.append(self.btn_random_rule)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_clear_rule = self._create_button("Clear rule", 2, y)
        self.buttons.append(self.btn_clear_rule)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP + 4

        # --- Rule density slider ---
        self.y_rule_density_lbl = y
        self.x_rule_density_lbl = config.PAD + 2 * (
            self.BUTTON_WIDTH + self.BUTTON_GAP
        )

        y += 13

        self.slider_rule_density = Slider(
            (
                self.x_rule_density_lbl,
                y,
                int(self.BUTTON_WIDTH * 1.4),
                12,
            ),
            value=0.5,
        )

        y += 24

        self.btn_load_rule = self._create_button("Load Rule", 2, y)
        self.buttons.append(self.btn_load_rule)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_save_rule = self._create_button("Save Rule", 2, y)
        self.buttons.append(self.btn_save_rule)

        y += config.PAD + 40

        self.y_sep2 = y
        y += config.PAD

        return y

    # ------------------------------------------------------------------
    # Layout orchestration
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        """Assembles all sections by delegating to sub-panels, then copies
        their public attributes onto ``self`` for backward compatibility."""
        self._create_hide_button()

        y = self._create_rule_section()

        # --- Population sub-panel ---
        self.population_controls = PopulationControls(
            self._create_button, self.buttons
        )
        y = self.population_controls._create_population_section(y)

        # --- Evolution sub-panel ---
        self.evolution_controls = EvolutionControls(
            self._create_button, self.buttons
        )
        y = self.evolution_controls._create_evolution_section(y)

        # --- Color / theme sub-panel ---
        self.color_controls = ColorControls(self.theme)
        y = self.color_controls._create_theme_section(y)

        # --- Copy attributes for direct access (simulationscene.py compat) ---
        self._copy_population_attrs()
        self._copy_evolution_attrs()
        self._copy_color_attrs()

        self.y_info = y

    # ------------------------------------------------------------------
    # Attribute forwarding helpers
    # ------------------------------------------------------------------

    def _copy_population_attrs(self) -> None:
        """Copies population-control attributes to ``self``."""
        pc = self.population_controls
        self.y_population_hdr = pc.y_population_hdr
        self.y_density_lbl = pc.y_density_lbl
        self.btn_random_config = pc.btn_random_config
        self.btn_clear_view = pc.btn_clear_view
        self.slider_density = pc.slider_density

    def _copy_evolution_attrs(self) -> None:
        """Copies evolution-control attributes to ``self``."""
        ec = self.evolution_controls
        self.y_evolution_hdr = ec.y_evolution_hdr
        self.btn_evolution = ec.btn_evolution
        self.btn_step = ec.btn_step
        self.btn_pause = ec.btn_pause
        self.btn_save = ec.btn_save
        self.btn_load = ec.btn_load
        self.btn_view_3d = ec.btn_view_3d

    def _copy_color_attrs(self) -> None:
        """Copies color-control attributes to ``self``."""
        cc = self.color_controls
        self.y_theme_lbl = cc.y_theme_lbl
        self.bg_color_selectors = cc.bg_color_selectors

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, screen: pygame.Surface) -> None:
        """Renders the full panel (or just the hide button when collapsed).

        Args:
            screen: The main display surface to blit onto.
        """
        if self.visible:
            self.surface.fill(config.P_BG)

            # =====================================================
            # RULE MATRIX
            # =====================================================

            config.draw_text(
                self.surface,
                self.font_bold,
                "Evolution Rule (512 bits)",
                (config.PAD, self.y_rule_hdr),
                config.P_FG,
            )

            self.rule_panel.draw(self.surface, self.font_small)
            self.kernel_panel.draw(self.surface, self.font_small)

            # Kernel info to the right
            xi = self.x_kernel_info
            yi = self.y_kernel_info
            lines = [
                "Click on each cell of the",
                "kernel to activate it.",
                "The rule is recalculated:",
                "rule[i]=1 if all",
                "active kernel bits",
                "are in index i.",
            ]
            for ln in lines:
                config.draw_text(
                    self.surface, self.font_normal, ln, (xi, yi), config.P_LABEL
                )
                yi += 11
                yi += 4

            config.draw_text(
                self.surface, self.font_normal, "Mask:", (xi, yi), config.P_LABEL
            )
            config.draw_text(
                self.surface,
                self.font_bold,
                f"{self.kernel.mask:09b} ({self.kernel.mask})",
                (xi + 65, yi),
                config.P_VALUE,
            )

            # Rule buttons + density
            self.btn_add_kernel.draw(self.surface, self.font_medium)
            self.btn_random_rule.draw(self.surface, self.font_medium)
            self.btn_clear_rule.draw(self.surface, self.font_medium)

            config.draw_text(
                self.surface,
                self.font_small,
                "Density Rules",
                (self.x_rule_density_lbl, self.y_rule_density_lbl),
                config.P_LABEL,
            )

            self.slider_rule_density.draw(self.surface, self.font_small)

            self.btn_load_rule.draw(self.surface, self.font_medium)
            self.btn_save_rule.draw(self.surface, self.font_medium)

            # =====================================================
            # DELEGATED SECTIONS
            # =====================================================

            self.population_controls.draw(
                self.surface,
                {
                    "bold": self.font_bold,
                    "medium": self.font_medium,
                    "small": self.font_small,
                },
            )

            self.evolution_controls.draw(
                self.surface,
                {
                    "bold": self.font_bold,
                    "medium": self.font_medium,
                },
            )

            self.color_controls.draw(
                self.surface,
                {
                    "medium": self.font_medium,
                    "small": self.font_small,
                },
            )

            # =====================================================
            # BORDER
            # =====================================================

            pygame.draw.rect(
                self.surface,
                config.P_BORDER,
                (0, 0, config.PANEL_W, config.WIN_H),
                1,
            )

            self.btn_hide_panel.draw(self.surface, self.font_medium)

            screen.blit(self.surface, (0, 0))

            pygame.draw.line(
                screen,
                config.P_BORDER,
                (config.PANEL_W, 0),
                (config.PANEL_W, config.WIN_H),
                2,
            )
        else:
            self.btn_hide_panel.draw(screen, self.font_medium)
