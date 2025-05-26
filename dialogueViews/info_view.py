# dialogueViews/info_view.py
import pygame
from .base_view import BaseView

class InfoView(BaseView):
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)

    def refresh(self):
        pass

    def handle_event(self, event):
        # Info view does not process specific events.
        return False

    def draw(self, screen, start_y):
        y = start_y + 10
        label = self.parent.main_font.render("Base Stats:", True, (0,0,0))
        screen.blit(label, (self.parent.dialog_rect.x+20, y))
        y += label.get_height() + 10
        if not self.parent.pokemon_info:
            return y
        stats = getattr(self.parent.pokemon_info, "stats", {})
        left_keys = ["atk", "def", "hp"]
        right_keys = ["sp.atk", "sp.def", "spd"]
        row_h = self.parent.main_font.get_height() + 5
        col_left_x = self.parent.dialog_rect.x + 40
        col_right_x = self.parent.dialog_rect.x + self.parent.dialog_rect.width//2 + 20
        y_left = y
        for k in left_keys:
            val = stats.get(k, 0)
            s = self.parent.main_font.render(f"{k.upper()}: {val}", True, (0,0,0))
            screen.blit(s, (col_left_x, y_left))
            y_left += row_h
        y_right = y
        for k in right_keys:
            key_name = k.replace(".", "")
            val = stats.get(key_name, 0)
            s = self.parent.main_font.render(f"{k.upper()}: {val}", True, (0,0,0))
            screen.blit(s, (col_right_x, y_right))
            y_right += row_h
        return max(y_left, y_right) + 10
