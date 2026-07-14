import sys
import random
import pygame

import config

from widgets.button import Button
from widgets.inputbox import InputBox

class MenuScene:

    def __init__(self, screen):

        self.screen = screen
        self.clock = pygame.time.Clock()

        # Fonts
        self.ftitle = pygame.font.SysFont("monospace", 42, bold=True)
        self.fsub   = pygame.font.SysFont("monospace", 18)
        self.ftext  = pygame.font.SysFont("monospace", 16)
        self.fsmall = pygame.font.SysFont("monospace", 14)

        # Inputs
        center_x = config.WIN_W // 2

        self.input_width = InputBox(
            (center_x - 110, 270, 220, 42),
            "100",
            numeric_only=True
        )

        self.input_height = InputBox(
            (center_x - 110, 340, 220, 42),
            "100",
            numeric_only=True
        )

        # Botones
        self.btn_create = Button(
            (center_x - 110, 430, 220, 40),
            "Create Space",
            toggle=False,
            bg=(45, 120, 60),
            bg_on=(60, 160, 80)
        )

        self.btn_settings = Button(
            (config.WIN_W - 140, config.WIN_H - 60, 110, 32),
            "Settings",
            toggle=False,
            bg=(55, 55, 70),
            bg_on=(80, 80, 100)
        )

        # Dummy popup
        self.show_settings = False

        # Animated background
        self.bg_cells = []

        for _ in range(140):
            self.bg_cells.append({
                "x": random.randint(0, config.WIN_W),
                "y": random.randint(0, config.WIN_H),
                "size": random.randint(2, 6),
                "speed": random.uniform(0.1, 0.5),
                "alpha": random.randint(40, 120)
            })

        # Result
        self.start_requested = False
        self.grid_width = 100
        self.grid_height = 100

    def run(self):

        while not self.start_requested:

            self.clock.tick(60)

            self.events()
            self.update()
            self.draw()

        return self.grid_width, self.grid_height

    def events(self):

        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            self.input_width.handle_event(ev)
            self.input_height.handle_event(ev)

            if self.btn_create.handle_event(ev):

                self.grid_width = self.input_width.value()
                self.grid_height = self.input_height.value()

                self.start_requested = True

            if self.btn_settings.handle_event(ev):
                self.show_settings = not self.show_settings

    def update(self):

        for c in self.bg_cells:

            c["y"] += c["speed"]

            if c["y"] > config.WIN_H:
                c["y"] = -10
                c["x"] = random.randint(0, config.WIN_W)

    def draw(self):

        self.screen.fill((8, 8, 12))

        self._draw_background()
        self._draw_panel()

        if self.show_settings:
            self._draw_settings_popup()

        pygame.display.flip()

    def _draw_background(self):

        # Subtle grid
        grid_color = (18, 18, 26)

        spacing = 40

        for x in range(0, config.WIN_W, spacing):
            pygame.draw.line(
                self.screen,
                grid_color,
                (x, 0),
                (x, config.WIN_H)
            )

        for y in range(0, config.WIN_H, spacing):
            pygame.draw.line(
                self.screen,
                grid_color,
                (0, y),
                (config.WIN_W, y)
            )

        # Animated cells
        for c in self.bg_cells:

            s = pygame.Surface((c["size"], c["size"]), pygame.SRCALPHA)

            s.fill((90, 180, 255, c["alpha"]))

            self.screen.blit(s, (c["x"], c["y"]))

    def _draw_panel(self):

        panel = pygame.Rect(
            config.WIN_W // 2 - 220,
            120,
            440,
            420
        )

        # Panel background
        pygame.draw.rect(
            self.screen,
            (18, 18, 26),
            panel,
            border_radius=12
        )

        pygame.draw.rect(
            self.screen,
            (60, 60, 80),
            panel,
            width=2,
            border_radius=12
        )

        # Title
        title = self.ftitle.render(
            "ACOSXM Studio",
            True,
            (230, 230, 240)
        )

        self.screen.blit(
            title,
            (
                config.WIN_W // 2 - title.get_width() // 2,
                150
            )
        )

        # Subtitle
        sub = self.fsub.render(
            "Cellular Automata Evolution Sandbox",
            True,
            (140, 140, 170)
        )

        self.screen.blit(
            sub,
            (
                config.WIN_W // 2 - sub.get_width() // 2,
                205
            )
        )

        # Labels
        wtxt = self.ftext.render(
            "Width",
            True,
            (210, 210, 220)
        )

        htxt = self.ftext.render(
            "Height",
            True,
            (210, 210, 220)
        )

        self.screen.blit(wtxt, (config.WIN_W // 2 - 110, 245))
        self.screen.blit(htxt, (config.WIN_W // 2 - 110, 315))

        # Inputs
        self.input_width.draw(self.screen, self.ftext)
        self.input_height.draw(self.screen, self.ftext)

        # Buttons
        self.btn_create.draw(self.screen, self.ftext)
        self.btn_settings.draw(self.screen, self.fsmall)

    def _draw_settings_popup(self):

        overlay = pygame.Surface(
            (config.WIN_W, config.WIN_H),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 120))

        self.screen.blit(overlay, (0, 0))

        popup = pygame.Rect(
            config.WIN_W // 2 - 180,
            config.WIN_H // 2 - 120,
            360,
            240
        )

        pygame.draw.rect(
            self.screen,
            (22, 22, 30),
            popup,
            border_radius=12
        )

        pygame.draw.rect(
            self.screen,
            (80, 80, 100),
            popup,
            width=2,
            border_radius=12
        )

        title = self.fsub.render(
            "Settings",
            True,
            (230, 230, 240)
        )

        txt = self.ftext.render(
            "Coming soon...",
            True,
            (180, 180, 190)
        )

        self.screen.blit(
            title,
            (
                popup.centerx - title.get_width() // 2,
                popup.y + 35
            )
        )

        self.screen.blit(
            txt,
            (
                popup.centerx - txt.get_width() // 2,
                popup.y + 110
            )
        )