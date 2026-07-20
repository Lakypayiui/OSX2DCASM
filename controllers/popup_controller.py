import pygame
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from core.life2dm import Life2DM
from core.rule_matrix import RuleMatrix
from ui.dialogs import (
    ConfirmOverwritePopup,
    LoadRulePopup,
    LoadSimulationPopup,
    SaveRulePopup,
    SaveSimulationPopup,
)
from widgets.popup import Popup

class PopupResultType(Enum):
    LOAD_RULE = auto()
    SAVE_RULE = auto()
    LOAD_SIMULATION = auto()
    SAVE_SIMULATION = auto()
    CONFIRM_OVERWRITE = auto()

@dataclass
class PopupResult:
    type: PopupResultType
    data: object = None

class PopupController:

    POPUP_WIDTH = 500
    POPUP_HEIGHT = 400

    def __init__(
        self,
        screen: pygame.Surface,
        rule_matrix: RuleMatrix,
        life: Life2DM
    ) -> None:
        """Initializes the popup controller.

        Args:
            screen: Main application surface.
            rule_matrix: Rule matrix used by rule-related dialogs.
        """
        self.screen = screen
        self.rule_matrix = rule_matrix
        self.life = life

        self.popup_stack: list[Popup] = []

        self._create_popups()


    def _popup_rect(self) -> tuple[int, int, int, int]:
        """Returns the centered rectangle used by popup dialogs.

        Returns:
            Rectangle in the form (x, y, width, height).
        """
        return (
            (self.screen.get_width() - self.POPUP_WIDTH) // 2,
            (self.screen.get_height() - self.POPUP_HEIGHT) // 2,
            self.POPUP_WIDTH,
            self.POPUP_HEIGHT,
        )

    def _create_popups(self) -> None:
        """Creates all dialogs managed by the controller."""

        rect = self._popup_rect()

        self.load_rule = LoadRulePopup(rect)

        self.save_rule = SaveRulePopup(
            rect,
            self.rule_matrix.to_rule_array(),
        )

        self.confirm = ConfirmOverwritePopup(
            rect,
            "File",
        )

        self.save_state = SaveSimulationPopup(
            rect,
            self.life
        )

        self.load_state = LoadSimulationPopup(rect)
    
    def push(self, popup: Popup) -> None:
        popup.open()
        self.popup_stack.append(popup)

    def pop(self) -> None:
        if self.popup_stack:
            self.popup_stack.pop().close()

    @property
    def current_popup(self) -> Optional[Popup]:
        if not self.popup_stack:
            return None

        return self.popup_stack[-1]

    @property
    def has_popup(self) -> bool:
        """Returns whether any popup is currently open."""
        return bool(self.popup_stack)

    def handle_event(self, event: pygame.event.Event) ->  Optional[PopupResult]:
        """Processes an event for the active popup.

        The event is forwarded only to the currently active popup. If the popup
        completes an action (for example, loading a rule or saving a simulation),
        the result is wrapped in a ``PopupResult`` object so the caller can decide
        how to handle it.

        Args:
            event: Pygame event to process.

        Returns:
            A ``PopupResult`` describing the completed popup action, or ``None``
            if no popup is active or the event does not produce any result.
        """

        if self.current_popup is None:
            return None

        result = self.current_popup.handle_event(event)


        if result is None:
            return None

        if self.current_popup is self.load_rule:
            return PopupResult(
                PopupResultType.LOAD_RULE,
                result
            )

        if self.current_popup is self.load_state:
            return PopupResult(
                PopupResultType.LOAD_SIMULATION,
                result
            )

        if self.current_popup is self.save_rule:
            return PopupResult(
                PopupResultType.SAVE_RULE,
                result
            )

        if self.current_popup is self.save_state:
            return PopupResult(
                PopupResultType.SAVE_SIMULATION,
                result
            )

        if self.current_popup is self.confirm:
            return PopupResult(
                PopupResultType.CONFIRM_OVERWRITE,
                result
            )

        return None

       

    def draw(self) -> None:
        """Draws all visible popups."""

        for popup in self.popup_stack:
            popup.draw(self.screen)