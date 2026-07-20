import pygame

from core import config


class CameraController:

    def __init__(self) -> None:
        """Initializes the camera controller."""

        self.scroll_x = 0
        self.scroll_y = 0

        self.dragging = False
        self.last_mouse_pos = (0, 0)

    def _zoom(self, direction: int) -> None:
        """Updates the zoom level."""

        if direction > 0:
            config.CELL_PX *= 1.6
        else:
            config.CELL_PX /= 1.6

        config.CELL_PX = max(2, int(config.CELL_PX))

    def _drag(self) -> None:
        """Moves the camera while dragging."""

        mx, my = pygame.mouse.get_pos()

        dx = mx - self.last_mouse_pos[0]
        dy = my - self.last_mouse_pos[1]

        self.scroll_x -= dx
        self.scroll_y -= dy

        self.last_mouse_pos = (mx, my)

    def handle_event(
        self,
        event: pygame.event.Event,
        panel_visible: bool,
        popup_open: bool,
    ) -> None:
        
        if event.type == pygame.MOUSEWHEEL:

            if popup_open:
                return

            mx, _ = pygame.mouse.get_pos()

            if panel_visible and mx < config.PANEL_W:
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