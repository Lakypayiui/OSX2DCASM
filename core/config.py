import numpy as np
import pygame

#  AUTOMATON CONSTANTS
CELL_PX = 8

 
#  WINDOW LAYOUT
#SPACE_W = GRID_W * CELL_PX
#SPACE_H = GRID_H * CELL_PX
PAD = 8

# Panel palette
P_BG     = ( 28,  28,  32)
P_FG     = (220, 220, 225)
P_LABEL  = (140, 140, 155)
P_VALUE  = (  0, 230, 120)
P_BORDER = ( 55,  55,  65)
P_ACCENT = ( 70, 170,  90)

BTN_OFF_BG  = ( 50,  50,  58)
BTN_OFF_FG  = (190, 190, 200)
BTN_ON_BG   = ( 72, 195, 105)
BTN_ON_FG   = ( 10,  10,  10)
BTN_HOV     = ( 75,  75,  88)
 
#  UTILITIES
 
def draw_text(
    surf: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    pos: tuple[int, int],
    color: tuple[int, int, int],
    align: str = "left",
) -> None:
    """Renders and blits text onto a surface.

    Args:
        surf: Target surface to draw on.
        font: Font used to render the text.
        text: Text to render.
        pos: (x, y) position for the text.
        color: RGB color tuple for the text.
        align: Horizontal alignment: ``"left"``, ``"center"``, or ``"right"``.
    """
    img = font.render(str(text), True, color)
    x, y = pos
    if   align == "right":  x -= img.get_width()
    elif align == "center": x -= img.get_width() // 2
    surf.blit(img, (x, y))


def rule_binary(n: int) -> list[int]:
    """Converts an integer into a list of 8 bits (LSB first).

    Args:
        n: Integer value in the range [0, 255].

    Returns:
        List of 8 integers (0 or 1) representing the binary digits,
        with the least significant bit at index 0.
    """
    return [(n >> i) & 1 for i in range(8)]
