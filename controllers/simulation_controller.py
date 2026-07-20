import pygame
from controllers.camera_controller import CameraController
from controllers.popup_controller import PopupController, PopupResultType
from core import config
from core.life2dm import Life2DM
from ui.panels.simulation_panel import SimulationPanel


class SimulationController:

    def __init__(
        self,
        screen,
        panel: SimulationPanel,
        popup_controller: PopupController,
        camera: CameraController,
        life: Life2DM,
        rule_matrix,
        kernel,
        grid_width,
        grid_height,
    ):
        self.screen = screen
        self.panel = panel
        self.popup_controller = popup_controller
        self.camera = camera
        self.life = life
        self.rule_matrix = rule_matrix
        self.kernel = kernel
        self.grid_width = grid_width
        self.grid_height = grid_height

        self.cur_cx = 0
        self.cur_cy = 0
        
    
    def handle_event(self, event):

        self._handle_mouse(event)

        self._handle_panel(event)

        self._handle_popups(event)


    def _handle_mouse(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            self._paint_cell(event.pos)

        if event.type == pygame.MOUSEMOTION and event.buttons[0]:

            self._paint_cell(event.pos)


        self.camera.handle_event(
                event,
                panel_visible=self.panel.visible,
                popup_open=self.popup_controller.has_popup,
        )

        # Kernel
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            self.panel.kernel_panel.handle_click(event.pos)

        # Rule matrix
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            res = self.panel.rule_panel.handle_click(event.pos)

            if res is not None:

                self.life.sync_rule_from_matrix(
                    self.rule_matrix.data
                )

                self.kernel.set_mask(res)

    def _paint_cell(self, pos):

        if self.popup_controller.current_popup:
            return

        mx, my = pos

        w_limit, h_limit = self.screen.get_size()

        total_w_px = self.grid_width * config.CELL_PX
        total_h_px = self.grid_height * config.CELL_PX

        global_off_x = (w_limit - total_w_px) // 2
        global_off_y = (h_limit - total_h_px) // 2

        start_px_x = global_off_x - (self.camera.scroll_x * config.CELL_PX)
        start_px_y = global_off_y - (self.camera.scroll_y * config.CELL_PX)

        if self.panel.visible:

            if mx < config.PANEL_W:
                return

        cx = (mx - start_px_x) // config.CELL_PX
        cy = (my - start_px_y) // config.CELL_PX

        if (cx, cy) != (self.cur_cx, self.cur_cy):

            if 0 <= cx < self.grid_width and 0 <= cy < self.grid_height:

                self.life.toggle_cell(cx, cy)

                self.cur_cx = cx
                self.cur_cy = cy

    def _handle_panel(self, event):
        # Slider
        self.panel.slider_density.handle_event(event)
        self.panel.slider_rule_density.handle_event(event)
        # Color selectors
        for s in self.panel.bg_color_selectors:
            s.handle_event(event)

        pass

    def _handle_popups(self, event):
        popup_result = self.popup_controller.handle_event(event)

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