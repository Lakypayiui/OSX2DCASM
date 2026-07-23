"""Base class for all widgets except :class:`Popup`.

Defines the common contract that every widget must fulfill:
a ``pygame.Rect`` for positioning, ``visible`` / ``enabled`` flags,
:meth:`handle_event`, and :meth:`draw`.

Concrete widgets such as :class:`Button`, :class:`Slider`,
:class:`InputBox`, :class:`RGBSelector`, :class:`GraphWidget`,
:class:`Label`, and :class:`Accordion` inherit from this class.

:class:`Popup` is deliberately excluded — it has a different draw
signature and lifecycle.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

import pygame


class BaseWidget(ABC):
    """Common contract for all non-Popup widgets.

    Every widget exposes:

    * ``rect`` — bounding rectangle (set by ``__init__``).
    * ``visible`` — whether the widget is drawn.
    * ``enabled`` — whether the widget processes input events.

    Subclasses **must** implement :meth:`handle_event` and :meth:`draw`.
    """

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def handle_event(self, ev: pygame.event.Event) -> Optional[bool]:
        """Process a single pygame event.

        Implementations should return early with ``None`` / ``False``
        when ``self.enabled`` is ``False`` or ``self.visible`` is
        ``False``.

        Args:
            ev: The pygame event to process.

        Returns:
            ``True`` if the event was consumed, otherwise ``None`` or
            ``False``.
        """
        ...

    @abstractmethod
    def draw(self, surf: pygame.Surface) -> None:
        """Render the widget onto a surface.

        Args:
            surf: Target :class:`pygame.Surface` to draw on.
        """
        ...

    # ------------------------------------------------------------------
    # Shared interface
    # ------------------------------------------------------------------

    rect: pygame.Rect  #: Set by ``__init__`` in concrete subclasses.

    @property
    def visible(self) -> bool:
        """Whether the widget is currently visible."""
        return getattr(self, "_visible", True)

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

    @property
    def enabled(self) -> bool:
        """Whether the widget accepts user interaction."""
        return getattr(self, "_enabled", True)

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Make the widget visible."""
        self._visible = True

    def hide(self) -> None:
        """Hide the widget (still in memory, but not drawn / interactive)."""
        self._visible = False

    def enable(self) -> None:
        """Enable user interaction."""
        self._enabled = True

    def disable(self) -> None:
        """Disable user interaction while keeping the widget visible."""
        self._enabled = False

    def contains_point(self, pos: tuple[int, int]) -> bool:
        """Check whether *pos* falls inside the widget's bounding rectangle.

        Args:
            pos: An ``(x, y)`` screen coordinate.

        Returns:
            ``True`` if the position is inside :attr:`rect`.
        """
        return self.rect.collidepoint(pos)
