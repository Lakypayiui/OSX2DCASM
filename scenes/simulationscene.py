import random
import sys
import numpy as np
import pygame
import os
from multiprocessing import Process, set_start_method

from controllers.camera_controller import CameraController
from controllers.simulation_controller import SimulationController
from core import config
from core.life2dm import Life2DM
from core.rule_matrix import RuleMatrix
from core.kernel import Kernel

from ui.panels import SimulationPanel

from controllers.popup_controller import PopupController, PopupResultType

main_pid: int = int(os.environ.get('MAIN_PID', 0))
if main_pid == 0 or os.getpid() == main_pid:
    print("SimulationScene loaded PID =", os.getpid())
else:
    print(f"[Child Process] SimulationScene loaded PID = {os.getpid()} (secondary)") 

class SimulationScene:
    """Main simulation scene managing the automaton, UI, and controllers."""

    def __init__(
        self,
        screen: pygame.Surface,
        width: int,
        height: int,
        bg_cells,
    ) -> None:
        """Initializes the simulation scene.

        Args:
            screen: Pygame display surface.
            width: Grid width in cells.
            height: Grid height in cells.
        """

        print("SimulationScene loaded PID =", os.getpid())

        self.screen: pygame.Surface = screen
        self.width, self.height = self.screen.get_size()

        # World
        self.grid_width: int = width
        self.grid_height: int = height

        # State
        self.running: bool = True
        self.theme: dict[str, tuple[int, int, int]] = {
            "bg": (8, 8, 12),
            "grid": (18, 18, 26),
            "cell": (90, 255, 255),
        }

        # Automaton
        self.rule_matrix: RuleMatrix = RuleMatrix()

        self.life: Life2DM = Life2DM(width, height)

        self.kernel: Kernel = Kernel()
        self.fonts: dict[str, pygame.font.Font] = {
            "normal": pygame.font.SysFont("monospace", 14),
            "medium": pygame.font.SysFont("monospace", 14),
            "bold": pygame.font.SysFont("monospace", 14, bold=True),
            "small": pygame.font.SysFont("monospace", 14)
        }
        self.panel: SimulationPanel = SimulationPanel(
            self.rule_matrix, 
            self.kernel, 
            self.life,
            self.theme, 
            self.fonts, 
            int(self.width * 0.4), 
            self.height
        )

        self._all_btns: list = self.panel.buttons

        # Popups
        self.popup_controller: PopupController = PopupController(
            self.screen,
            self.rule_matrix,
            self.life
        )

        self.camera: CameraController = CameraController()

        self.simulation_controller: SimulationController = SimulationController(
            self.screen,
            self.panel,
            self.popup_controller,
            self.camera,
            self.life,
            self.rule_matrix,
            self.kernel,
            self.grid_width,
            self.grid_height
        )

        self.bg_cells = bg_cells
        self.automaton_layer = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)

    def run(self) -> bool:
        """Runs the main simulation loop."""

        while self.running:

            if self.events():
                self.running = False

            self.life.tick()

            self.panel.graph_population.set_dirty()
            self.panel.graph_global_entropy.set_dirty()
            self.panel.graph_block_entropy.set_dirty()

            self.update()
            self.draw()
        return self.bg_cells

    def events(self) -> bool:
        """Processes pygame events for the simulation."""

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
                self.panel._on_resize(ev.h)

            elif ev.type == pygame.WINDOWSIZECHANGED:
                width, heigth = self.screen.get_size()
                self.panel._on_resize(heigth)

            if self.simulation_controller.handle_event(ev):
                return True
               
    def update(self) -> None:
        """Updates the animated background cells."""

        for c in self.bg_cells:

            c["y"] += c["speed"]

            if c["y"] > self.height:
                c["y"] = -10
                c["x"] = random.randint(0, self.width)

    def draw(self) -> None:
        """Draws the complete simulation screen."""
        self.theme["bg"] = self.panel.bg_color_selectors[0].get_color()
        self.theme["grid"] = self.panel.bg_color_selectors[1].get_color()
        self.theme["cell"] = self.panel.bg_color_selectors[2].get_color()

        self.screen.fill((10, 10, 12))

        for c in self.bg_cells:

            s: pygame.Surface = pygame.Surface((c["size"], c["size"]), pygame.SRCALPHA)

            s.fill((90, 180, 255, c["alpha"]))

            self.screen.blit(s, (c["x"], c["y"]))

        self.automaton_layer.fill((0, 0, 0, 0))

        self.life.draw(
            self.automaton_layer,
            self.theme,
            self.camera.scroll_x,
            self.camera.scroll_y
        )

        self.screen.blit(self.automaton_layer, (0, 0))

        self.panel.draw(self.screen)

        self.popup_controller.draw()
        

        pygame.display.flip()

    
