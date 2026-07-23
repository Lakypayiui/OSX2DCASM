"""Rule controls sub-panel — rule matrix, kernel, buttons, density slider."""

from __future__ import annotations

from typing import Callable

import pygame

from core import config
from core.kernel import Kernel
from core.rule_matrix import RuleMatrix
from widgets.accordion import Accordion
from widgets.kernel_widget import KernelWidget
from ui.panels.rule_panel import RulePanel
from widgets.button import Button
from widgets.label import Label
from widgets.slider import Slider


class RuleControls:
    """Rule-matrix editor, kernel panel, and associated controls.

    Attributes:
        y_rule_hdr: Y-position of the rule section header.
        _height: Total height of this sub-panel.
        rule_panel: :class:`RulePanel` widget.
        kernel_panel: :class:`KernelWidget` widget.
        x_kernel_info, y_kernel_info: Kernel info text anchor.
        btn_add_kernel, btn_random_rule, btn_clear_rule: Rule action buttons.
        btn_load_rule, btn_save_rule: Rule preset buttons.
        slider_rule_density, y_rule_density_lbl: Rule density slider + label Y.
    """

    BUTTON_WIDTH = 183
    BUTTON_HEIGHT = 22
    BUTTON_GAP = 4

    def __init__(
        self,
        rule_matrix: RuleMatrix,
        kernel: Kernel,
        create_button: Callable[..., Button],
        buttons_list: list[Button],
        width: int,
        fonts: dict[str, pygame.font.Font],
    ) -> None:
        self.rule_matrix = rule_matrix
        self.kernel = kernel
        self.width = width
        self.fonts = fonts
        self._create_button = create_button
        self._buttons_list = buttons_list

        self._height: int = 0
        self.y_rule_hdr: int = 0
        self.y_rule_density_lbl: int = 0
        self.x_rule_density_lbl: int = 0
        self.x_kernel_info: int = 0
        self.y_kernel_info: int = 0

        self.rule_panel: RulePanel | None = None
        self.kernel_panel: KernelWidget | None = None
        self._rule_header_label: Label | None = None
        self._kernel_info_labels: list[Label] = []
        self._mask_label: Label | None = None
        self._mask_value_label: Label | None = None

        self.btn_add_kernel: Button | None = None
        self.btn_random_rule: Button | None = None
        self.btn_clear_rule: Button | None = None
        self.btn_load_rule: Button | None = None
        self.btn_save_rule: Button | None = None
        self.slider_rule_density: Slider | None = None
        self._density_rules_label: Label | None = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _create_rule_section(self, y: int) -> int:
        """Build widgets at *y* and return the next free y."""
        return self.update_layout(y, True)

    def update_layout(self, y: int, create: bool = False) -> int:
        """Reposition all widgets starting at *y* and recalculate height."""
        start_y = y
        self.y_rule_hdr = y
        self._rule_header_label = Label(
            (config.PAD, y), "Evolution Rule (512 bits)", self.fonts["bold"], config.P_FG,
        )
        y += 25

        matrix_x = config.PAD + 16
        self.rule_panel = RulePanel(self.rule_matrix, matrix_x, y, self.width * 0.9)
        y += self.rule_panel.total_h + config.PAD + 18

        self.rule_accordion = Accordion(
            rect=pygame.Rect(config.PAD, y, self.width - config.PAD * 2, 40),
            label="Rules",
            font=self.fonts["bold"],
            widgets=[],
            expanded=False if create else self.rule_accordion.expanded,
        )

        y += 50
        kernel_x = matrix_x
        self.kernel_panel = KernelWidget((kernel_x, y), self.kernel, self.fonts["bold"])
        self.rule_accordion.add_widget(self.kernel_panel)
    
        self.x_kernel_info = kernel_x + self.kernel_panel.total_w + 16
        self.y_kernel_info = y

        self._kernel_info_labels.clear()
        xi, yi = self.x_kernel_info, self.y_kernel_info
        for ln in [
            "Click on each cell of the", "kernel to activate it.",
            "The rule is recalculated:", "rule[i]=1 if all",
            "active kernel bits", "are in index i.",
        ]:
            self._kernel_info_labels.append(Label((xi, yi), ln, self.fonts["normal"], config.P_LABEL))
            yi += 15
        for label in self._kernel_info_labels:
            self.rule_accordion.add_widget(label)

        self._mask_label = Label((xi, yi), "Mask:", self.fonts["normal"], config.P_LABEL)
        self.rule_accordion.add_widget(self._mask_label)
        self._mask_value_label = Label((xi + 65, yi), "", self.fonts["bold"], config.P_VALUE)
        self.rule_accordion.add_widget(self._mask_value_label)

        self.btn_add_kernel = self._create_button("Add kernel", 2, y)
        self.rule_accordion.add_widget(self.btn_add_kernel)
        self._buttons_list.append(self.btn_add_kernel)
        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_random_rule = self._create_button("Random rule", 2, y)
        self.rule_accordion.add_widget(self.btn_random_rule)
        self._buttons_list.append(self.btn_random_rule)
        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_clear_rule = self._create_button("Clear rule", 2, y)
        self.rule_accordion.add_widget(self.btn_clear_rule)
        self._buttons_list.append(self.btn_clear_rule)
        y += self.BUTTON_HEIGHT + self.BUTTON_GAP + 4

        self.y_rule_density_lbl = y
        self.x_rule_density_lbl = config.PAD + 2 * (self.BUTTON_WIDTH + self.BUTTON_GAP)
        self._density_rules_label = Label(
            (self.x_rule_density_lbl, y), "Density Rules", self.fonts["small"], config.P_LABEL,
        )
        self.rule_accordion.add_widget(self._density_rules_label)
        y += 13

        self.slider_rule_density = Slider(
            (self.x_rule_density_lbl, y, int(self.BUTTON_WIDTH * 1.4), 12),
            self.fonts["medium"], value=0.5,
        )
        self.rule_accordion.add_widget(self.slider_rule_density)
        y += 24

        self.btn_load_rule = self._create_button("Load Rule", 2, y)
        self._buttons_list.append(self.btn_load_rule)
        self.rule_accordion.add_widget(self.btn_load_rule)
        y += self.BUTTON_HEIGHT + self.BUTTON_GAP

        self.btn_save_rule = self._create_button("Save Rule", 2, y)
        self.rule_accordion.add_widget(self.btn_save_rule)
        self._buttons_list.append(self.btn_save_rule)

        self._height = self._calc_height()
        return start_y + self._height

    def _calc_height(self) -> int:
        """Return the total pixel height of this sub-panel.
        Approximate — exact value depends on rule_panel.total_h."""
        return (
            50 + (self.rule_panel.total_h + config.PAD + 18) + self.rule_accordion.rect.height
        )

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the rule section onto *surface*."""
        assert self._rule_header_label is not None
        self._rule_header_label.draw(surface)

        assert self.rule_panel is not None
        self.rule_panel.draw(surface, self.fonts["medium"])
        
        self.rule_accordion.draw(surface)