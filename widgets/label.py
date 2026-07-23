"""Non-interactive text label widget.

A lightweight widget that renders a single line of text.  It inherits
from :class:`BaseWidget` so it can be composed alongside interactive
widgets inside containers such as :class:`Accordion` or used as a
drop-in replacement for ``config.draw_text`` calls.
"""

from __future__ import annotations

import pygame

from widgets.base_widget import BaseWidget


class Label(BaseWidget):
    """A read-only text label.

    Positions itself via ``rect`` and renders ``text`` using the font
    passed to :meth:`draw`.  Alignment is controlled by ``align``
    (``"left"``, ``"center"``, or ``"right"``).

    Because labels are non-interactive, :meth:`handle_event` always
    returns ``None``.
    """

    def __init__(
        self,
        pos: tuple[int, int],
        text: str,
        font: pygame.font.Font,
        color: tuple[int, int, int] = (255, 255, 255),
        align: str = "left"
    ) -> None:
        """Initialise the label.

        Args:
            pos: ``(x, y)`` screen position.
            text: Text to display.
            color: RGB colour tuple.
            align: ``"left"``, ``"center"``, or ``"right"``.
            font: Font used to render the text to display.
        """
        # rect is just a position marker; width/height are set on draw.
        self.rect = pygame.Rect(pos[0], pos[1], 0, 0)
        self.text = text
        self.color = color
        self.align = align
        self.font = font

    # ------------------------------------------------------------------
    # BaseWidget interface
    # ------------------------------------------------------------------

    def handle_event(self, ev: pygame.event.Event) -> None:
        """No-op — labels are read-only.

        Args:
            ev: Ignored.

        Returns:
            Always ``None``.
        """
        return None

    def draw(self, surf: pygame.Surface) -> None:
        """Render the label onto *surf*.

        Args:
            surf: Target surface.
            font: Font used to render ``self.text``.
        """
        if not self.visible:
            return

        img = self.font.render(self.text, True, self.color)
        x, y = self.rect.topleft

        if self.align == "right":
            x -= img.get_width()
        elif self.align == "center":
            x -= img.get_width() // 2

        self.rect.width = img.get_width()
        self.rect.height = img.get_height()
        surf.blit(img, (x, y))
