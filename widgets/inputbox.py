import pygame

class InputBox:
    def __init__(self, rect, text="", numeric_only=False):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.active = False
        self.numeric_only = numeric_only

        self.bg = (28, 28, 36)
        self.border = (70, 70, 90)
        self.border_active = (120, 180, 255)
        self.fg = (230, 230, 240)

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(ev.pos)

        if ev.type == pygame.KEYDOWN and self.active:

            if ev.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]

            elif ev.key == pygame.K_RETURN:
                pass

            else:
                if self.numeric_only:
                    if ev.unicode.isdigit():
                        self.text += ev.unicode
                else:
                    if ev.unicode.isprintable():
                        self.text += ev.unicode

    def draw(self, surf, font):
        pygame.draw.rect(surf, self.bg, self.rect, border_radius=6)

        border_color = self.border_active if self.active else self.border
        pygame.draw.rect(
            surf,
            border_color,
            self.rect,
            width=2,
            border_radius=6
        )

        txt = font.render(self.text, True, self.fg)
        surf.blit(
            txt,
            (
                self.rect.x + 10,
                self.rect.y + (self.rect.height - txt.get_height()) // 2
            )
        )

    def value(self, default=128):
        try:
            return max(1, int(self.text))
        except:
            return default