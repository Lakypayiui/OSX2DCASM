"""Kernel widget — 3×3 Moore neighborhood editor using toggle buttons."""

from __future__ import annotations

import pygame

from core.config import (
    BTN_OFF_BG,
    BTN_OFF_FG,
    BTN_ON_BG,
    BTN_ON_FG,
)
from core.kernel import Kernel
from widgets.base_widget import BaseWidget
from widgets.button import Button


class KernelWidget(BaseWidget):
    """Interactive 3×3 grid editor for a Moore neighborhood kernel.

    Each of the nine cells is a toggle :class:`Button`.  The widget
    reads/writes the underlying :class:`Kernel` model directly.
    """

    LABELS = ["NW", "N", "NE", "W", "C", "E", "SW", "S", "SE"]

    def __init__(
        self,
        pos: tuple[int, int],
        kernel: Kernel,
        font: pygame.font.Font,
        cell_size: int = 44,
    ) -> None:
        """Initialise the kernel widget.

        Args:
            pos: ``(x, y)`` top-left position.
            kernel: The :class:`Kernel` model to bind.
            font: Font used for cell labels.
            cell_size: Pixel size of each cell.
        """
        self._kernel = kernel
        self._cell_size = cell_size
        self._font = font

        x, y = pos
        self.rect = pygame.Rect(x, y, cell_size * 3, cell_size * 3)

        self._buttons: list[Button] = []
        for i in range(9):
            bx = x + (i % 3) * cell_size
            by = y + (i // 3) * cell_size
            btn = Button(
                (bx, by, cell_size - 4, cell_size - 4),
                self.LABELS[i],
                font,
                toggle=True,
                bg=BTN_OFF_BG,
                fg=BTN_OFF_FG,
                bg_on=BTN_ON_BG,
                fg_on=BTN_ON_FG,
            )
            btn.active = bool(kernel.bits[i])
            self._buttons.append(btn)

    # ------------------------------------------------------------------
    # BaseWidget interface
    # ------------------------------------------------------------------

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Process a pygame event.

        Each toggle button toggles the corresponding kernel bit and
        updates its visual state.

        Args:
            ev: Pygame event.

        Returns:
            ``True`` if any button was clicked.
        """
        if not self.enabled:
            return False

        for i, btn in enumerate(self._buttons):
            if btn.handle_event(ev):
                self._kernel.bits[i] = 1 if btn.active else 0
                return True
        return False

    def draw(self, surf: pygame.Surface) -> None:
        """Draw the 3×3 grid onto *surf*.

        Args:
            surf: Target surface.
        """
        if not self.visible:
            return
        for btn in self._buttons:
            btn.draw(surf)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def total_w(self) -> int:
        """Total pixel width of the widget."""
        return self._cell_size * 3

    @property
    def total_h(self) -> int:
        """Total pixel height of the widget."""
        return self._cell_size * 3

    def sync_from_kernel(self) -> None:
        """Refresh all button states from the underlying kernel model."""
        for i, btn in enumerate(self._buttons):
            btn.active = bool(self._kernel.bits[i])

    def clear(self) -> None:
        """Reset all buttons to off and clear the kernel."""
        self._kernel.clear()
        self.sync_from_kernel()
