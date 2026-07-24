from time import sleep
import pygame
from typing import Optional

from core.config import *
from widgets.base_widget import BaseWidget

_ui_volume: float = 0.5


def set_ui_volume(volume: float) -> None:
    """Set the global UI sound volume (0.0 – 1.0)."""
    global _ui_volume
    _ui_volume = max(0.0, min(1.0, volume))


def get_ui_volume() -> float:
    """Return the current global UI sound volume."""
    return _ui_volume


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
        bg_hov: tuple[int, int, int] = BTN_HOV,
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
        self.bg_hov = bg_hov

        self.click_sound = pygame.mixer.Sound("assets/sounds/click_button.wav")
        self.click_sound.set_volume(_ui_volume)

        self._hov: bool = False

        self.scale: float = 1.0
        self.target_scale: float = 1.0
        self.lerp_speed: float = 0.25

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
            self.target_scale = 1.0
        elif self._hov:
            bg, fg = self.bg_hov, self.fg
            self.target_scale = 1.08
        else:
            bg, fg = self.bg, self.fg
            self.target_scale = 1.0

        self.scale += (self.target_scale - self.scale) * self.lerp_speed

        draw_rect = self.rect.copy()
        
        if abs(self.scale - 1.0) > 0.01:
            new_w = int(self.rect.width * self.scale)
            new_h = int(self.rect.height * self.scale)
            draw_rect = pygame.Rect(0, 0, new_w, new_h)
            draw_rect.center = self.rect.center

        pygame.draw.rect(surf, bg, draw_rect, border_radius=6)
        pygame.draw.rect(surf, P_BORDER, draw_rect, 2, border_radius=6)

        content_rect = draw_rect

        text_surf = self.font.render(self.label, True, fg)

        if abs(self.scale - 1.0) > 0.01:
            new_text_size = (
                int(text_surf.get_width() * self.scale),
                int(text_surf.get_height() * self.scale)
            )
            text_surf = pygame.transform.smoothscale(text_surf, new_text_size)

        
        if self.icon is None:
            surf.blit(
                text_surf,
                (
                    content_rect.centerx - text_surf.get_width() // 2,
                    content_rect.centery - text_surf.get_height() // 2,
                ),
            )
            return

        
        if self.label == "":
            surf.blit(
                self.icon,
                (
                    content_rect.centerx - self.icon.get_width() // 2,
                    content_rect.centery - self.icon.get_height() // 2,
                ),
            )
            return
        
        
        spacing = 4
        total_height = self.icon.get_height() + spacing + text_surf.get_height()
        top = content_rect.centery - total_height // 2

        surf.blit(
            self.icon,
            (
                content_rect.centerx - self.icon.get_width() // 2,
                top,
            ),
        )

        surf.blit(
            text_surf,
            (
                content_rect.centerx - text_surf.get_width() // 2,
                top + self.icon.get_height() + spacing,
            ),
        )