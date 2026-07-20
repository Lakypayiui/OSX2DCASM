import pygame

from core import config

from core.kernel import Kernel
from core.rule_matrix import RuleMatrix

from widgets.button import Button
from widgets.slider import Slider
from widgets.rgbselector import RGBSelector

from ui.panels import (
    KernelPanel,
    RulePanel,
)


class SimulationPanel:

    BUTTON_WIDTH = 183
    BUTTON_HEIGHT = 22
    BUTTON_GAP = 4

    def __init__(
        self,
        rule_matrix: RuleMatrix,
        kernel: Kernel,
        theme: dict[str, tuple[int, int, int]],
        fonts: dict[str, pygame.font.Font]
    ) -> None:
        """Initializes the simulation control panel.

        Args:
            rule_matrix: Rule matrix model displayed by the panel.
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

        self.surface = pygame.Surface(
            (config.PANEL_W, config.WIN_H)
        )
        

    def _create_button(
        self,
        label: str,
        column: int,
        y: int,
        toggle: bool = False,
        bg: tuple = config.BTN_OFF_BG,
        bg_on: tuple = config.BTN_ON_BG,
    ) -> Button:
        return Button(
            (config.PAD + column * (self.BUTTON_WIDTH + self.BUTTON_GAP), y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT),
            label,
            toggle=toggle,
            bg=bg,
            bg_on=bg_on
        )

    def _create_hide_button(self) -> None:
        self.btn_hide_panel = Button(
            (config.PANEL_W - config.PAD - 40, config.PAD, 40, 20),
            "<<",
            toggle=False,
            bg=config.BTN_OFF_BG,
            bg_on=config.BTN_ON_BG
        )
        self.buttons.append(self.btn_hide_panel)
    
    def _create_rule_section(self) -> int:
        y = config.PAD

        self.y_rule_hdr = y

        y += 28

        matrix_x = config.PAD + 16

        self.rule_panel = RulePanel(self.rule_matrix, matrix_x, y)

        y += self.rule_panel.total_h + config.PAD + 18

        kernel_x = matrix_x

        self.kernel_panel = KernelPanel(
            self.kernel,
            kernel_x,
            y
        )

        self.x_kernel_info = kernel_x + self.kernel_panel.total_w + 16
        self.y_kernel_info = y

        self.btn_add_kernel = self._create_button(
            "Add kernel",
            2,
            y
        )
        self.buttons.append(self.btn_add_kernel)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_random_rule = self._create_button(
            "Random rule",
            2,
            y
        )
        self.buttons.append(self.btn_random_rule)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_clear_rule = self._create_button(
            "Clear rule",
            2,
            y
        )
        self.buttons.append(self.btn_clear_rule)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP + 4

        # Density slider
        self.y_rule_density_lbl = y
        self.x_rule_density_lbl = config.PAD + 2 * (self.BUTTON_WIDTH + self.BUTTON_GAP)

        y += 13

        self.slider_rule_density = Slider(
            (self.x_rule_density_lbl , y,  int(self.BUTTON_WIDTH*1.4), 12),
            value=0.5
        )

        y += 24

        self.btn_load_rule = self._create_button(
            "Load Rule",
            2,
            y
        )
        self.buttons.append(self.btn_load_rule)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_save_rule = self._create_button(
            "Save Rule",
            2,
            y
        )
        self.buttons.append(self.btn_save_rule)

        y += config.PAD + 40

        self.y_sep2 = y

        y += config.PAD

        return y

    def _create_population_section(self, y) -> int:

        self.y_population_hdr = y

        y += 25

        self.btn_random_config = self._create_button(
            "Random config",
            0,
            y
        )
        self.buttons.append(self.btn_random_config)

        self.btn_clear_view = self._create_button(
            "Clear view",
            1,
            y
        )
        self.buttons.append(self.btn_clear_view)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP + 4

        # Density slider
        self.y_density_lbl = y

        y += 13

        self.slider_density = Slider(
            (config.PAD, y, config.PANEL_W - 65, 12),
            value=0.5
        )

        y += 40 + config.PAD

        return y
    
    def _create_evolution_section(self, y) -> int:

        self.y_evolution_hdr = y

        y += 25

        self.btn_evolution = self._create_button(
            "Start",
            0,
            y,
            toggle=True,
            bg=(45, 120, 60)
        )
        self.buttons.append(self.btn_evolution)

        self.btn_step = self._create_button(
            "Step",
            1,
            y
        )
        self.buttons.append(self.btn_step)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_pause = self._create_button(
            "Pause",
            0,
            y,
            toggle=True,
        )
        self.buttons.append(self.btn_pause)

        self.btn_view_3d = self._create_button(
            "3D View",
            1,
            y
        )
        self.buttons.append(self.btn_view_3d)

        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_save = self._create_button(
            "Save",
            0,
            y
        )
        self.buttons.append(self.btn_save)

        self.btn_load = self._create_button(
            "Load",
            1,
            y
        )
        self.buttons.append(self.btn_load)

        y += 40

        return y

    def _create_theme_section(self, y) -> int:
        self.y_theme_lbl = y

        y += 13

        self.bg_color_selectors = []

        labels_colors = ["bg", "grid", "cell"]
        CSW = (config.PANEL_W - config.PAD) // len(labels_colors) - 2
        for idx, lc in enumerate(labels_colors):
            bx = config.PAD + idx * (CSW + 2)
            self.bg_color_selectors.append(RGBSelector(
                (bx, y, CSW, 80), initial=self.theme[lc.lower().replace(" ", "")]
            ))

        y += 17 + config.PAD
        return y

    def _build_layout(self) -> None:
        self._create_hide_button()

        y = self._create_rule_section()

        y = self._create_population_section(y)

        y = self._create_evolution_section(y)

        y = self._create_theme_section(y)

        self.y_info = y

    def draw(self, screen):
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
                config.P_FG
            )

            self.rule_panel.draw(
                self.surface,
                self.font_small
            )

            self.kernel_panel.draw(
                self.surface,
                self.font_small
            )

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
                config.draw_text(self.surface, self.font_normal, ln, (xi, yi), config.P_LABEL) 
                yi += 11 
                yi += 4 
            config.draw_text(self.surface, self.font_normal, "Mask:", (xi, yi), config.P_LABEL) 
            config.draw_text(self.surface, self.font_bold, f"{self.kernel.mask:09b} ({self.kernel.mask})", (xi + 65, yi), config.P_VALUE)

            # =====================================================
            # RULES SECTION
            # =====================================================

            self.btn_add_kernel.draw(self.surface, self.font_medium)
            self.btn_random_rule.draw(self.surface, self.font_medium)
            self.btn_clear_rule.draw(self.surface, self.font_medium)

            config.draw_text(
                self.surface,
                self.font_small,
                "Density Rules",
                (self.x_rule_density_lbl, self.y_rule_density_lbl),
                config.P_LABEL
            )

            self.slider_rule_density.draw(self.surface, self.font_small)

            self.btn_load_rule.draw(self.surface, self.font_medium)
            self.btn_save_rule.draw(self.surface, self.font_medium)

            # =====================================================
            # POPULATION SECTION
            # =====================================================

            config.draw_text(
                self.surface,
                self.font_bold,
                "Population",
                (config.PAD, self.y_population_hdr),
                config.P_FG
            )

            pygame.draw.line(
                self.surface,
                config.P_BORDER,
                (config.PAD, self.y_population_hdr + 16),
                (config.PANEL_W - config.PAD, self.y_population_hdr + 16)
            )

            self.btn_random_config.draw(self.surface, self.font_medium)
            self.btn_clear_view.draw(self.surface, self.font_medium)

            config.draw_text(
                self.surface,
                self.font_small,
                "Density Population",
                (config.PAD, self.y_density_lbl),
                config.P_LABEL
            )

            self.slider_density.draw(self.surface, self.font_small)

            # =====================================================
            # EVOLUTION SECTION
            # =====================================================

            config.draw_text(
                self.surface,
                self.font_bold,
                "Evolution",
                (config.PAD, self.y_evolution_hdr),
                config.P_FG
            )

            pygame.draw.line(
                self.surface,
                config.P_BORDER,
                (config.PAD, self.y_evolution_hdr + 16),
                (config.PANEL_W - config.PAD, self.y_evolution_hdr + 16)
            )

            self.btn_evolution.draw(self.surface, self.font_medium)
            self.btn_step.draw(self.surface, self.font_medium)

            self.btn_pause.draw(self.surface, self.font_medium)

            self.btn_save.draw(self.surface, self.font_medium)

            self.btn_view_3d.draw(self.surface, self.font_medium)
            
            self.btn_load.draw(self.surface, self.font_medium)

            # =====================================================
            # COLORS
            # =====================================================

            for idx, lc in enumerate(["Background", "Grid", "Cell"]):

                config.draw_text(
                    self.surface,
                    self.font_medium,
                    lc,
                    (
                        config.PAD + idx * ((config.PANEL_W - config.PAD) // 3),
                        self.y_theme_lbl
                    ),
                    config.P_LABEL
                )

            for idx, b in enumerate(self.bg_color_selectors):
                b.draw(self.surface, self.font_small)


            # =====================================================
            # BORDER
            # =====================================================

            pygame.draw.rect(
                self.surface,
                config.P_BORDER,
                (0, 0, config.PANEL_W, config.WIN_H),
                1
            )

            self.btn_hide_panel.draw(self.surface, self.font_medium)

            screen.blit(self.surface, (0, 0))

            pygame.draw.line(
                screen,
                config.P_BORDER,
                (config.PANEL_W, 0),
                (config.PANEL_W, config.WIN_H),
                2
            )
        else:
            self.btn_hide_panel.draw(screen,self.font_medium)
