from __future__ import annotations

import sys, random
import pygame

from core import config
from ui.dialogs.settings_popup import SettingsPopup, load_settings
from widgets.button import Button
from widgets.inputbox import InputBox


class MenuScene:
    """Main menu scene with animated background and grid size input."""

    def __init__(self, screen: pygame.Surface, width: int, height: int,
                 bg_cells: list[dict] | None = None) -> None:
        self.screen = screen
        self.width, self.height = self.screen.get_size()
        self.clock = pygame.time.Clock()

        self.ftitle = pygame.font.SysFont("monospace", 42, bold=True)
        self.fsub   = pygame.font.SysFont("monospace", 18)
        self.ftext  = pygame.font.SysFont("monospace", 16)
        self.fsmall = pygame.font.SysFont("monospace", 14)

        cx = self.width // 2

        self.input_width = InputBox(
            (cx - 110, 270, 220, 42), self.ftext, f"{width}", numeric_only=True)
        self.input_height = InputBox(
            (cx - 110, 340, 220, 42), self.ftext, f"{height}", numeric_only=True)

        self.btn_create = Button(
            (cx - 110, 430, 220, 40), "Create Space", self.ftext,
            toggle=False, bg=(45, 120, 60), bg_on=(60, 160, 80), bg_hov=(65, 150, 80))
        self.btn_settings = Button(
            (self.width - 140, self.height - 60, 110, 32), "Settings", self.fsmall,
            toggle=False, bg=(55, 55, 70), bg_on=(80, 80, 100))

        self._settings = load_settings()
        self.show_settings = False
        self._settings_popup: SettingsPopup | None = None

        if bg_cells:
            self.bg_cells = bg_cells
        else:
            self.bg_cells = []
            for _ in range(140):
                self.bg_cells.append({
                    "x": random.randint(0, self.width),
                    "y": random.randint(0, self.height),
                    "size": random.randint(2, 6),
                    "speed": random.uniform(0.1, 0.5),
                    "alpha": random.randint(40, 120),
                })

        self.start_requested = False
        self.grid_width, self.grid_height = 100, 100

    # ------------------------------------------------------------------
    # Loop
    # ------------------------------------------------------------------

    def run(self) -> tuple[int, int, list[dict]]:
        while not self.start_requested:
            self.clock.tick(60)
            self._events()
            self._update()
            self._draw()
        return self.grid_width, self.grid_height, self.bg_cells

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def _events(self) -> None:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()
            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((ev.w, ev.h), pygame.RESIZABLE)
                self._on_resize(ev.w, ev.h)
            elif ev.type == pygame.WINDOWSIZECHANGED:
                self._on_resize(*self.screen.get_size())

            if self._settings_popup is not None and self._settings_popup.visible:
                self._settings_popup.handle_events(ev)
                continue

            self.input_width.handle_event(ev)
            self.input_height.handle_event(ev)

            if self.btn_create.handle_event(ev):
                self.grid_width = self.input_width.value()
                self.grid_height = self.input_height.value()
                self.start_requested = True

            if self.btn_settings.handle_event(ev):
                self._open_settings()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def _update(self) -> None:
        if not self._settings["bg_animation"]:
            return
        for c in self.bg_cells:
            c["y"] += c["speed"]
            if c["y"] > self.height:
                c["y"] = -10
                c["x"] = random.randint(0, self.width)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self.screen.fill((8, 8, 12))
        self._draw_background()
        self._draw_panel()
        if self._settings_popup is not None and self._settings_popup.visible:
            self._settings_popup.draw(self.screen)
        pygame.display.flip()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _open_settings(self) -> None:
        self._settings_popup = SettingsPopup(
            (self.width // 2 - 200, self.height // 2 - 155, 400, 310),
            on_close=self._on_settings_close,
        )
        self._settings_popup.visible = True

    def _on_settings_close(self) -> None:
        self._settings = load_settings()

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def _on_resize(self, width: int, height: int) -> None:
        self.width, self.height = width, height
        cx = width // 2
        self.input_width.rect.topleft = (cx - 110, 270)
        self.input_height.rect.topleft = (cx - 110, 340)
        self.btn_create.rect.topleft = (cx - 110, 430)
        self.btn_settings.rect.topleft = (width - 140, height - 60)

    # ------------------------------------------------------------------
    # Background
    # ------------------------------------------------------------------

    def _draw_background(self) -> None:
        gc = (18, 18, 26)
        for x in range(0, self.width, 40):
            pygame.draw.line(self.screen, gc, (x, 0), (x, self.height))
        for y in range(0, self.height, 40):
            pygame.draw.line(self.screen, gc, (0, y), (self.width, y))

        if not self._settings["bg_animation"]:
            return

        for c in self.bg_cells:
            s = pygame.Surface((c["size"], c["size"]), pygame.SRCALPHA)
            s.fill((90, 180, 255, c["alpha"]))
            self.screen.blit(s, (c["x"], c["y"]))

    # ------------------------------------------------------------------
    # Panel
    # ------------------------------------------------------------------

    def _draw_panel(self) -> None:
        panel = pygame.Rect(self.width // 2 - 220, 120, 440, 420)
        pygame.draw.rect(self.screen, (18, 18, 26), panel, border_radius=12)
        pygame.draw.rect(self.screen, (60, 60, 80), panel, 2, border_radius=12)

        title = self.ftitle.render("ACOSXM Studio", True, (230, 230, 240))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 150))

        sub = self.fsub.render("Cellular Automata Evolution Sandbox", True, (140, 140, 170))
        self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, 205))

        wtxt = self.ftext.render("Width", True, (210, 210, 220))
        htxt = self.ftext.render("Height", True, (210, 210, 220))
        self.screen.blit(wtxt, (self.width // 2 - 110, 245))
        self.screen.blit(htxt, (self.width // 2 - 110, 315))

        self.input_width.draw(self.screen)
        self.input_height.draw(self.screen)
        self.btn_create.draw(self.screen)
        self.btn_settings.draw(self.screen)
