import pygame
from typing import Optional

from core.config import *

from widgets.interactive_widget import InteractiveWidget


class Button(InteractiveWidget):
    """A clickable UI button with optional toggle behavior."""

    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        toggle: bool = False,
        bg: tuple[int, int, int] = BTN_OFF_BG,
        fg: tuple[int, int, int] = BTN_OFF_FG,
        bg_on: tuple[int, int, int] = (170, 55, 55),
        fg_on: tuple[int, int, int] = (240, 240, 240),
    ) -> None:
        """Initializes the button.

        Args:
            rect: Position and size as (x, y, width, height).
            label: Button text.
            toggle: If True, the button stays pressed after clicking.
            bg: Background color when not active.
            fg: Foreground (text) color when not active.
            bg_on: Background color when active.
            fg_on: Foreground color when active.
        """
        self.rect: pygame.Rect   = pygame.Rect(rect)
        self.label: str  = label
        self.toggle: bool = toggle
        self.active: bool = False
        self.bg: tuple[int, int, int]     = bg
        self.fg: tuple[int, int, int]    = fg
        self.bg_on: tuple[int, int, int]  = bg_on
        self.fg_on: tuple[int, int, int] = fg_on
        self.click_sound: pygame.mixer.Sound = pygame.mixer.Sound("assets/sounds/click_button.wav")
        self.click_sound.set_volume(0.5)
        self._hov: bool   = False

    def handle_event(self, ev: pygame.event.Event) -> bool:
        """Processes a pygame event for the button.

        Args:
            ev: Pygame event to process.

        Returns:
            ``True`` if the button was clicked, ``False`` otherwise.
        """
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

    def draw(
        self,
        surf: pygame.Surface,
        font: pygame.font.Font,
    ) -> None:
        """Draws the button onto a surface.

        Args:
            surf: Target surface to draw on.
            font: Font used to render the label text.
        """
        if self.toggle and self.active:
            bg, fg = self.bg_on, self.fg_on
        elif self._hov:
            bg, fg = BTN_HOV, P_FG
        else:
            bg, fg = self.bg, self.fg
        pygame.draw.rect(surf, bg, self.rect, border_radius=4)
        pygame.draw.rect(surf, P_BORDER, self.rect, 1, border_radius=4)
        t: pygame.Surface = font.render(self.label, True, fg)
        surf.blit(t, (self.rect.centerx - t.get_width()  // 2,
                      self.rect.centery - t.get_height() // 2))
