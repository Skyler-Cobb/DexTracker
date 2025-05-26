# dialogueViews/base_view.py
import pygame

class BaseView:
    def __init__(self, parent_dialog):
        self.parent = parent_dialog

    def refresh(self):
        """
        Called when the main dialog state changes (for example, when a new Pokémon is loaded).
        """
        pass

    def handle_event(self, event):
        """
        Process events specific to this view.
        Return True if the event was handled.
        """
        return False

    def draw(self, screen, start_y):
        """
        Draw the view’s content starting at the given Y-coordinate.
        """
        pass
