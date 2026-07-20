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
from core.display3d import Display3D, PLATFORM

from ui.panels import SimulationPanel

from controllers.popup_controller import PopupController, PopupResultType

main_pid: int = int(os.environ.get('MAIN_PID', 0))
if main_pid == 0 or os.getpid() == main_pid:
    print("SimulationScene loaded PID =", os.getpid())
else:
    print(f"[Child Process] SimulationScene loaded PID = {os.getpid()} (secondary)")
    
def open_gl_window(history: list) -> None:
    """Launches a separate 3D OpenGL window for viewing simulation history.

    Args:
        history: List of automaton state arrays representing the evolution.
    """
    os.environ['MAIN_PID'] = str(os.getpid())  # force this to be considered main for 3D
    print("open_gl_window PID =", os.getpid())
    
    renderer = Display3D(history)
    if PLATFORM == "Darwin":
        renderer.macos_3d_render()
    else:
        renderer.open_gl_render()


class SimulationScene:
    """Main simulation scene managing the automaton, UI, and controllers."""

    def __init__(
        self,
        screen: pygame.Surface,
        width: int,
        height: int,
    ) -> None:
        """Initializes the simulation scene.

        Args:
            screen: Pygame display surface.
            width: Grid width in cells.
            height: Grid height in cells.
        """

        print("SimulationScene loaded PID =", os.getpid())

        self.screen: pygame.Surface = screen

        # World
        self.grid_width: int = width
        self.grid_height: int = height

        # State
        self.running: bool = True
        self.theme: dict[str, tuple[int, int, int]] = {
            "bg": (13, 13, 13),
            "grid": (25, 40, 25),
            "cell": (0, 255, 100),
        }

        # Automaton
        self.rule_matrix: RuleMatrix = RuleMatrix()
        

        self.life: Life2DM = Life2DM(width, height)
        self.history: list = []

        self.kernel: Kernel = Kernel()
        self.fonts: dict[str, pygame.font.Font] = {
            "normal": pygame.font.SysFont("monospace", 14),
            "medium": pygame.font.SysFont("monospace", 14),
            "bold": pygame.font.SysFont("monospace", 14, bold=True),
            "small": pygame.font.SysFont("monospace", 14)
        }
        self.panel: SimulationPanel = SimulationPanel(self.rule_matrix, self.kernel, self.theme, self.fonts)

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

    def run(self) -> None:
        """Runs the main simulation loop."""

        while self.running:

            self.events()

            self.life.tick()

            self.draw()

    def events(self) -> None:
        """Processes pygame events for the simulation."""

        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:

                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()


            self.simulation_controller.handle_event(ev)
            
            # Buttons
            for b in self._all_btns:

                if b.handle_event(ev):

                    self._on_btn(b)
            

    def launch_3d_view(self) -> None:
        """Launches the 3D view in a separate process."""
        if not self.life.history:
            return

        print(f"[3D] Launching separate process - main PID = {os.getpid()}")

        from multiprocessing import Process

        p = Process(
            target=open_gl_window,
            args=(self.life.history.copy(),),   # copy para evitar problemas
            daemon=True
        )
        p.start()
        print(f"[3D] Process launched with PID = {p.pid}")
       

    def _on_btn(self, b) -> None:
        """Handles a button click from the simulation panel.

        Args:
            b: The button that was clicked.
        """

        d: float = self.panel.slider_density.value
        dr: float = self.panel.slider_rule_density.value

        if b is self.panel.btn_random_config:

            self.life.random_fill(d)

        elif b is self.panel.btn_random_rule:

            self.rule_matrix.randomize(dr)

            self.life.sync_rule_from_matrix(
                self.rule_matrix.data
            )

        elif b is self.panel.btn_step:
            self.panel.btn_pause.active = True
            self.panel.btn_evolution.active = False
            self.panel.btn_pause.label = "Resume"
            self.life.running = False
            self.life.step()

        elif b is self.panel.btn_clear_rule:

            self.rule_matrix.clear()

            self.life.rule[:] = 0

            self.kernel.clear()

        elif b is self.panel.btn_evolution:
            self.life.running = b.active
            if b.active:
                self.panel.btn_evolution.label = "Stop"
            else:
                self.panel.btn_evolution.label = "Start"
                self.panel.btn_pause.active = False
                self.panel.btn_pause.label = "Pause"
                self.life.reset()

        elif b is self.panel.btn_pause:
            self.life.running = not b.active
            if b.active:
                self.panel.btn_pause.label = "Resume"
            else:
                self.panel.btn_pause.label = "Pause"

        elif b is self.panel.btn_clear_view:
            self.panel.btn_evolution.active = False
            self.panel.btn_evolution.label = "Start"
            self.panel.btn_pause.active = False
            self.panel.btn_pause.label = "Pause"

            self.life.full_reset()

        elif b is self.panel.btn_add_kernel:

            rule: np.ndarray = self.kernel.apply_to_matrix(
                self.rule_matrix
            )

            self.life.rule = rule

        elif b is self.panel.btn_load_rule:
            self.popup_controller.push(self.popup_controller.load_rule)

        elif b is self.panel.btn_save_rule:
            self.popup_controller.save_rule.rule = self.rule_matrix.to_rule_array()
            self.popup_controller.push(self.popup_controller.save_rule)

        elif b is self.panel.btn_save:
            self.popup_controller.push(self.popup_controller.save_state)

        elif b is self.panel.btn_load:
            self.popup_controller.push(self.popup_controller.load_state)

        elif b is self.panel.btn_view_3d:
            if self.life.history:
                self.launch_3d_view()

        elif b is self.panel.btn_hide_panel:

            self.panel.visible = not self.panel.visible

            if self.panel.visible:

                self.panel.btn_hide_panel.label = "<<"

                self.panel.btn_hide_panel.rect.x = (
                    config.PANEL_W - config.PAD - 40
                )

            else:

                self.panel.btn_hide_panel.label = ">>"

                self.panel.btn_hide_panel.rect.x = config.PAD
        

    def draw(self) -> None:
        """Draws the complete simulation screen."""
        self.theme["bg"] = self.panel.bg_color_selectors[0].get_color()
        self.theme["grid"] = self.panel.bg_color_selectors[1].get_color()
        self.theme["cell"] = self.panel.bg_color_selectors[2].get_color()

        self.screen.fill((10, 10, 12))

        self.life.draw(
            self.screen,
            self.theme,
            self.camera.scroll_x,
            self.camera.scroll_y
        )

        self.panel.draw(self.screen)

        self.popup_controller.draw()
        

        pygame.display.flip()

    
