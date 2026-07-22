from __future__ import annotations
from typing import List, Optional, Tuple
import pygame

from .interactive_widget import InteractiveWidget  # Adjust import based on your project structure


class Accordion(InteractiveWidget):
    """A collapsible container widget that displays a header and optional content.

    The accordion consists of a clickable header (with label) and a list of
    child widgets that are shown only when expanded. It follows the
    InteractiveWidget interface for event handling and rendering.
    """

    def __init__(
        self,
        rect: pygame.Rect,
        label: str,
        widgets: List[InteractiveWidget],
        expanded: bool = False,
        padding: int = 8,
        header_height: int = 40,
        content_padding: int = 10,
        colors: Optional[dict] = None,
    ) -> None:
        """Initializes the Accordion widget.

        Args:
            rect: The bounding rectangle for the entire accordion.
            label: Text displayed in the header.
            widgets: List of InteractiveWidget children to display when expanded.
            expanded: Whether the accordion starts expanded.
            padding: Horizontal padding for content and header elements.
            header_height: Height of the clickable header section.
            content_padding: Vertical spacing between child widgets.
            colors: Optional dictionary to override default colors.
        """
        self.rect = rect.copy()
        self.label = label
        self.widgets: List[InteractiveWidget] = widgets
        self._expanded = expanded
        self.padding = padding
        self.header_height = header_height
        self.content_padding = content_padding

        # Default color scheme
        self.colors = colors or {
            "header_bg": (60, 60, 70),
            "header_hover": (80, 80, 90),
            "header_text": (255, 255, 255),
            "content_bg": (45, 45, 55),
            "border": (100, 100, 110),
        }

        self._enabled = True
        self._visible = True
        self._hov = False

        # Header rectangle (used for hit detection and drawing)
        self._header_rect = pygame.Rect(
            rect.x, rect.y, rect.width, header_height
        )

        self._update_layout()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def expanded(self) -> bool:
        """Returns whether the accordion is currently expanded."""
        return self._expanded

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def toggle(self) -> None:
        """Toggles the expanded/collapsed state of the accordion."""
        self._expanded = not self._expanded
        self._update_layout()

    def expand(self) -> None:
        """Expands the accordion to show its content."""
        if not self._expanded:
            self._expanded = True
            self._update_layout()

    def collapse(self) -> None:
        """Collapses the accordion, hiding its content."""
        if self._expanded:
            self._expanded = False
            self._update_layout()

    def add_widget(self, widget: InteractiveWidget) -> None:
        """Adds a new widget to the accordion's content area.

        Args:
            widget: The InteractiveWidget to add.
        """
        self.widgets.append(widget)
        self._update_layout()

    def clear_widgets(self) -> None:
        """Removes all child widgets from the accordion."""
        self.widgets.clear()
        self._update_layout()

    # ------------------------------------------------------------------
    # InteractiveWidget interface implementation
    # ------------------------------------------------------------------

    def handle_event(self, ev: pygame.event.Event) -> Optional[bool]:
        """Processes a single pygame event.

        Handles clicks on the header to toggle expansion and forwards
        events to child widgets when expanded.

        Returns:
            True if the event was consumed, None/False otherwise.
        """
        if not self._visible or not self._enabled:
            return None

        if ev.type == pygame.MOUSEMOTION:
            self._hov = self._header_rect.collidepoint(ev.pos)
        # Handle header click
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self._header_rect.collidepoint(ev.pos):
                self.toggle()
                return True

        # Forward events to children only when expanded
        if self._expanded:
            for widget in self.widgets:
                if widget.visible and getattr(widget, 'enabled', True):
                    consumed = widget.handle_event(ev)
                    if consumed:
                        return True

        return None

    def draw(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        """Renders the accordion and its children (if expanded) to the surface.

        Args:
            surf: Target surface to draw on.
            font: Font used for text rendering.
        """
        if not self._visible:
            return

        # Draw header
        header_color = (
            self.colors["header_hover"] if self._hov
            else self.colors["header_bg"]
        )
        pygame.draw.rect(surf, header_color, self._header_rect)
        pygame.draw.rect(surf, self.colors["border"], self._header_rect, width=2)

        # Draw label
        text_surf = font.render(self.label, True, self.colors["header_text"])
        text_rect = text_surf.get_rect(
            midleft=(self._header_rect.x + 15, self._header_rect.centery)
        )
        surf.blit(text_surf, text_rect)

        # Draw expand/collapse arrow
        arrow = "▼" if self._expanded else "▶"
        arrow_surf = font.render(arrow, True, self.colors["header_text"])
        arrow_rect = arrow_surf.get_rect(
            midright=(self._header_rect.right - 15, self._header_rect.centery)
        )
        surf.blit(arrow_surf, arrow_rect)

        # Draw expanded content
        if self._expanded:
            content_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.header_height,
                self.rect.width,
                self.rect.height - self.header_height
            )
            pygame.draw.rect(surf, self.colors["content_bg"], content_rect)
            pygame.draw.rect(surf, self.colors["border"], content_rect, width=2)

            # Draw child widgets
            for widget in self.widgets:
                if widget.visible:
                    widget.draw(surf, font)

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _update_layout(self) -> None:
        """Recalculates positions and total height of the accordion.

        Should be called whenever the expanded state or children change.
        """
        if not self._expanded:
            # Only header is visible when collapsed
            self.rect.height = self.header_height
            return

        # Position child widgets
        y = self.rect.y + self.header_height + self.content_padding
        content_width = self.rect.width - 2 * self.padding

        for widget in self.widgets:
            if not hasattr(widget, 'rect'):
                continue

            widget.rect.x = self.rect.x + self.padding
            widget.rect.y = y
            widget.rect.width = content_width

            y += widget.rect.height + self.content_padding

        # Update total height
        total_content_h = y - (self.rect.y + self.header_height + self.content_padding)
        self.rect.height = (
            self.header_height + self.content_padding + total_content_h + self.padding
        )