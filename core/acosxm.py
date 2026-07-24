import pygame
from core import config
from scenes.menuscene import MenuScene
from scenes.simulationscene import SimulationScene
from ui.dialogs.settings_popup import load_settings, apply_music_volume


class ACOSXM:
    """Main application entry point for the ACOSXM cellular automaton.

    Manages the game loop, screen, clock, and transitions between
    the menu scene and the simulation scene.
    """

    FPS: int = 30

    def __init__(self) -> None:
        """Initializes the application window and clock."""
        pygame.init()

        # Background music (loops forever)
        try:
            settings = load_settings()
            pygame.mixer.music.load("assets/music/Far.mp3")
            apply_music_volume(settings.get("music_volume", 0.5))
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[WARN] Could not start background music: {e}")

        pygame.display.set_caption("ACOSXM - Moore Neighborhood Cellular Automaton")

        # Resizable window
        self.screen: pygame.Surface = pygame.display.set_mode(
            (0, 0),
            pygame.RESIZABLE
        )

    def run(self) -> None:
        """Starts the application by running the menu and then the simulation."""
        width = 100
        height = 100
        bg_cells = None
        while True:
            menu = MenuScene(self.screen, width, height, bg_cells)
            width, height, bg_cells = menu.run()

            sim = SimulationScene(self.screen, width, height, bg_cells)
            bg_cells = sim.run()
