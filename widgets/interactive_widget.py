"""Abstract base class for interactive widgets.

Defines the common interface that every interactive widget must implement:
a ``pygame.Rect`` for positioning, a ``visible`` flag, an event handler, and a
draw method.  Concrete widgets such as :class:`Button`, :class:`Slider`,
:class:`InputBox`, and :class:`RGBSelector` inherit from this class.

Non-interactive containers like :class:`Popup` do **not** inherit from this
class — they have a different draw signature and lifecycle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pygame


class InteractiveWidget(ABC):
    """Common interface for interactive widgets.

    Every interactive widget exposes a bounding ``rect``, a ``visible``
    flag, and two core methods — :meth:`handle_event` and :meth:`draw`.

    Subclasses **must** override :meth:`handle_event` and :meth:`draw`.  They
    are also expected to set ``self.rect`` (a :class:`pygame.Rect`) in their
    ``__init__``.
    """

    # ------------------------------------------------------------------
    # Abstract interface — must be implemented by every concrete widget
    # ------------------------------------------------------------------

    @abstractmethod
    def handle_event(self, ev: pygame.event.Event) -> Optional[bool]:
        """Process a single pygame event.

        Args:
            ev: The pygame event to process.

        Returns:
            ``True`` if the event was consumed by this widget (e.g. a
            click), ``False`` / ``None`` otherwise.  Concrete subclasses
            may tighten the return type.
        """
        ...

    @abstractmethod
    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        """Render the widget onto a surface.

        Args:
            surf: Target :class:`pygame.Surface` to draw on.
            font: Font used to render any text the widget displays.
        """
        ...

    # ------------------------------------------------------------------
    # Shared interface — documented contract, not enforced by the ABC
    # ------------------------------------------------------------------

    #: Bounding rectangle of the widget (set by ``__init__`` in subclasses).
    rect: pygame.Rect

    @property
    def visible(self) -> bool:
        """Whether the widget is currently visible.

        Returns:
            ``True`` unless the subclass explicitly hides the widget.
        """
        return True
    
    @property
    def enabled(self) -> bool:
        """Whether the widget accepts user interaction.

        Args:
            None.

        Returns:
            ``True`` if the widget can receive user input, ``False`` otherwise.
        """
        return self._enabled

    # ------------------------------------------------------------------
    # Utility methods (usable by all subclasses without overriding)
    # ------------------------------------------------------------------


    def show(self) -> None:
        """Makes the widget visible.

        Args:
            None.

        Returns:
            None.
        """
        self._visible = True

    def hide(self) -> None:
        """Hides the widget.

        The widget remains in memory but will not be drawn or receive events.

        Args:
            None.

        Returns:
            None.
        """
        self._visible = False

    def enable(self) -> None:
        """Enables user interaction.

        A visible widget will once again process input events.

        Args:
            None.

        Returns:
            None.
        """
        self._enabled = True

    def disable(self) -> None:
        """Disables user interaction while keeping the widget visible.

        The widget is still drawn but ignores all input events until
        :meth:`enable` is called.

        Args:
            None.

        Returns:
            None.
        """
        self._enabled = False

    def contains_point(self, pos: tuple[int, int]) -> bool:
        """Check whether *pos* falls inside the widget's bounding rectangle.

        Args:
            pos: An ``(x, y)`` screen coordinate.

        Returns:
            ``True`` if the position is inside :attr:`rect`.
        """
        return self.rect.collidepoint(pos)
