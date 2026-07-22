import os
from typing import Dict, List, Optional

import pygame

from scenes.display3dscene import Display3DScene, PLATFORM
from core import config
from core.life2dm import Life2DM

from .camera_controller import CameraController
from .popup_controller import PopupController, PopupResultType

from ui.panels.simulation_panel import SimulationPanel

def open_gl_window(history: list) -> None:
    """Launches a separate 3D OpenGL window for viewing simulation history.

    Args:
        history: List of automaton state arrays representing the evolution.
    """
    os.environ['MAIN_PID'] = str(os.getpid())  # force this to be considered main for 3D
    print("open_gl_window PID =", os.getpid())
    
    renderer = Display3DScene(history)
    if PLATFORM == "Darwin":
        renderer.macos_3d_render()
    else:
        renderer.open_gl_render()

class SimulationController:
    """Orchestrates mouse input, painting, and popup handling for the simulation."""

    def __init__(
        self,
        screen: pygame.Surface,
        panel: SimulationPanel,
        popup_controller: PopupController,
        camera: CameraController,
        life: Life2DM,
        rule_matrix,
        kernel,
        grid_width: int,
        grid_height: int,
    ) -> None:
        """Initializes the simulation controller.

        Args:
            screen: Main display surface.
            panel: Simulation panel with sliders and buttons.
            popup_controller: Controller for popup dialogs.
            camera: Camera controller for viewport manipulation.
            life: Cellular automaton instance.
            rule_matrix: Rule matrix instance.
            kernel: Moore neighborhood kernel instance.
            grid_width: Number of grid columns.
            grid_height: Number of grid rows.
        """
        self.screen: pygame.Surface = screen
        self.panel: SimulationPanel = panel
        self.popup_controller: PopupController = popup_controller
        self.camera: CameraController = camera
        self.life: Life2DM = life
        self.rule_matrix = rule_matrix
        self.kernel = kernel
        self.grid_width: int = grid_width
        self.grid_height: int = grid_height

        self.cur_cx: int = 0
        self.cur_cy: int = 0
        
    
    def handle_event(self, event: pygame.event.Event) -> None:
        """Dispatches a pygame event to the appropriate handler.

        Args:
            event: Pygame event to process.
        """

        self._handle_mouse(event)

        self._handle_popups(event)

        self._handle_panel(event)


    def _handle_mouse(self, event: pygame.event.Event) -> None:
        """Processes mouse events for painting, camera control, and UI clicks.

        Args:
            event: Pygame event to process.
        """

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            self._paint_cell(event.pos)

        if event.type == pygame.MOUSEMOTION and event.buttons[0]:

            self._paint_cell(event.pos)


        self.camera.handle_event(
                event,
                panel_visible=self.panel.visible,
                popup_open=self.popup_controller.has_popup,
                panel_width=self.panel.width
        )

    def _paint_cell(self, pos: tuple[int, int]) -> None:
        """Toggles a cell under the given screen position.

        Args:
            pos: Mouse position in screen coordinates.
        """

        if self.popup_controller.current_popup:
            return

        mx, my = pos

        w_limit, h_limit = self.screen.get_size()

        total_w_px: int = self.grid_width * config.CELL_PX
        total_h_px: int = self.grid_height * config.CELL_PX

        global_off_x: int = (w_limit - total_w_px) // 2
        global_off_y: int = (h_limit - total_h_px) // 2

        start_px_x: int = global_off_x - (self.camera.scroll_x * config.CELL_PX)
        start_px_y: int = global_off_y - (self.camera.scroll_y * config.CELL_PX)

        if self.panel.visible:

            if mx < self.panel.width:
                return

        cx: int = (mx - start_px_x) // config.CELL_PX
        cy: int = (my - start_px_y) // config.CELL_PX

        if (cx, cy) != (self.cur_cx, self.cur_cy):

            if 0 <= cx < self.grid_width and 0 <= cy < self.grid_height:

                self.life.toggle_cell(cx, cy)

                self.cur_cx = cx
                self.cur_cy = cy

    def _handle_panel(self, event: pygame.event.Event) -> None:
        """Processes events for sliders and color selectors.

        Args:
            event: Pygame event to process.
        """
        # Slider
        if event.type == pygame.MOUSEWHEEL:
            if pygame.mouse.get_pos()[0]< self.panel.width:
                self.panel.scroll_y -= event.y * 30  
                self.panel._clamp_scroll()

        self._handle_panel_toggle(event)

        if self.panel.visible:
            
            if event.type == pygame.MOUSEMOTION or event.type == pygame.MOUSEBUTTONDOWN:
                event.pos = (event.pos[0], event.pos[1] + self.panel.scroll_y)

            # Accordions
            self.panel.color_accordion.handle_event(event)

            # Kernel
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                self.panel.kernel_panel.handle_click(event.pos)

            # Rule matrix
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

                res: Optional[int] = self.panel.rule_panel.handle_click(event.pos)

                if res is not None:

                    self.life.sync_rule_from_matrix(
                        self.rule_matrix.data
                    )

                    self.kernel.set_mask(res)

            self.panel.slider_density.handle_event(event)
            self.panel.slider_rule_density.handle_event(event)

            # Color selectors
            for s in self.panel.bg_color_selectors:
                s.handle_event(event)

            # Buttons
            for b in self.panel.buttons:

                if b.handle_event(event):

                    self._on_btn(b)
            
            # Graphs

            self.panel.graph_population.handle_event(event)
            self.panel.graph_global_entropy.handle_event(event)
    
    def _handle_panel_toggle(self, event: pygame.event.Event) -> None:
        """Handles toggling the side panel visibility.

        If the hide/show button is pressed, the panel visibility is toggled and
        the button label and position are updated accordingly.

        Args:
            event: The pygame event to process.

        Returns:
            None.
        """

        if not self.panel.btn_hide_panel.handle_event(event):
            return

        self.panel.visible = not self.panel.visible

        if self.panel.visible:
            self.panel.btn_hide_panel.label = "<<"
            self.panel.btn_hide_panel.rect.x = (
                self.panel.width - config.PAD - 40
            )
        else:
            self.panel.btn_hide_panel.label = ">>"
            self.panel.btn_hide_panel.rect.x = config.PAD

    def _on_btn(self, b) -> None:
        """Handles a button click from the simulation panel.

        Args:
            b: The button that was clicked.
        """

        if b is self.panel.btn_random_config:
            self.life.random_fill(self.panel.slider_density.value)

        elif b is self.panel.btn_random_rule:
            self.rule_matrix.randomize(self.panel.slider_rule_density.value)

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


    def _handle_popups(self, event: pygame.event.Event) -> None:
        """Processes events for popup dialogs and their results.

        Args:
            event: Pygame event to process.
        """
        popup_result: Optional[object] = self.popup_controller.handle_event(event)

        if popup_result is not None:
            if popup_result.data != "closed":
                if popup_result.type is PopupResultType.LOAD_RULE:
                    self.rule_matrix.set_from_rule_array(
                        popup_result.data["rule"]
                    )
                    self.life.sync_rule_from_matrix(
                        self.rule_matrix.data
                    )
                    self.popup_controller.pop()
                if popup_result.type is PopupResultType.LOAD_SIMULATION:
                    self.life.state = popup_result.data["state"]
                    self.life.rule = popup_result.data["rule"]
                    self.life.gen = popup_result.data["generation"]
                    self.rule_matrix.set_from_rule_array(
                        popup_result.data["rule"]
                    )
                    self.popup_controller.pop()
                
                if popup_result.type is PopupResultType.SAVE_RULE:
                    if popup_result.data == "exists":
                        self.popup_controller.confirm.object_type = "Rule"
                        self.popup_controller.confirm.file_name = self.popup_controller.save_rule.input_name.text
                        self.popup_controller.push(self.popup_controller.confirm)
                    elif popup_result.data == "saved":
                        self.popup_controller.load_rule.load_presets()
                        self.popup_controller.pop()
                if popup_result.type is PopupResultType.SAVE_SIMULATION:
                    if popup_result.data == "exists":
                        self.popup_controller.confirm.object_type = "File"
                        self.popup_controller.confirm.file_name = self.popup_controller.save_state.input_name.text.strip() + ".txt"
                        self.popup_controller.push(self.popup_controller.confirm)
                    elif popup_result.data == "saved":
                        self.popup_controller.load_state.load_simulations()
                        self.popup_controller.pop()
                if popup_result.type is PopupResultType.CONFIRM_OVERWRITE:
                    if popup_result.data is True:
                        if self.popup_controller.confirm.object_type == "Rule":
                            self.popup_controller.save_rule.save_rule(
                                overwrite=True
                            )
                        else:
                            self.popup_controller.save_state.save_simulation(
                                overwrite=True
                            )
                        self.popup_controller.pop()
                    self.popup_controller.pop()
            else:
                self.popup_controller.pop()

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