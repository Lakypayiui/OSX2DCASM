import numpy as np
import pygame

#  SCREEN AND AUTOMATON CONFIGURATION

pygame.display.init()
info = pygame.display.Info()
SCREEN_W = info.current_w
SCREEN_H = info.current_h

WIN_W   = int(SCREEN_W * 0.9)
WIN_H   = int(SCREEN_H * 0.9)
#  AUTOMATON CONSTANTS
 

GRID_W  = 100 # space columns (RING  / FACTOR)
GRID_H  = 100   # space rows    (LINES / FACTOR)
CELL_PX = max(4, WIN_W // GRID_W)      # pixels per cell

 
#  WINDOW LAYOUT
PANEL_W = int(WIN_W * 0.4)
SPACE_W = GRID_W * CELL_PX
SPACE_H = GRID_H * CELL_PX
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
 
def draw_text(surf, font, text, pos, color, align="left"):
    img = font.render(str(text), True, color)
    x, y = pos
    if   align == "right":  x -= img.get_width()
    elif align == "center": x -= img.get_width() // 2
    surf.blit(img, (x, y))


def rule_binary(n):
    """Integer -> list of 8 bits (LSB first)."""
    return [(n >> i) & 1 for i in range(8)]