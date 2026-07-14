from core.config import *
import pygame

class RGBSelector:
    def __init__(self, rect, initial=(128, 128, 128)):
        self.rect = pygame.Rect(rect)
        
        # Sub-rects para sliders
        h = self.rect.height // 4
        self.r_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, h)
        self.g_rect = pygame.Rect(self.rect.x, self.rect.y + h, self.rect.width, h)
        self.b_rect = pygame.Rect(self.rect.x, self.rect.y + 2*h, self.rect.width, h)
        self.preview_rect = pygame.Rect(self.rect.x, self.rect.y + 3*h, self.rect.width, h)

        self.r, self.g, self.b = initial
        self.dragging = None  # "r", "g", "b"

    def _get_value_from_pos(self, rect, x):
        rel = (x - rect.x) / rect.width
        return max(0, min(255, int(rel * 255)))

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.r_rect.collidepoint(ev.pos):
                self.dragging = "r"
            elif self.g_rect.collidepoint(ev.pos):
                self.dragging = "g"
            elif self.b_rect.collidepoint(ev.pos):
                self.dragging = "b"

        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dragging = None

        elif ev.type == pygame.MOUSEMOTION:
            if self.dragging:
                x = ev.pos[0]
                if self.dragging == "r":
                    self.r = self._get_value_from_pos(self.r_rect, x)
                elif self.dragging == "g":
                    self.g = self._get_value_from_pos(self.g_rect, x)
                elif self.dragging == "b":
                    self.b = self._get_value_from_pos(self.b_rect, x)

    def get_color(self):
        return (self.r, self.g, self.b)

    def draw_slider(self, surf, rect, value, color, label, font):
        # Fondo
        pygame.draw.rect(surf, BTN_OFF_BG, rect, border_radius=4)
        pygame.draw.rect(surf, P_BORDER, rect, 1, border_radius=4)

        # Barra de color
        fill_w = int((value / 255) * rect.width)
        fill_rect = pygame.Rect(rect.x, rect.y, fill_w, rect.height)
        pygame.draw.rect(surf, color, fill_rect, border_radius=4)

        # Texto
        txt = f"{label}: {value}"
        t = font.render(txt, True, P_FG)
        surf.blit(t, (rect.x + 6, rect.y + rect.height // 2 - t.get_height() // 2))

    def draw(self, surf, font):
        # Sliders
        self.draw_slider(surf, self.r_rect, self.r, (255, 0, 0), "R", font)
        self.draw_slider(surf, self.g_rect, self.g, (0, 255, 0), "G", font)
        self.draw_slider(surf, self.b_rect, self.b, (0, 0, 255), "B", font)

        # Preview color
        color = self.get_color()
        pygame.draw.rect(surf, color, self.preview_rect, border_radius=4)
        pygame.draw.rect(surf, P_BORDER, self.preview_rect, 1, border_radius=4)

        # Texto del color
        txt = f"RGB{color}"
        t = font.render(txt, True, P_FG)
        surf.blit(t, (self.preview_rect.centerx - t.get_width() // 2,
                      self.preview_rect.centery - t.get_height() // 2))