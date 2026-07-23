import pygame
from core import config
from scenes.menuscene import MenuScene
from scenes.simulationscene import SimulationScene

class ACOSXM:
    """Main application entry point for the ACOSXM cellular automaton.

    Manages the game loop, screen, clock, and transitions between
    the menu scene and the simulation scene.
    """

    FPS: int = 30

    def __init__(self) -> None:
        """Initializes the application window and clock."""
        pygame.init()
        pygame.display.set_caption("ACOSXM - Moore Neighborhood Cellular Automaton")

        # Ventana redimensionable
        self.screen: pygame.Surface = pygame.display.set_mode(
            (0, 0),
            pygame.RESIZABLE
        )

    def run(self) -> None:
        """Starts the application by running the menu and then the simulation."""
        while True:
            menu = MenuScene(self.screen)
            width, height = menu.run()

            sim = SimulationScene(self.screen, width, height)
            sim.run()
