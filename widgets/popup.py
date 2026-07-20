import pygame
from core import config
from widgets.button import Button

class Popup:

    def __init__(self, rect, title="Popup"):

        self.rect = pygame.Rect(rect)

        self.title = title

        self.visible = False

        self.bg = (28, 28, 34)

        self.border = config.P_BORDER

        self.title_color = config.P_FG

        self.overlay = (0, 0, 0, 180)

        self.fn = pygame.font.SysFont("monospace", 14)
        self.fb = pygame.font.SysFont("monospace", 18, bold=True)

        self.btn_close = Button(
            (
                self.rect.right - 38,
                self.rect.y + 8,
                30,
                30
            ),
            "X"
        )

    def open(self):

        self.visible = True

    def close(self):

        self.visible = False

    def handle_event(self, ev):

        if not self.visible:
            return None

        if self.btn_close.handle_event(ev):
            self.close()
            return "closed"

        return None

    def draw(self, screen):

        if not self.visible:
            return

        overlay = pygame.Surface(
            screen.get_size(),
            pygame.SRCALPHA
        )

        overlay.fill(self.overlay)

        screen.blit(overlay, (0, 0))

        pygame.draw.rect(
            screen,
            self.bg,
            self.rect,
            border_radius=8
        )

        pygame.draw.rect(
            screen,
            self.border,
            self.rect,
            2,
            border_radius=8
        )

        title = self.fb.render(
            self.title,
            True,
            self.title_color
        )

        screen.blit(
            title,
            (
                self.rect.x + 16,
                self.rect.y + 12
            )
        )

        self.btn_close.draw(screen, self.fb)