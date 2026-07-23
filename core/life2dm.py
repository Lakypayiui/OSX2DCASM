import math
import time
from typing import Counter
from core import config
import pygame
import numpy as np

#  AUTOMATON LOGIC  (numpy for speed)
 
class Life2DM:
    """2D cellular automaton with full Moore neighborhood.

    state   : ndarray uint8 [GRID_H, GRID_W]
    rule    : ndarray uint8 [512]  — rule[idx] = 0 or 1
    """

    def __init__(self, width: int, height: int) -> None:
        """Initializes the cellular automaton.

        Args:
            width: Number of columns in the grid.
            height: Number of rows in the grid.
        """
        self.width: int   = width
        self.height: int  = height
        self.state: np.ndarray   = np.zeros((self.height, self.width), dtype=np.uint8)
        self.rule: np.ndarray    = np.zeros(512,              dtype=np.uint8)
        self.gen: int     = 0
        self.running: bool = False
        self.history: list[np.ndarray] = []
        self.data_population = {'time': [], 'values': []}
        self.data_global_entropy = {'time': [], 'values': []}
        self.data_block_entropy = {'time': [], 'values': []}
     
    def sync_rule_from_matrix(self, matrix_data: list[list[int]]) -> None:
        """Synchronizes the internal rule array from a 16x32 matrix.

        Args:
            matrix_data: A 16x32 list of binary values representing the rule.
        """
        for i in range(16):
            for j in range(32):
                idx = i * 32 + j
                if idx < 512:
                    self.rule[idx] = matrix_data[i][j]

     
    def step(self) -> None:
        """Advances the automaton by one generation using the current rule."""
        s = self.state
        # Neighbors with torus using roll
        nw = np.roll(np.roll(s,  1, 0),  1, 1)
        n  = np.roll(s,  1, 0)
        ne = np.roll(np.roll(s,  1, 0), -1, 1)
        w  = np.roll(s,  1, 1)
        c  = s
        e  = np.roll(s, -1, 1)
        sw = np.roll(np.roll(s, -1, 0),  1, 1)
        ss = np.roll(s, -1, 0)
        se = np.roll(np.roll(s, -1, 0), -1, 1)

        # Identifier: 9 bits (same order as original)
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
        self.history.append(np.rot90(self.state.copy(), -1))

        population = self.state.sum()

        self.data_population['time'].append(self.gen)
        self.data_population['values'].append(population)

        p = population / self.state.size 
        if p == 0:
            global_entropy=0
        else:
            global_entropy = -(p * math.log2(p)  + (1 - p) *  math.log2(1 - p))

        self.data_global_entropy['time'].append(self.gen)
        self.data_global_entropy['values'].append(global_entropy)

        self.data_block_entropy['time'].append(self.gen)
        self.data_block_entropy['values'].append(self.block_entropy(self.state))

    def block_entropy(self, grid):
        a = grid[:-1, :-1]
        b = grid[:-1, 1:]
        c = grid[1:, :-1]
        d = grid[1:, 1:]

        codes = (
            a
            | (b << 1)
            | (c << 2)
            | (d << 3)
        )

        counts = np.bincount(codes.ravel(), minlength=16)

        probs = counts[counts > 0]
        probs = probs / probs.sum()

        return -(probs * np.log2(probs)).sum()

    def tick(self) -> None:
        """Advances the automaton if it is currently running."""
        if self.running:
            self.step()

     
    def reset(self) -> None:
        """Resets generation counter, history, and stops the automaton."""
        self.gen   = 0
        self.history = []
        for data in [self.data_population, self.data_global_entropy, self.data_block_entropy]:
            data['time'] = []
            data['values'] = []
        self.running = False

    def full_reset(self) -> None:
        """Clears the entire grid and resets all counters."""
        self.state[:] = 0
        self.reset()

    def random_fill(self, density: float) -> None:
        """Fills the grid with random alive cells.

        Args:
            density: Probability (0.0 to 1.0) that a cell is set to alive.
        """
        rng = np.random.default_rng(int(time.time() * 1000) & 0xFFFFFFFF)
        self.state = (rng.random((self.height, self.width)) < density).astype(np.uint8)
        self.gen   = 0

    def toggle_cell(self, cx: int, cy: int) -> None:
        """Toggles the state of a single cell.

        Args:
            cx: Column index of the cell.
            cy: Row index of the cell.
        """
        if 0 <= cx < self.width and 0 <= cy < self.height:
            self.state[cy, cx] ^= 1

    def count_alive(self) -> int:
        """Returns the total number of alive cells in the grid.

        Returns:
            Integer count of cells with value 1.
        """
        return int(self.state.sum())

     
    def draw(
        self,
        target_surf: pygame.Surface,
        theme: dict[str, tuple[int, int, int]],
        scroll_x: int,
        scroll_y: int,
    ) -> None:
        """Draws the automaton grid onto a target surface.

        Args:
            target_surf: Pygame surface to render onto.
            theme: Color dictionary with keys ``"bg"``, ``"grid"``, ``"cell"``.
            scroll_x: Horizontal scroll offset in cells.
            scroll_y: Vertical scroll offset in cells.
        """
        w_limit, h_limit = target_surf.get_size()
        rgb = np.full((h_limit, w_limit, 3), theme["bg"], dtype=np.uint8)

        # 1. TOTAL world size in pixels (may be much larger than screen)
        total_w_px = self.width * config.CELL_PX
        total_h_px = self.height * config.CELL_PX

        # 2. GLOBAL OFFSETS
        # If total_w_px < w_limit -> off_x is POSITIVE (centers the small world)
        # If total_w_px > w_limit -> off_x is NEGATIVE (world starts off-screen, centered)
        global_off_x = (w_limit - total_w_px) // 2
        global_off_y = (h_limit - total_h_px) // 2

        # 3. Apply scroll to those offsets
        # Scroll shifts the origin. Multiply by CELL_PX because scroll is in cells
        start_px_x = global_off_x - (scroll_x * config.CELL_PX)
        start_px_y = global_off_y - (scroll_y * config.CELL_PX)

        # 4. Slicing to optimize (only what fits in the screen rectangle)
        # Calculate which cell indices cross the screen edges
        x0 = max(0, -start_px_x // config.CELL_PX)
        y0 = max(0, -start_px_y // config.CELL_PX)
        x1 = min(self.width, (w_limit - start_px_x) // config.CELL_PX + 1)
        y1 = min(self.height, (h_limit - start_px_y) // config.CELL_PX + 1)

        view_state = self.state[y0:y1, x0:x1]

        # 5. Draw visible cells
        ys, xs = np.where(view_state == 1)
        for cx, cy in zip(xs, ys):
            # Real position is: World start + (relative_index + start_index) * size
            px = start_px_x + (cx + x0) * config.CELL_PX + 1
            py = start_px_y + (cy + y0) * config.CELL_PX + 1

            # Safety clipping to avoid painting outside the RGB array
            if 0 <= px < w_limit - config.CELL_PX and 0 <= py < h_limit - config.CELL_PX:
                rgb[py : py + config.CELL_PX - 1, px : px + config.CELL_PX - 1] = theme["cell"]

        # 6. Flush to screen
        pygame.surfarray.blit_array(target_surf, np.ascontiguousarray(rgb.swapaxes(0, 1)))

        # 7. Grid (only on visible world area)
        # Draw lines from the actual world start to its end
        for i in range(x0, x1 + 1):
            lx = start_px_x + i * config.CELL_PX
            pygame.draw.line(target_surf, theme["grid"], (lx, max(0, start_px_y)), (lx, min(h_limit, start_px_y + total_h_px)))
        for i in range(y0, y1 + 1):
            ly = start_px_y + i * config.CELL_PX
            pygame.draw.line(target_surf, theme["grid"], (max(0, start_px_x), ly), (min(w_limit, start_px_x + total_w_px), ly))
