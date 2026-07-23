import pygame
from typing import Optional

from core.config import *
from widgets.base_widget import BaseWidget


class Button(BaseWidget):
    """A clickable UI button with optional toggle behavior."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        font: pygame.font.Font,
        toggle: bool = False,
        bg: tuple[int, int, int] = BTN_OFF_BG,
        fg: tuple[int, int, int] = BTN_OFF_FG,
        bg_on: tuple[int, int, int] = (170, 55, 55),
        fg_on: tuple[int, int, int] = (240, 240, 240),
        icon: Optional[pygame.Surface] = None,
    ) -> None:
        """Initializes the button.

        Args:
            rect: Position and size as (x, y, width, height).
            label: Button text.
            font: Font used to render the label.
            toggle: If True, the button stays pressed after clicking.
            bg: Background color when not active.
            fg: Foreground (text) color when not active.
            bg_on: Background color when active.
            fg_on: Foreground color when active.
            icon: Optional icon drawn inside the button.
        """
        self.rect: pygame.Rect = pygame.Rect(rect)
        self.label: str = label
        self.font: pygame.font.Font = font
        self.icon: Optional[pygame.Surface] = icon

        self.toggle: bool = toggle
        self.active: bool = False

        self.bg = bg
        self.fg = fg
        self.bg_on = bg_on
        self.fg_on = fg_on

        self.click_sound = pygame.mixer.Sound("assets/sounds/click_button.wav")
        self.click_sound.set_volume(0.5)

        self._hov: bool = False

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Processes a pygame event for the button."""
        if not self.enabled:
            return False

        if ev.type == pygame.MOUSEMOTION:
            self._hov = self.rect.collidepoint(ev.pos)

        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                if self.click_sound:
                    self.click_sound.play()

                if self.toggle:
                    self.active = not self.active

                return True

        return False

    def draw(self, surf: pygame.Surface) -> None:
        """Draws the button onto a surface."""
        if self.toggle and self.active:
            bg, fg = self.bg_on, self.fg_on
        elif self._hov:
            bg, fg = BTN_HOV, P_FG
        else:
            bg, fg = self.bg, self.fg

        pygame.draw.rect(surf, bg, self.rect, border_radius=4)
        pygame.draw.rect(surf, P_BORDER, self.rect, 1, border_radius=4)

        # Sin icono: comportamiento original
        if self.icon is None:
            text = self.font.render(self.label, True, fg)
            surf.blit(
                text,
                (
                    self.rect.centerx - text.get_width() // 2,
                    self.rect.centery - text.get_height() // 2,
                ),
            )
            return

        # Solo icono
        if self.label == "":
            surf.blit(
                self.icon,
                (
                    self.rect.centerx - self.icon.get_width() // 2,
                    self.rect.centery - self.icon.get_height() // 2,
                ),
            )
            return

        # Icono + texto
        text = self.font.render(self.label, True, fg)

        spacing = 4
        total_height = self.icon.get_height() + spacing + text.get_height()
        top = self.rect.centery - total_height // 2

        surf.blit(
            self.icon,
            (
                self.rect.centerx - self.icon.get_width() // 2,
                top,
            ),
        )

        surf.blit(
            text,
            (
                self.rect.centerx - text.get_width() // 2,
                top + self.icon.get_height() + spacing,
            ),
        )