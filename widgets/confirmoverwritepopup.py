import pygame

from widgets.popup import Popup
from widgets.button import Button


class ConfirmOverwritePopup(Popup):

    def __init__(self, rect):

        super().__init__(rect, "Rule already exists")

        self.rule_name = ""

        self.result = None

        self.btn_overwrite = Button(
            (
                self.rect.x + 20,
                self.rect.bottom - 60,
                140,
                32
            ),
            "Overwrite"
        )

        self.btn_cancel = Button(
            (
                self.rect.x + 180,
                self.rect.bottom - 60,
                140,
                32
            ),
            "Cancel"
        )

    def open(self, rule_name):

        self.rule_name = rule_name

        self.result = None

        self.visible = True

    def handle_event(self, ev):

        if not self.visible:
            return None

        if super().handle_event(ev):
            return None

        if ev.type == pygame.KEYDOWN:

            if ev.key == pygame.K_ESCAPE:

                self.result = False

                self.close()

                return False

        if self.btn_overwrite.handle_event(ev):

            self.result = True

            self.close()

            return True

        if self.btn_cancel.handle_event(ev):

            self.result = False

            self.close()

            return False

        return None

    def draw(self, screen):

        super().draw(screen)

        if not self.visible:
            return

        text1 = self.fn.render(
            "A rule with this name already exists.",
            True,
            self.title_color
        )

        screen.blit(
            text1,
            (
                self.rect.x + 20,
                self.rect.y + 70
            )
        )

        text2 = self.fn.render(
            f'"{self.rule_name}"',
            True,
            self.title_color
        )

        screen.blit(
            text2,
            (
                self.rect.x + 20,
                self.rect.y + 95
            )
        )

        text3 = self.fn.render(
            "Do you want to overwrite it?",
            True,
            self.title_color
        )

        screen.blit(
            text3,
            (
                self.rect.x + 20,
                self.rect.y + 125
            )
        )

        self.btn_overwrite.draw(
            screen,
            self.fn
        )

        self.btn_cancel.draw(
            screen,
            self.fn
        )