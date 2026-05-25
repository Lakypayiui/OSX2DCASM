import time
import config
import pygame
import numpy as np

#  LOGICA DEL AUTOMATA  (numpy para velocidad)
 
class Life2DM:
    """
    Automata celular 2D vecindad de Moore completa.
    state   : ndarray uint8 [GRID_H, GRID_W]
    rule    : ndarray uint8 [512]  — rule[idx] = 0 o 1
    """
    def __init__(self):
        self.state   = np.zeros((config.GRID_H, config.GRID_W), dtype=np.uint8)
        self.rule    = np.zeros(512,              dtype=np.uint8)
        self.gen     = 0
        self.running = False
     
    def sync_rule_from_matrix(self, matrix_data):
        """matrix_data: lista[16][32]  -> self.rule[512]"""
        for i in range(16):
            for j in range(32):
                idx = i * 32 + j
                if idx < 512:
                    self.rule[idx] = matrix_data[i][j]
        print(self.rule)

     
    def step(self):
        s = self.state
        # Vecinos con toroide usando roll
        nw = np.roll(np.roll(s,  1, 0),  1, 1)
        n  = np.roll(s,  1, 0)
        ne = np.roll(np.roll(s,  1, 0), -1, 1)
        w  = np.roll(s,  1, 1)
        c  = s
        e  = np.roll(s, -1, 1)
        sw = np.roll(np.roll(s, -1, 0),  1, 1)
        ss = np.roll(s, -1, 0)
        se = np.roll(np.roll(s, -1, 0), -1, 1)

        # Identificador: 9 bits (mismo orden que el original)
        idx = (nw.astype(np.uint16)        |
               n .astype(np.uint16) <<  1  |
               ne.astype(np.uint16) <<  2  |
               w .astype(np.uint16) <<  3  |
               c .astype(np.uint16) <<  4  |
               e .astype(np.uint16) <<  5  |
               sw.astype(np.uint16) <<  6  |
               ss.astype(np.uint16) <<  7  |
               se.astype(np.uint16) <<  8)

        self.state = self.rule[idx].astype(np.uint8)
        self.gen  += 1

    def tick(self):
        if self.running:
            self.step()

     
    def reset(self):
        self.state[:] = 0
        self.gen   = 0

    def random_fill(self, density):
        rng = np.random.default_rng(int(time.time() * 1000) & 0xFFFFFFFF)
        self.state = (rng.random((config.GRID_H, config.GRID_W)) < density).astype(np.uint8)
        self.gen   = 0

    def rule110_fill(self, density):
        nb  = config.rule_binary(110)
        rng = np.random.default_rng(int(time.time() * 1000) & 0xFFFFFFFF)
        row = (rng.random(config.GRID_W) < density).astype(np.uint8)
        self.state[:] = 0
        self.state[0] = row
        for i in range(1, config.GRID_H):
            new_row = np.zeros(config.GRID_W, dtype=np.uint8)
            for j in range(config.GRID_W):
                l = int(row[(j - 1) % config.GRID_W])
                cv = int(row[j])
                r  = int(row[(j + 1) % config.GRID_W])
                new_row[j] = nb[l * 4 + cv * 2 + r]
            self.state[i] = new_row
            row = new_row
        self.gen   = 0

    def toggle_cell(self, cx, cy):
        if 0 <= cx < config.GRID_W and 0 <= cy < config.GRID_H:
            self.state[cy, cx] ^= 1

    def count_alive(self):
        return int(self.state.sum())

     
    def draw(self, target_surf, theme, scroll_x, scroll_y):
        w_limit, h_limit = target_surf.get_size()
        rgb = np.full((h_limit, w_limit, 3), theme["bg"], dtype=np.uint8)

        # 1. Tamaño TOTAL del mundo en píxeles (puede ser mucho mayor que la pantalla)
        total_w_px = config.GRID_W * config.CELL_PX
        total_h_px = config.GRID_H * config.CELL_PX

        # 2. OFFSETS GLOBALES
        # Si total_w_px < w_limit -> off_x es POSITIVO (centra el mundo pequeño)
        # Si total_w_px > w_limit -> off_x es NEGATIVO (el mundo empieza fuera de pantalla, centrado)
        global_off_x = (w_limit - total_w_px) // 2
        global_off_y = (h_limit - total_h_px) // 2

        # 3. Aplicar el scroll a esos offsets
        # El scroll desplaza el origen. Multiplicamos por CELL_PX porque el scroll es en celdas
        start_px_x = global_off_x - (scroll_x * config.CELL_PX)
        start_px_y = global_off_y - (scroll_y * config.CELL_PX)

        # 4. Slicing para optimizar (solo lo que entra en el rectángulo de la pantalla)
        # Calculamos qué índices de celda están cruzando los bordes de la pantalla
        x0 = max(0, -start_px_x // config.CELL_PX)
        y0 = max(0, -start_px_y // config.CELL_PX)
        x1 = min(config.GRID_W, (w_limit - start_px_x) // config.CELL_PX + 1)
        y1 = min(config.GRID_H, (h_limit - start_px_y) // config.CELL_PX + 1)

        view_state = self.state[y0:y1, x0:x1]

        # 5. Dibujar celdas visibles
        ys, xs = np.where(view_state == 1)
        for cx, cy in zip(xs, ys):
            # La posición real es: Inicio del mundo + (índice_relativo + índice_inicial) * tamaño
            px = start_px_x + (cx + x0) * config.CELL_PX + 1
            py = start_px_y + (cy + y0) * config.CELL_PX + 1
            
            # Clipping de seguridad para no pintar fuera del array RGB
            if 0 <= px < w_limit - config.CELL_PX and 0 <= py < h_limit - config.CELL_PX:
                rgb[py : py + config.CELL_PX - 1, px : px + config.CELL_PX - 1] = theme["cell"]

        # 6. Volcar a pantalla
        pygame.surfarray.blit_array(target_surf, np.ascontiguousarray(rgb.swapaxes(0, 1)))

        # 7. Malla (solo en el área visible del mundo)
        # Dibujamos líneas desde el inicio real del mundo hasta su fin
        for i in range(x0, x1 + 1):
            lx = start_px_x + i * config.CELL_PX
            pygame.draw.line(target_surf, theme["grid"], (lx, max(0, start_px_y)), (lx, min(h_limit, start_px_y + total_h_px)))
        for i in range(y0, y1 + 1):
            ly = start_px_y + i * config.CELL_PX
            pygame.draw.line(target_surf, theme["grid"], (max(0, start_px_x), ly), (min(w_limit, start_px_x + total_w_px), ly))
