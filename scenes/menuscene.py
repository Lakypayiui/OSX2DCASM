import sys
import random
import pygame

from core import config

from widgets.button import Button
from widgets.inputbox import InputBox

class MenuScene:
    """Main menu scene with animated background and grid size input."""

    def __init__(self, screen: pygame.Surface) -> None:
        """Initializes the menu scene.

        Args:
            screen: Pygame display surface.
        """

        self.screen: pygame.Surface = screen
        self.width, self.height = self.screen.get_size()
        self.clock: pygame.time.Clock = pygame.time.Clock()

        # Fonts
        self.ftitle: pygame.font.Font = pygame.font.SysFont("monospace", 42, bold=True)
        self.fsub: pygame.font.Font   = pygame.font.SysFont("monospace", 18)
        self.ftext: pygame.font.Font  = pygame.font.SysFont("monospace", 16)
        self.fsmall: pygame.font.Font = pygame.font.SysFont("monospace", 14)

        # Inputs
        center_x: int = self.width // 2

        self.input_width: InputBox = InputBox(
            (center_x - 110, 270, 220, 42),
            "100",
            numeric_only=True
        )

        self.input_height: InputBox = InputBox(
            (center_x - 110, 340, 220, 42),
            "100",
            numeric_only=True
        )

        # Botones
        self.btn_create: Button = Button(
            (center_x - 110, 430, 220, 40),
            "Create Space",
            toggle=False,
            bg=(45, 120, 60),
            bg_on=(60, 160, 80)
        )

        self.btn_settings: Button = Button(
            (self.width- 140, self.height- 60, 110, 32),
            "Settings",
            toggle=False,
            bg=(55, 55, 70),
            bg_on=(80, 80, 100)
        )

        # Dummy popup
        self.show_settings: bool = False

        # Animated background
        self.bg_cells: list[dict] = []

        for _ in range(140):
            self.bg_cells.append({
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "size": random.randint(2, 6),
                "speed": random.uniform(0.1, 0.5),
                "alpha": random.randint(40, 120)
            })

        # Result
        self.start_requested: bool = False
        self.grid_width: int = 100
        self.grid_height: int = 100

    def run(self) -> tuple[int, int]:
        """Runs the menu loop until the user starts a new simulation.

        Returns:
            A tuple of (width, height) for the new grid.
        """

        while not self.start_requested:

            self.clock.tick(60)

            self.events()
            self.update()
            self.draw()

        return self.grid_width, self.grid_height

    def events(self) -> None:
        """Processes pygame events for the menu."""

        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            if ev.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode(
                    (ev.w, ev.h),
                    pygame.RESIZABLE
                )
                self._on_resize(ev.w, ev.h)

            elif ev.type == pygame.WINDOWSIZECHANGED:
                self._on_resize(*self.screen.get_size())

            self.input_width.handle_event(ev)
            self.input_height.handle_event(ev)

            if self.btn_create.handle_event(ev):

                self.grid_width = self.input_width.value()
                self.grid_height = self.input_height.value()

                self.start_requested = True

            if self.btn_settings.handle_event(ev):
                self.show_settings = not self.show_settings

    def update(self) -> None:
        """Updates the animated background cells."""

        for c in self.bg_cells:

            c["y"] += c["speed"]

            if c["y"] > self.height:
                c["y"] = -10
                c["x"] = random.randint(0, self.width)

    def draw(self) -> None:
        """Draws the complete menu screen."""

        self.screen.fill((8, 8, 12))

        self._draw_background()
        self._draw_panel()

        if self.show_settings:
            self._draw_settings_popup()

        pygame.display.flip()

    def _on_resize(self, width: int, height: int) -> None:
        """Repositions widgets after the window size changes."""

        self.width = width
        self.height = height

        center_x = width // 2

        self.input_width.rect.topleft = (center_x - 110, 270)
        self.input_height.rect.topleft = (center_x - 110, 340)

        self.btn_create.rect.topleft = (center_x - 110, 430)

        self.btn_settings.rect.topleft = (
            width - 140,
            height - 60
        )

    def _draw_background(self) -> None:
        """Draws the animated background grid and floating cells."""

        # Subtle grid
        grid_color: tuple[int, int, int] = (18, 18, 26)

        spacing: int = 40


        for x in range(0, self.width, spacing):
            pygame.draw.line(
                self.screen,
                grid_color,
                (x, 0),
                (x, self.height)
            )

        for y in range(0, self.height, spacing):
            pygame.draw.line(
                self.screen,
                grid_color,
                (0, y),
                (self.width, y)
            )

        # Animated cells
        for c in self.bg_cells:

            s: pygame.Surface = pygame.Surface((c["size"], c["size"]), pygame.SRCALPHA)

            s.fill((90, 180, 255, c["alpha"]))

            self.screen.blit(s, (c["x"], c["y"]))

    def _draw_panel(self) -> None:
        """Draws the main menu panel with title, inputs, and buttons."""

        panel: pygame.Rect = pygame.Rect(
            self.width // 2 - 220,
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
        title: pygame.Surface = self.ftitle.render(
            "ACOSXM Studio",
            True,
            (230, 230, 240)
        )

        self.screen.blit(
            title,
            (
                self.width // 2 - title.get_width() // 2,
                150
            )
        )

        # Subtitle
        sub: pygame.Surface = self.fsub.render(
            "Cellular Automata Evolution Sandbox",
            True,
            (140, 140, 170)
        )

        self.screen.blit(
            sub,
            (
                self.width // 2 - sub.get_width() // 2,
                205
            )
        )

        # Labels
        wtxt: pygame.Surface = self.ftext.render(
            "Width",
            True,
            (210, 210, 220)
        )

        htxt: pygame.Surface = self.ftext.render(
            "Height",
            True,
            (210, 210, 220)
        )

        self.screen.blit(wtxt, (self.width // 2 - 110, 245))
        self.screen.blit(htxt, (self.width // 2 - 110, 315))

        # Inputs
        self.input_width.draw(self.screen, self.ftext)
        self.input_height.draw(self.screen, self.ftext)

        # Buttons
        self.btn_create.draw(self.screen, self.ftext)
        self.btn_settings.draw(self.screen, self.fsmall)

    def _draw_settings_popup(self) -> None:
        """Draws the settings popup (placeholder)."""

        overlay: pygame.Surface = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )

        overlay.fill((0, 0, 0, 120))

        self.screen.blit(overlay, (0, 0))

        popup: pygame.Rect = pygame.Rect(
            self.width // 2 - 180,
            self.height // 2 - 120,
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

        title: pygame.Surface = self.fsub.render(
            "Settings",
            True,
            (230, 230, 240)
        )

        txt: pygame.Surface = self.ftext.render(
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
