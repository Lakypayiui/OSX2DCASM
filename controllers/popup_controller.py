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
    """Enumeration of popup result types."""
    LOAD_RULE = auto()
    SAVE_RULE = auto()
    LOAD_SIMULATION = auto()
    SAVE_SIMULATION = auto()
    CONFIRM_OVERWRITE = auto()

@dataclass
class PopupResult:
    """Stores the result of a popup action.

    Attributes:
        type: The type of popup action that completed.
        data: Additional data returned by the popup.
    """
    type: PopupResultType
    data: object = None

class PopupController:
    """Manages a stack of popup dialogs for the simulation scene."""

    POPUP_WIDTH: int = 500
    POPUP_HEIGHT: int = 400

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
            life: Life2DM automaton used by simulation-related dialogs.
        """
        self.screen: pygame.Surface = screen
        self.rule_matrix: RuleMatrix = rule_matrix
        self.life: Life2DM = life

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

        rect: tuple[int, int, int, int] = self._popup_rect()

        self.load_rule: LoadRulePopup = LoadRulePopup(rect)

        self.save_rule: SaveRulePopup = SaveRulePopup(
            rect,
            self.rule_matrix.to_rule_array(),
        )

        self.confirm: ConfirmOverwritePopup = ConfirmOverwritePopup(
            rect,
            "File",
        )

        self.save_state: SaveSimulationPopup = SaveSimulationPopup(
            rect,
            self.life
        )

        self.load_state: LoadSimulationPopup = LoadSimulationPopup(rect)
    
    def push(self, popup: Popup) -> None:
        """Pushes a popup onto the stack and opens it.

        Args:
            popup: The popup dialog to push.
        """
        popup.open()
        self.popup_stack.append(popup)

    def pop(self) -> None:
        """Pops the topmost popup from the stack and closes it."""
        if self.popup_stack:
            self.popup_stack.pop().close()

    @property
    def current_popup(self) -> Optional[Popup]:
        """Returns the currently active popup, if any.

        Returns:
            The topmost popup on the stack, or ``None`` if the stack is empty.
        """
        if not self.popup_stack:
            return None

        return self.popup_stack[-1]

    @property
    def has_popup(self) -> bool:
        """Returns whether any popup is currently open."""
        return bool(self.popup_stack)

    def handle_event(self, event: pygame.event.Event) -> Optional[PopupResult]:
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

        result: object = self.current_popup.handle_event(event)


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
