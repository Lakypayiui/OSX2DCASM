from config import *
#  3x3 KERNEL (editable Moore neighborhood)
 
class Kernel3x3:
    """
    Represents the 9 bits of the kernel (Moore neighborhood).
    """

    CELL_S = 44   # Was 22, now doubled

    LABELS = [
        "NW", "N",  "NE",
        "W",  "C",  "E",
        "SW", "S",  "SE"
    ]

    def __init__(self, x, y):

        self.active = True

        self.x = x
        self.y = y

        self.bits = [0] * 9

        self.rects = [
            pygame.Rect(
                x + (i % 3) * self.CELL_S,
                y + (i // 3) * self.CELL_S,
                self.CELL_S - 4,
                self.CELL_S - 4
            )
            for i in range(9)
        ]

    @property
    def total_w(self):
        return self.CELL_S * 3

    @property
    def total_h(self):
        return self.CELL_S * 3

    @property
    def mask(self):

        m = 0

        for i, b in enumerate(self.bits):
            m |= b << i

        return m

    def handle_click(self, pos):

        if self.active:

            for i, r in enumerate(self.rects):

                if r.collidepoint(pos):
                    self.bits[i] ^= 1
                    return i

        return None

    def set_kernel_mask(self, num):

        if num < 0 or num > 0x1FF:
            raise ValueError(
                "Kernel mask must be a 9-bit integer (0-511)."
            )

        for i in range(9):
            self.bits[i] = (num >> i) & 1

    def apply_to_matrix(self, rule_matrix):
        m = self.mask

        for idx in range(512):

            if idx == int(m):
                rule_matrix.data[idx // 32][idx % 32] = 1

        return rule_matrix.to_rule_array()

    def draw(self, surf, font):

        # Scale labels to double
        big_font = pygame.font.SysFont(
            "monospace",
            font.get_height(),
            bold=True
        )

        for i, r in enumerate(self.rects):

            v = self.bits[i]

            bg = BTN_ON_BG if v else BTN_OFF_BG
            fg = BTN_ON_FG if v else BTN_OFF_FG

            pygame.draw.rect(
                surf,
                bg,
                r,
                border_radius=6
            )

            pygame.draw.rect(
                surf,
                P_BORDER,
                r,
                2,
                border_radius=6
            )

            lbl = big_font.render(
                self.LABELS[i],
                True,
                fg
            )

            surf.blit(
                lbl,
                (
                    r.centerx - lbl.get_width() // 2,
                    r.centery - lbl.get_height() // 2
                )
            )

    def clear(self):

        for i in range(9):
            self.bits[i] = 0