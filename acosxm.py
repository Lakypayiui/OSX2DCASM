import pygame
import config

from scenes.menuscene import MenuScene
from scenes.simulationscene import SimulationScene

class ACOSXM:
    FPS = 30

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ACOSXM - Moore Neighborhood Cellular Automaton")
        self.screen = pygame.display.set_mode((config.WIN_W, config.WIN_H))
        self.clock  = pygame.time.Clock()

     
    def run(self):
        menu = MenuScene(self.screen)

        width, height = menu.run()

        sim = SimulationScene(
            self.screen,
            width,
            height
        )

        sim.run()

