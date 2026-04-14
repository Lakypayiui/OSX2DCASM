import sys
import math
import random
import time
import pygame
import config
from life2dm import Life2DM
from matrizregla import MatrizRegla
from kernel import Kernel3x3
from widgets.button import Button
from widgets.slider import Slider

class ACOSXM:
    FPS = 30

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ACOSXM - Automata Celular Vecindad de Moore")
        self.screen = pygame.display.set_mode((config.WIN_W, config.WIN_H))
        self.clock  = pygame.time.Clock()

        # Tamaño de botones y gap entre ellos en el panel
        BW, BH, BGAP = 183, 22, 4

        # Fuentes
        self.fn  = pygame.font.SysFont("monospace",  10)
        self.fm  = pygame.font.SysFont("monospace", 12)
        self.fb  = pygame.font.SysFont("monospace", 14, bold=True)
        self.fxs = pygame.font.SysFont("monospace",  12)

        self.show_panel = True

        self.theme_idx = 0

        # ── Objetos del automata 
        self.matriz_regla = MatrizRegla()
        self.life         = Life2DM()

        # ── Layout: posiciones Y de cada seccion 
        y = config.PAD

        # Boton ocultar panel
        self.btn_ocultar_panel = Button((config.PANEL_W - config.PAD - 40, y, 40, 20),
                                       "<<", toggle=False, bg=config.BTN_OFF_BG, bg_on=config.BTN_ON_BG)

        # Encabezado regla
        self.y_rule_hdr = y;  y += 18

        

        # Numeracion de columnas de la matriz
        self.y_colnum = y;    y += 10

        # Matriz 16x32
        self.y_mat = y
        MAT_X0 = config.PAD + 16
        self.mat_rects = self.matriz_regla.build_rects(MAT_X0, y)
        y += self.matriz_regla.total_h + config.PAD + 4

        # Separador visual
        self.y_sep1 = y - 4

        # Encabezado kernel
        self.y_kern_hdr = y 
        y += 18 

        # Kernel 3x3  (izquierda)
        KERN_X = config.PAD
        self.kernel = Kernel3x3(KERN_X, y)

        # Info del kernel (a la derecha del kernel)
        self.x_kern_info = KERN_X + self.kernel.total_w + 16
        self.y_kern_info = y
        

        # Boton Agregar kernel (a la derecha de la info del kernel)
        self.btn_agregar_kernel = Button((config.PANEL_W/2, y, BW, BH), "Agregar kernel",
                                        toggle=False, bg=config.BTN_OFF_BG, bg_on=config.BTN_ON_BG)
        
        y += self.kernel.total_h + (config.PAD*2) + 4

        # Separador
        self.y_sep2 = y
        y += config.PAD

        # Botones de accion

        def btn_panel(label, col, yy, toggle=False,
                bg=config.BTN_OFF_BG, bg_on=(170, 55, 55)):
            return Button((config.PAD + col * (BW + BGAP), yy, BW, BH),
                          label, toggle=toggle, bg=bg, bg_on=bg_on)

        self.btn_conf_aleat  = btn_panel("Config. aleatoria",  0, y)
        self.btn_regla_aleat = btn_panel("Regla aleatoria",    1, y);  y += BH + BGAP
        self.btn_evol_paso   = btn_panel("Paso a paso",        0, y)
        self.btn_limpiar_reg = btn_panel("Limpiar regla",      1, y);  y += BH + BGAP
        self.btn_evolucion   = btn_panel("Evolucion", 0, y,
                                   toggle=True, bg=(45, 120, 60))
        self.btn_regla110    = btn_panel("Regla 110",          1, y);  y += BH + BGAP
        self.btn_limpiar_vis = btn_panel("Limpiar vista",      0, y);  y += BH + config.PAD * 2
        #self.btn_agregar_kernel = btn_panel("Agregar kernel",      1, y)

        # Slider densidad
        self.y_den_lbl = y; y += 13
        self.slider_den = Slider((config.PAD, y, config.PANEL_W - 65, 12), value=0.5)
        y += 20 + config.PAD

        # Selector de tema
        self.y_tema_lbl = y; y += 13
        TBW = (config.PANEL_W - config.PAD) // len(config.COLOR_THEMES) - 2
        self.tema_btns = []
        for idx, t in enumerate(config.COLOR_THEMES):
            bx = config.PAD + idx * (TBW + 2)
            self.tema_btns.append(
                Button((bx, y, TBW, 17), t["name"][:6],
                       bg=(38, 38, 46), fg=config.BTN_OFF_FG))
        y += 17 + config.PAD

        # Info
        self.y_info = y

        # Listas para iterar
        self._action_btns = [
            self.btn_conf_aleat, self.btn_regla_aleat,
            self.btn_evol_paso,  self.btn_limpiar_reg,
            self.btn_evolucion,  self.btn_regla110,
            self.btn_limpiar_vis, self.btn_agregar_kernel,
            self.btn_ocultar_panel
        ]
        self._all_btns = self._action_btns + self.tema_btns

        # Surface del panel
        self.panel_surf = pygame.Surface((config.PANEL_W, config.WIN_H))

        # Scroll y cursor
        self.scroll_x = 0; self.scroll_y = 0
        self.cur_cx   = 0; self.cur_cy   = 0

     
    @property
    def theme(self):
        return config.COLOR_THEMES[self.theme_idx]

     
    def run(self):
        while True:
            self.clock.tick(self.FPS)
            self._events()
            self.life.tick()
            self._draw()

     
    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

            # Scroll
            if ev.type == pygame.MOUSEWHEEL:
                mx, _ = pygame.mouse.get_pos()
                if mx >= config.PANEL_W:
                    self.scroll_y = self.scroll_y - ev.y
                    self.scroll_x = self.scroll_x + ev.x
            
            # Zoom
            if ev.type == pygame.KEYDOWN:
                # Tecla +
                if ev.key == pygame.K_PLUS or ev.key == pygame.K_KP_PLUS:
                    config.CELL_PX *= 2
                    config.CELL_PX =int(config.CELL_PX)

                # Tecla -
                elif ev.key == pygame.K_MINUS or ev.key == pygame.K_KP_MINUS:
                    config.CELL_PX *= 0.5
                    config.CELL_PX = int(config.CELL_PX)

                config.SPACE_W = config.GRID_W * config.CELL_PX
                config. SPACE_H = config.GRID_H * config.CELL_PX
                self.life.surf = pygame.Surface((config.SPACE_W, config.SPACE_H))
                self.life.dirty = True

                # Limitar zoom
                #CELL_PX = max(0.1, min(5.0, CELL_PX))

            # Clic en espacio de evoluciones
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                mx, my = ev.pos
                if (self.show_panel and mx > config.PANEL_W) or not self.show_panel:
                    cx = mx // config.CELL_PX + self.scroll_x
                    cy = my              // config.CELL_PX + self.scroll_y
                    self.life.toggle_cell(cx, cy)
                    self.cur_cx, self.cur_cy = cx, cy

            # Arrastrar en espacio
            if ev.type == pygame.MOUSEMOTION and ev.buttons[0]:
                mx, my = ev.pos
                if (self.show_panel and mx > config.PANEL_W) or not self.show_panel:
                    cx = mx // config.CELL_PX + self.scroll_x
                    cy = my              // config.CELL_PX + self.scroll_y
                    if (cx, cy) != (self.cur_cx, self.cur_cy):
                        self.life.toggle_cell(cx, cy)
                        self.cur_cx, self.cur_cy = cx, cy

            # Slider
            self.slider_den.handle_event(ev)

            # Botones de accion + tema
            for b in self._all_btns:
                if b.handle_event(ev):
                    self._on_btn(b)

            # Clic en la matriz de la regla
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                res = self.matriz_regla.handle_click(ev.pos, self.mat_rects)
                if res is not None:
                    # Sincronizar con Life2DM
                    self.life.sync_rule_from_matrix(self.matriz_regla.data)
                    # Mostrar mascara del kernel
                    self.kernel.set_kernel_mask(res)

            # Clic en el kernel 3x3
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                bit = self.kernel.handle_click(ev.pos)

     
    def _on_btn(self, b):
        d = self.slider_den.value

        if   b is self.btn_conf_aleat:
            self.life.random_fill(d)

        elif b is self.btn_regla_aleat:
            self.matriz_regla.randomize()
            self.life.sync_rule_from_matrix(self.matriz_regla.data)

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
            rule = self.kernel.apply_to_matrix(self.matriz_regla)
            self.life.rule = rule

        elif b is self.btn_ocultar_panel:
            self.show_panel = not self.show_panel
            if self.show_panel:
                self.btn_ocultar_panel.label = "<<"
            else:
                self.btn_ocultar_panel.label = ">>"

        else:
            for idx, tb in enumerate(self.tema_btns):
                if b is tb:
                    self.theme_idx = idx
                    self.life.dirty = True
                    break

     
    def _draw(self):
        self.screen.fill((10, 10, 12))

        # Espacio de evoluciones
        self.life.draw(self.theme)
        vr = pygame.Rect(
            self.scroll_x * config.CELL_PX, self.scroll_y * config.CELL_PX,
            config.SPACE_W,
            min(config.WIN_H, config.SPACE_H))
        self.screen.blit(self.life.surf, (0, 0), area=vr)

        # Panel
        if self.show_panel:
            self._draw_panel()
            self.btn_ocultar_panel.draw(self.panel_surf, self.fm)
            self.screen.blit(self.panel_surf, (0, 0))
            pygame.draw.line(self.screen, config.P_BORDER,
                            (config.PANEL_W, 0), (config.PANEL_W, config.WIN_H), 2)
        else:
            self.btn_ocultar_panel.draw(self.screen, self.fm)

        # Titulo del espacio
        t = self.fb.render(
            f"Espacio de evoluciones",
            True, (110, 110, 128))
        self.screen.blit(t, (config.PANEL_W + 6, 4))

        pygame.display.flip()

     
    def _draw_panel(self):
        surf = self.panel_surf
        surf.fill(config.P_BG)

        # ── Encabezado matriz    ───────────────────
        config.draw_text(surf, self.fb, "Regla de evolucion  (16 x 32 = 512 bits)",
                  (config.PAD, self.y_rule_hdr), config.P_FG)
        
        

        # Numeracion de columnas (cada 8)
        for j in range(0, 32, 8):
            rx = config.PAD + 16 + j * (MatrizRegla.BW + MatrizRegla.BM)
            config.draw_text(surf, self.fxs, str(j), (rx, self.y_colnum), config.P_LABEL)

        # Numeracion de filas
        for i in range(16):
            ry = self.y_mat + i * (MatrizRegla.BH + MatrizRegla.BM)
            config.draw_text(surf, self.fxs, str(i), (config.PAD, ry + 2), config.P_LABEL)

        # Matriz 16x32
        self.matriz_regla.draw(surf, self.mat_rects, self.fxs)

        # Separador
        pygame.draw.line(surf, config.P_BORDER,
                         (config.PAD, self.y_sep1), (config.PANEL_W - config.PAD, self.y_sep1))

        # ── Kernel 3x3    ──────────────────────────
        config.draw_text(surf, self.fb, "Kernel",
                         (config.PAD, self.y_kern_hdr), config.P_FG)

        self.kernel.draw(surf, self.fxs)

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
        config.draw_text(surf, self.fn,  "Mascara:", (xi, yi), config.P_LABEL)
        config.draw_text(surf, self.fb,
                  f"{self.kernel.mask:09b}  ({self.kernel.mask})",
                  (xi + 55, yi), config.P_VALUE)

        # Separador
        pygame.draw.line(surf, config.P_BORDER,
                         (config.PAD, self.y_sep2), (config.PANEL_W - config.PAD, self.y_sep2))

        # ── Botones de accion    ───────────────────
        for b in self._action_btns:
            b.draw(surf, self.fm)

        # ── Slider densidad    ─────────────────────
        config.draw_text(surf, self.fxs, "Densidad",
                  (config.PAD, self.y_den_lbl), config.P_LABEL)
        self.slider_den.draw(surf, self.fxs)

        # ── Selector de tema    ────────────────────
        config.draw_text(surf, self.fxs, "Modo de color",
                  (config.PAD, self.y_tema_lbl), config.P_LABEL)
        for idx, b in enumerate(self.tema_btns):
            if idx == self.theme_idx:
                hl = b.rect.inflate(4, 4)
                pygame.draw.rect(surf, config.COLOR_THEMES[idx]["cell"],
                                 hl, border_radius=4)
            b.draw(surf, self.fxs)

        # ── Info de estado    ──────────────────────
        y = self.y_info

        def kv(label, val):
            nonlocal y
            config.draw_text(surf, self.fm, label,      (config.PAD,       y), config.P_LABEL)
            config.draw_text(surf, self.fb, str(val),   (config.PAD + 118, y), config.P_VALUE)
            y += 14

        kv("Generaciones:", self.life.gen)
        kv("Celulas vivas:", self.life.count_alive())
        kv("Cursor  x:",     self.cur_cx)
        kv("Cursor  y:",     self.cur_cy)

        est   = "   CORRIENDO" if self.life.running else "   DETENIDO"
        sym   = "▶" if self.life.running else "■"
        color = (75, 220, 95) if self.life.running else (190, 70, 70)
        config.draw_text(surf, self.fb, sym + est, (config.PAD, y), color)
        y += 16

        # Ayuda
        y += 4
        for h in ["ESC: salir",
                  "Rueda: scroll",
                  "Clic+arrastrar: dibujar celulas"]:
            config.draw_text(surf, self.fxs, h, (config.PAD, y), config.P_LABEL)
            y += 11

        # Borde del panel
        pygame.draw.rect(surf, config.P_BORDER, (0, 0, config.PANEL_W, config.WIN_H), 1)
