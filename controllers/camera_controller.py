from typing import Optional

import pygame

from core import config


class CameraController:
    """Controls zoom and pan of the automaton viewport."""

    def __init__(self) -> None:
        """Initializes the camera controller."""

        self.scroll_x: int = 0
        self.scroll_y: int = 0

        self.dragging: bool = False
        self.last_mouse_pos: tuple[int, int] = (0, 0)

    def _zoom(self, direction: int) -> None:
        """Updates the zoom level.

        Args:
            direction: Positive to zoom in, negative to zoom out.
        """

        if direction > 0:
            config.CELL_PX *= 1.6
        else:
            config.CELL_PX /= 1.6

        config.CELL_PX = max(2, int(config.CELL_PX))

    def _drag(self) -> None:
        """Moves the camera while dragging."""

        mx, my = pygame.mouse.get_pos()

        dx: int = mx - self.last_mouse_pos[0]
        dy: int = my - self.last_mouse_pos[1]

        self.scroll_x -= dx
        self.scroll_y -= dy

        self.last_mouse_pos = (mx, my)

    def handle_event(
        self,
        event: pygame.event.Event,
        panel_visible: bool,
        popup_open: bool,
        panel_width: int
    ) -> None:
        """Processes a pygame event for camera control.

        Args:
            event: Pygame event to process.
            panel_visible: Whether the side panel is visible (blocks zoom if the
                mouse is over it).
            popup_open: Whether a popup is open (blocks zoom).
        """

        if event.type == pygame.MOUSEWHEEL:

            if popup_open:
                return

            mx, _ = pygame.mouse.get_pos()

            if panel_visible and mx < panel_width:
                return

            self._zoom(event.y)
        
        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 3:
                self.dragging = True
                self.last_mouse_pos = pygame.mouse.get_pos()

        if event.type == pygame.MOUSEBUTTONUP:

            if event.button == 3:
                self.dragging = False

        if event.type == pygame.MOUSEMOTION:

            if self.dragging:
                self._drag()
