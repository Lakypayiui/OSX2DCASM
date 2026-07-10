import sys
import pygame
from multiprocessing import Process, set_start_method

import config

from life2dm import Life2DM
from matrizregla import MatrizRegla
from kernel import Kernel3x3
from display3d import Display3D, PLATFORM

from widgets.button import Button
from widgets.savesimulationpopup import SaveSimulationPopup
from widgets.slider import Slider
from widgets.rgbselector import RGBSelector
from widgets.presetpopup import PresetPopup
from widgets.saverulepopup import SaveRulePopup
from widgets.confirmoverwritepopup import ConfirmOverwritePopup
import os

main_pid = int(os.environ.get('MAIN_PID', 0))
if main_pid == 0 or os.getpid() == main_pid:
    print("SimulationScene cargado PID =", os.getpid())
else:
    print(f"[Child Process] SimulationScene cargado PID = {os.getpid()} (secundario)")
def open_gl_window(history):
    os.environ['MAIN_PID'] = str(os.getpid())  # forzar que este sea considerado principal para el 3D
    print("open_gl_window PID =", os.getpid())
    
    renderer = Display3D(history)
    if PLATFORM == "Darwin":
        renderer.macos_3d_render()
    else:
        renderer.open_gl_render()


class SimulationScene:

    def __init__(self, screen, width, height):

        self.screen = screen

        # Mundo
        self.grid_width = width
        self.grid_height = height

        # Fuentes
        self.fn  = pygame.font.SysFont("monospace", 14)
        self.fm  = pygame.font.SysFont("monospace", 14)
        self.fb  = pygame.font.SysFont("monospace", 14, bold=True)
        self.fxs = pygame.font.SysFont("monospace", 14)

        # Estado
        self.running = True
        self.show_panel = True
        self.theme = {"bg": ( 13, 13, 13), "grid": ( 25, 40, 25), "cell": (  0,255,100)}

        # Automata
        self.matriz_regla = MatrizRegla()
        self.life = Life2DM(width, height)
        self.history = []

        
        # Panel
        BW, BH, BGAP = 183, 22, 4

        y = config.PAD

        self.btn_ocultar_panel = Button(
            (config.PANEL_W - config.PAD - 40, y, 40, 20),
            "<<",
            toggle=False,
            bg=config.BTN_OFF_BG,
            bg_on=config.BTN_ON_BG
        )

        self.y_rule_hdr = y
        y += 18

        self.y_colnum = y
        y += 10

        self.y_mat = y

        MAT_X0 = config.PAD + 16

        self.mat_rects = self.matriz_regla.build_rects(MAT_X0, y)

        y += self.matriz_regla.total_h + config.PAD + 4

        self.y_sep1 = y - 4

        self.y_kern_hdr = y
        y += 14

        KERN_X = MAT_X0

        self.kernel = Kernel3x3(KERN_X, y)

        self.x_kern_info = KERN_X + self.kernel.total_w + 16
        self.y_kern_info = y

        # =========================================================
        # HELPERS
        # =========================================================

        def btn_panel(label, col, yy,
                    toggle=False,
                    bg=config.BTN_OFF_BG,
                    bg_on=(170, 55, 55)):

            return Button(
                (config.PAD + col * (BW + BGAP), yy, BW, BH),
                label,
                toggle=toggle,
                bg=bg,
                bg_on=bg_on
            )

        # =========================================================
        # RULES
        # =========================================================

        self.btn_agregar_kernel = btn_panel(
            "Add kernel",
            2,
            y
        )

        y += BH + BGAP

        self.btn_regla_aleat = btn_panel(
            "Random rule",
            2,
            y
        )

        y += BH + BGAP

        self.btn_limpiar_reg = btn_panel(
            "Clear rule",
            2,
            y
        )

        y += BH + BGAP + 4

        # Density slider
        self.y_den_rules_lbl = y
        self.x_den_rules_lbl = config.PAD + 2 * (BW + BGAP)

        y += 13

        self.slider_den_rules = Slider(
            (self.x_den_rules_lbl , y,  int(BW*1.4), 12),
            value=0.5
        )

        y += 24

        self.btn_presets = btn_panel(
            "Load preset",
            2,
            y
        )

        y += BH + BGAP

        self.btn_save_preset = btn_panel(
            "Save preset",
            2,
            y
        )

        y += config.PAD + 40

        self.y_sep2 = y

        y += config.PAD

        # =========================================================
        # POPULATION SECTION
        # =========================================================

        self.y_population_hdr = y

        y += 25

        self.btn_conf_aleat = btn_panel(
            "Random config",
            0,
            y
        )

        self.btn_limpiar_vis = btn_panel(
            "Clear view",
            1,
            y
        )

        y += BH + BGAP + 4

        # Density slider
        self.y_den_lbl = y

        y += 13

        self.slider_den = Slider(
            (config.PAD, y, config.PANEL_W - 65, 12),
            value=0.5
        )

        y += 40 + config.PAD


        # =========================================================
        # EVOLUTION SECTION
        # =========================================================

        self.y_evolution_hdr = y

        y += 25

        self.btn_evolucion = btn_panel(
            "Start",
            0,
            y,
            toggle=True,
            bg=(45, 120, 60)
        )

        self.btn_evol_paso = btn_panel(
            "Step",
            1,
            y
        )

        y += BH + BGAP

        self.btn_pause = btn_panel(
            "Pause",
            0,
            y,
            toggle=True,
        )

        self.btn_view_3d = btn_panel(
            "3D View",
            1,
            y
        )

        y += BH + BGAP

        self.btn_save = btn_panel(
            "Save",
            0,
            y
        )


        y += 40

        # Temas
        self.y_tema_lbl = y

        y += 13

        self.bg_color_selectors = []

        labels_colors = ["bg", "grid", "cell"]
        CSW = (config.PANEL_W - config.PAD) // len(labels_colors) - 2
        for idx, lc in enumerate(labels_colors):
            bx = config.PAD + idx * (CSW + 2)
            self.bg_color_selectors.append(RGBSelector(
                (bx, y, CSW, 80), initial=self.theme[lc.lower().replace(" ", "")]
            ))

        y += 17 + config.PAD

        self.y_info = y

        self._action_btns = [
            self.btn_conf_aleat,
            self.btn_regla_aleat,
            self.btn_presets,
            self.btn_save_preset,
            self.btn_evol_paso,
            self.btn_pause,
            self.btn_save,
            self.btn_view_3d,
            self.btn_limpiar_reg,
            self.btn_evolucion,
            self.btn_limpiar_vis,
            self.btn_agregar_kernel,
            self.btn_ocultar_panel
        ]

        self._all_btns = self._action_btns

        self.panel_surf = pygame.Surface(
            (config.PANEL_W, config.WIN_H)
        )

        # Popups
        self.preset_w, self.preset_h = 500, 400
        self.show_popup = False
        self.show_confirm = False

        self.preset_popup = PresetPopup(
            (
                (self.screen.get_width() - self.preset_w) // 2,
                (self.screen.get_height() - self.preset_h) // 2,
                self.preset_w,
                self.preset_h
            )
        )
        self.save_preset_popup = SaveRulePopup(
            (
                (self.screen.get_width() - self.preset_w) // 2,
                (self.screen.get_height() - self.preset_h) // 2,
                self.preset_w,
                self.preset_h,
            ),
            self.matriz_regla.to_rule_array()
        )

        self.confirm_popup = ConfirmOverwritePopup(
            (
                (self.screen.get_width() - 500) // 2,
                (self.screen.get_height() - 300) // 2,
                500,
                300
            )
        )

        self.save_state_popup = SaveSimulationPopup(
            (
                (self.screen.get_width() - 500) // 2,
                (self.screen.get_height() - 300) // 2,
                500,
                300
            )
        )

        # Camara
        self.scroll_x = 0
        self.scroll_y = 0

        self.cur_cx = 0
        self.cur_cy = 0

        self.dragging_right = False

        self.last_mouse_pos = (0, 0)

    def run(self):

        while self.running:

            self.events()

            self.life.tick()

            self.draw()

    def events(self):

        for ev in pygame.event.get():

            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if ev.type == pygame.KEYDOWN:

                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # Zoom
            if ev.type == pygame.MOUSEWHEEL:
                if not self.show_popup:
                    mx, _ = pygame.mouse.get_pos()

                    if (mx >= config.PANEL_W and self.show_panel) or not self.show_panel:

                        if ev.y > 0:
                            config.CELL_PX *= 1.6

                        elif ev.y < 0:
                            config.CELL_PX /= 1.6

                        config.CELL_PX = max(2, config.CELL_PX)
                        config.CELL_PX = int(config.CELL_PX)


            # Inicio drag
            if ev.type == pygame.MOUSEBUTTONDOWN:

                if ev.button == 3:
                    self.dragging_right = True
                    self.last_mouse_pos = pygame.mouse.get_pos()

            # Fin drag
            if ev.type == pygame.MOUSEBUTTONUP:

                if ev.button == 3:
                    self.dragging_right = False

            # Movimiento camara
            if ev.type == pygame.MOUSEMOTION and self.dragging_right:

                mx, my = pygame.mouse.get_pos()

                dx = mx - self.last_mouse_pos[0]
                dy = my - self.last_mouse_pos[1]

                self.scroll_x -= dx
                self.scroll_y -= dy

                self.last_mouse_pos = (mx, my)

            # Pintar celdas
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:

                self._paint_cell(ev.pos)

            if ev.type == pygame.MOUSEMOTION and ev.buttons[0]:

                self._paint_cell(ev.pos)

            # Slider
            self.slider_den.handle_event(ev)
            self.slider_den_rules.handle_event(ev)

            # Botones
            for b in self._all_btns:

                if b.handle_event(ev):

                    self._on_btn(b)

            # Selectores de color
            for s in self.bg_color_selectors:
                s.handle_event(ev)

            # Popup Presets
            preset = self.preset_popup.handle_event(ev)

            if preset is not None:

                self.matriz_regla.set_from_rule_array(preset["rule"])

                self.life.sync_rule_from_matrix(
                    self.matriz_regla.data
                )

            # Popup Save Preset
            if not self.show_confirm:
                save_result = self.save_preset_popup.handle_event(ev)

                if save_result == "exists":
                    self.confirm_popup.open(
                        self.save_preset_popup.input_name.text
                    )

                elif save_result == "saved":
                    self.preset_popup.load_presets()
                    print("Rule saved")


            confirm = self.confirm_popup.handle_event(ev)

            if confirm is True:

                self.save_preset_popup.save_rule(
                    overwrite=True
                )

            if self.save_preset_popup.visible or self.preset_popup.visible:
                self.show_popup = True
            else:
                self.show_popup = False

            if self.confirm_popup.visible:
                self.show_confirm = True
            else:
                self.show_confirm = False

            # Matriz regla
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:

                res = self.matriz_regla.handle_click(
                    ev.pos,
                    self.mat_rects
                )

                if res is not None:

                    self.life.sync_rule_from_matrix(
                        self.matriz_regla.data
                    )

                    self.kernel.set_kernel_mask(res)

            # Kernel
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:

                self.kernel.handle_click(ev.pos)

    def launch_3d_view(self):
        if not self.life.history:
            return

        print(f"[3D] Lanzando proceso separado - PID principal = {os.getpid()}")

        from multiprocessing import Process

        p = Process(
            target=open_gl_window,
            args=(self.life.history.copy(),),   # copy para evitar problemas
            daemon=True
        )
        p.start()
        print(f"[3D] Proceso lanzado con PID = {p.pid}")
       

    def _paint_cell(self, pos):

        if self.show_popup:
            return

        mx, my = pos

        w_limit, h_limit = self.screen.get_size()

        total_w_px = self.grid_width * config.CELL_PX
        total_h_px = self.grid_height * config.CELL_PX

        global_off_x = (w_limit - total_w_px) // 2
        global_off_y = (h_limit - total_h_px) // 2

        start_px_x = global_off_x - (self.scroll_x * config.CELL_PX)
        start_px_y = global_off_y - (self.scroll_y * config.CELL_PX)

        if self.show_panel:

            if mx < config.PANEL_W:
                return

        cx = (mx - start_px_x) // config.CELL_PX
        cy = (my - start_px_y) // config.CELL_PX

        if (cx, cy) != (self.cur_cx, self.cur_cy):

            if 0 <= cx < self.grid_width and 0 <= cy < self.grid_height:

                self.life.toggle_cell(cx, cy)

                self.cur_cx = cx
                self.cur_cy = cy

    def _on_btn(self, b):

        d = self.slider_den.value
        dr = self.slider_den_rules.value

        if b is self.btn_conf_aleat:

            self.life.random_fill(d)

        elif b is self.btn_regla_aleat:

            self.matriz_regla.randomize(dr)

            self.life.sync_rule_from_matrix(
                self.matriz_regla.data
            )

        elif b is self.btn_evol_paso:
            self.btn_pause.active = True
            self.btn_evolucion.active = False
            self.btn_pause.label = "Resume"
            self.life.running = False
            self.life.step()

        elif b is self.btn_limpiar_reg:

            self.matriz_regla.clear()

            self.life.rule[:] = 0

            self.kernel.clear()

        elif b is self.btn_evolucion:
            self.life.running = b.active
            if b.active:
                self.btn_evolucion.label = "Stop"
            else:
                self.btn_evolucion.label = "Start"
                self.btn_pause.active = False
                self.btn_pause.label = "Pause"
                self.life.reset()

        elif b is self.btn_pause:
            self.life.running = not b.active
            if b.active:
                self.btn_pause.label = "Resume"
            else:
                self.btn_pause.label = "Pause"

        elif b is self.btn_limpiar_vis:
            self.btn_evolucion.active = False
            self.btn_evolucion.label = "Start"
            self.btn_pause.active = False
            self.btn_pause.label = "Pause"

            self.life.full_reset()

        elif b is self.btn_agregar_kernel:

            rule = self.kernel.apply_to_matrix(
                self.matriz_regla
            )

            self.life.rule = rule

        elif b is self.btn_presets:
            self.show_popup = True
            self.preset_popup.open()

        elif b is self.btn_save_preset:
            self.show_popup = True
            self.save_preset_popup.rule = self.matriz_regla.to_rule_array()
            self.save_preset_popup.open()
            print("Save preset opened")

        elif b is self.btn_view_3d:
            if self.life.history:
                self.launch_3d_view()

        elif b is self.btn_ocultar_panel:

            self.show_panel = not self.show_panel

            if self.show_panel:

                self.btn_ocultar_panel.label = "<<"

                self.btn_ocultar_panel.rect.x = (
                    config.PANEL_W - config.PAD - 40
                )

            else:

                self.btn_ocultar_panel.label = ">>"

                self.btn_ocultar_panel.rect.x = config.PAD
        

    def draw(self):
        self.theme["bg"] = self.bg_color_selectors[0].get_color()
        self.theme["grid"] = self.bg_color_selectors[1].get_color()
        self.theme["cell"] = self.bg_color_selectors[2].get_color()

        self.screen.fill((10, 10, 12))

        self.life.draw(
            self.screen,
            self.theme,
            self.scroll_x,
            self.scroll_y
        )

        if self.show_panel:

            self._draw_panel()

            self.btn_ocultar_panel.draw(
                self.panel_surf,
                self.fm
            )

            self.screen.blit(self.panel_surf, (0, 0))

            pygame.draw.line(
                self.screen,
                config.P_BORDER,
                (config.PANEL_W, 0),
                (config.PANEL_W, config.WIN_H),
                2
            )

        else:

            self.btn_ocultar_panel.draw(
                self.screen,
                self.fm
            )

        self.preset_popup.draw(self.screen)
        self.save_preset_popup.draw(self.screen)
        self.confirm_popup.draw(self.screen)

        pygame.display.flip()

    def _draw_panel(self):

        surf = self.panel_surf

        surf.fill(config.P_BG)

        # =====================================================
        # RULE MATRIX
        # =====================================================

        config.draw_text(
            surf,
            self.fb,
            "Evolution Rule (512 bits)",
            (config.PAD, self.y_rule_hdr),
            config.P_FG
        )

        self.matriz_regla.draw(
            surf,
            self.mat_rects,
            self.fxs
        )

        self.kernel.draw(
            surf,
            self.fxs
        )

        # Info del kernel a su derecha 
        xi = self.x_kern_info 
        yi = self.y_kern_info 
        lineas = [ 
            "Clic en cada celda del", 
            "kernel para activarla.", 
            "La regla se recalcula:", 
            "rule[i]=1 si todos los", 
            "bits del kernel activos", 
            "estan en el indice i.", 
            ] 
        for ln in lineas: 
            config.draw_text(surf, self.fn, ln, (xi, yi), config.P_LABEL) 
            yi += 11 
            yi += 4 
        config.draw_text(surf, self.fn, "Mascara:", (xi, yi), config.P_LABEL) 
        config.draw_text(surf, self.fb, f"{self.kernel.mask:09b} ({self.kernel.mask})", (xi + 65, yi), config.P_VALUE)

        # =====================================================
        # RULES SECTION
        # =====================================================

        self.btn_agregar_kernel.draw(surf, self.fm)
        self.btn_regla_aleat.draw(surf, self.fm)
        self.btn_limpiar_reg.draw(surf, self.fm)

        config.draw_text(
            surf,
            self.fxs,
            "Density Rules",
            (self.x_den_rules_lbl, self.y_den_rules_lbl),
            config.P_LABEL
        )

        self.slider_den_rules.draw(surf, self.fxs)

        self.btn_presets.draw(surf, self.fm)
        self.btn_save_preset.draw(surf, self.fm)

        # =====================================================
        # POPULATION SECTION
        # =====================================================

        config.draw_text(
            surf,
            self.fb,
            "Population",
            (config.PAD, self.y_population_hdr),
            config.P_FG
        )

        pygame.draw.line(
            surf,
            config.P_BORDER,
            (config.PAD, self.y_population_hdr + 16),
            (config.PANEL_W - config.PAD, self.y_population_hdr + 16)
        )

        self.btn_conf_aleat.draw(surf, self.fm)
        self.btn_limpiar_vis.draw(surf, self.fm)

        config.draw_text(
            surf,
            self.fxs,
            "Density Population",
            (config.PAD, self.y_den_lbl),
            config.P_LABEL
        )

        self.slider_den.draw(surf, self.fxs)

        # =====================================================
        # EVOLUTION SECTION
        # =====================================================

        config.draw_text(
            surf,
            self.fb,
            "Evolution",
            (config.PAD, self.y_evolution_hdr),
            config.P_FG
        )

        pygame.draw.line(
            surf,
            config.P_BORDER,
            (config.PAD, self.y_evolution_hdr + 16),
            (config.PANEL_W - config.PAD, self.y_evolution_hdr + 16)
        )

        self.btn_evolucion.draw(surf, self.fm)
        self.btn_evol_paso.draw(surf, self.fm)

        self.btn_pause.draw(surf, self.fm)

        self.btn_save.draw(surf, self.fm)
        self.btn_view_3d.draw(surf, self.fm)

        # =====================================================
        # COLORS
        # =====================================================

        for idx, lc in enumerate(["Background", "Grid", "Cell"]):

            config.draw_text(
                surf,
                self.fm,
                lc,
                (
                    config.PAD + idx * ((config.PANEL_W - config.PAD) // 3),
                    self.y_tema_lbl
                ),
                config.P_LABEL
            )

        for idx, b in enumerate(self.bg_color_selectors):
            b.draw(surf, self.fxs)


        # =====================================================
        # BORDER
        # =====================================================

        pygame.draw.rect(
            surf,
            config.P_BORDER,
            (0, 0, config.PANEL_W, config.WIN_H),
            1
        )