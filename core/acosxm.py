import pygame
from core import config
from scenes.menuscene import MenuScene
from scenes.simulationscene import SimulationScene

class ACOSXM:
    FPS = 30

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("ACOSXM - Moore Neighborhood Cellular Automaton")
        
        # Ventana redimensionable
        self.screen = pygame.display.set_mode(
            (config.WIN_W, config.WIN_H), 
            pygame.RESIZABLE
        )
        
        self.clock = pygame.time.Clock()
        self.current_width = config.WIN_W
        self.current_height = config.WIN_H

    def run(self):
        menu = MenuScene(self.screen)
        width, height = menu.run()
        
        sim = SimulationScene(self.screen, width, height)
        sim.run()