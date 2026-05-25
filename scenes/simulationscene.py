import sys
import pygame

import config

from life2dm import Life2DM
from matrizregla import MatrizRegla
from kernel import Kernel3x3

from widgets.button import Button
from widgets.slider import Slider
from widgets.rgbselector import RGBSelector


class SimulationScene:

    def __init__(self, screen, width, height):

        self.screen = screen

        # Mundo
        self.grid_width = width
        self.grid_height = height

        # Fuentes
        self.fn  = pygame.font.SysFont("monospace", 10)
        self.fm  = pygame.font.SysFont("monospace", 12)
        self.fb  = pygame.font.SysFont("monospace", 14, bold=True)
        self.fxs = pygame.font.SysFont("monospace", 12)

        # Estado
        self.running = True
        self.show_panel = True
        self.theme = {"bg": ( 13, 13, 13), "grid": ( 25, 40, 25), "cell": (  0,255,100)}

        # Automata
        self.matriz_regla = MatrizRegla()
        self.life = Life2DM(width, height)

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
        y += 18

        KERN_X = config.PAD

        self.kernel = Kernel3x3(KERN_X, y)

        self.x_kern_info = KERN_X + self.kernel.total_w + 16
        self.y_kern_info = y

        self.btn_agregar_kernel = Button(
            (config.PANEL_W / 2, y, BW, BH),
            "Add kernel",
            toggle=False,
            bg=config.BTN_OFF_BG,
            bg_on=config.BTN_ON_BG
        )

        y += self.kernel.total_h + (config.PAD * 2) + 4

        self.y_sep2 = y

        y += config.PAD

        # Helper botones
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

        self.btn_conf_aleat = btn_panel(
            "Random config",
            0,
            y
        )

        self.btn_regla_aleat = btn_panel(
            "Random rule",
            1,
            y
        )

        y += BH + BGAP

        self.btn_evol_paso = btn_panel(
            "Step by step",
            0,
            y
        )

        self.btn_limpiar_reg = btn_panel(
            "Clear rule",
            1,
            y
        )

        y += BH + BGAP

        self.btn_evolucion = btn_panel(
            "Evolution",
            0,
            y,
            toggle=True,
            bg=(45, 120, 60)
        )

        y += BH + BGAP

        self.btn_limpiar_vis = btn_panel(
            "Clear view",
            0,
            y
        )

        y += BH + config.PAD * 2

        # Slider
        self.y_den_lbl = y

        y += 13

        self.slider_den = Slider(
            (config.PAD, y, config.PANEL_W - 65, 12),
            value=0.5
        )

        y += 30 + config.PAD

        # Temas
        self.y_tema_lbl = y

        y += 13

        TBW = (config.PANEL_W - config.PAD) // len(config.COLOR_THEMES) - 2

        self.tema_btns = []

        self.bg_color_selectors = []

        labels_colors = ["bg", "grid", "cell"]
        CSW = (config.PANEL_W - config.PAD) // len(labels_colors) - 2
        for idx, lc in enumerate(labels_colors):
            bx = config.PAD + idx * (CSW + 2)
            self.bg_color_selectors.append(RGBSelector(
                (bx, y, CSW, 80), initial=self.theme[lc.lower().replace(" ", "")]
            ))

        bx = config.PAD + idx * (CSW + 2)

        y += 17 + config.PAD
        

        for idx, t in enumerate(config.COLOR_THEMES):

            bx = config.PAD + idx * (TBW + 2)

            self.tema_btns.append(
                Button(
                    (bx, y, TBW, 17),
                    t["name"][:6],
                    bg=(38, 38, 46),
                    fg=config.BTN_OFF_FG
                )
            )

        y += 17 + config.PAD

        self.y_info = y

        self._action_btns = [
            self.btn_conf_aleat,
            self.btn_regla_aleat,
            self.btn_evol_paso,
            self.btn_limpiar_reg,
            self.btn_evolucion,
            self.btn_limpiar_vis,
            self.btn_agregar_kernel,
            self.btn_ocultar_panel
        ]

        self._all_btns = self._action_btns + self.tema_btns

        self.panel_surf = pygame.Surface(
            (config.PANEL_W, config.WIN_H)
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

            # Botones
            for b in self._all_btns:

                if b.handle_event(ev):

                    self._on_btn(b)

            # Selectores de color
            for s in self.bg_color_selectors:
                s.handle_event(ev)

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

    def _paint_cell(self, pos):

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

        if b is self.btn_conf_aleat:

            self.life.random_fill(d)

        elif b is self.btn_regla_aleat:

            self.matriz_regla.randomize()

            self.life.sync_rule_from_matrix(
                self.matriz_regla.data
            )

        elif b is self.btn_evol_paso:

            self.life.step()

        elif b is self.btn_limpiar_reg:

            self.matriz_regla.clear()

            self.life.rule[:] = 0

            self.kernel.clear()

        elif b is self.btn_evolucion:

            self.life.running = b.active

        elif b is self.btn_regla110:

            self.life.rule110_fill(d)

        elif b is self.btn_limpiar_vis:

            if self.life.running:

                self.life.running = False

                self.btn_evolucion.active = False

            self.life.reset()

        elif b is self.btn_agregar_kernel:

            rule = self.kernel.apply_to_matrix(
                self.matriz_regla
            )

            self.life.rule = rule

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

        pygame.display.flip()

    def _draw_panel(self):

        surf = self.panel_surf

        surf.fill(config.P_BG)

        config.draw_text(
            surf,
            self.fb,
            "Regla de evolucion (512 bits)",
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

        for b in self._action_btns:
            b.draw(surf, self.fm)

        self.slider_den.draw(surf, self.fxs)

        for idx, lc in enumerate(["Background", "Grid", "Cell"]):
            config.draw_text(
                surf,
                self.fm,
                lc,
                (config.PAD + idx * ((config.PANEL_W - config.PAD) // 3), self.y_tema_lbl),
                config.P_LABEL
            )

        

        for idx, b in enumerate(self.bg_color_selectors):
            b.draw(surf, self.fxs)

        pygame.draw.rect(
            surf,
            config.P_BORDER,
            (0, 0, config.PANEL_W, config.WIN_H),
            1
        )