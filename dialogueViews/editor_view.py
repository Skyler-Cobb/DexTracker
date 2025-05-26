# dialogueViews/editor_view.py
import pygame
from .base_view import BaseView
import dex_adapter

class EditorView(BaseView):
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.editor_buttons = {}
        self.button_size = 50  # Increased button size.
        self.gap = 15          # Increased gap between buttons.

    def refresh(self):
        # Refresh any editor-specific state if necessary.
        pass

    def handle_event(self, event):
        if self.parent.current_page != "Editor":
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for key, rect in self.editor_buttons.items():
                if rect.collidepoint(event.pos):
                    self._click_editor_button(key)
                    return True
        return False

    def _click_editor_button(self, key):
        if key == "Caught":
            new_val = not self.parent.caught_state
            dex_adapter.toggle_pokemon_caught(self.parent.selected_pokemon_id)
            self.parent.caught_state = new_val
        elif key == "Lock":
            new_val = not self.parent.locked_state
            dex_adapter.set_pokemon_locked(self.parent.selected_pokemon_id, new_val)
            self.parent.locked_state = new_val
        elif key in ["Origin", "Source", "Color"]:
            self.parent.popup_manager.show_popup(key)

    def draw(self, screen, start_y):
        total_w = 5 * self.button_size + 4 * self.gap
        x_start = self.parent.dialog_rect.centerx - total_w // 2
        y = start_y + 10
        self.editor_buttons.clear()

        for key in ["Caught", "Lock", "Origin", "Source", "Color"]:
            rect = pygame.Rect(x_start, y, self.button_size, self.button_size)
            self._draw_editor_icon_button(screen, rect, key)
            self.editor_buttons[key] = rect
            x_start += self.button_size + self.gap

        return y + self.button_size + 20

    def _draw_editor_icon_button(self, screen, rect, key):
        pygame.draw.rect(screen, (200, 200, 200), rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)
        padding = 6  # Adjust padding for larger buttons.

        if key == "Caught":
            if self.parent.caught_state and self.parent.flag_image:
                scaled = pygame.transform.smoothscale(
                    self.parent.flag_image,
                    (rect.width - 2 * padding, rect.height - 2 * padding)
                )
                r = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - 2 * padding, rect.height - 2 * padding)
                screen.blit(scaled, r)
        elif key == "Lock":
            if self.parent.lock_image:
                icon = self.parent.lock_image.get(self.parent.locked_state)
                if icon:
                    scaled = pygame.transform.smoothscale(
                        icon,
                        (rect.width - 2 * padding, rect.height - 2 * padding)
                    )
                    r = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - 2 * padding, rect.height - 2 * padding)
                    screen.blit(scaled, r)
        elif key == "Origin":
            omark = dex_adapter.get_origin_mark(self.parent.selected_pokemon_id)
            if omark and omark in self.parent.origin_mark_images:
                icon = self.parent.origin_mark_images[omark]
                scaled = pygame.transform.smoothscale(
                    icon,
                    (rect.width - 2 * padding, rect.height - 2 * padding)
                )
                r = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - 2 * padding, rect.height - 2 * padding)
                screen.blit(scaled, r)
        elif key == "Source":
            if hasattr(dex_adapter, "get_source_mark"):
                smark = dex_adapter.get_source_mark(self.parent.selected_pokemon_id)
                if smark and smark in self.parent.source_mark_images:
                    icon = self.parent.source_mark_images[smark]
                    scaled = pygame.transform.smoothscale(
                        icon,
                        (rect.width - 2 * padding, rect.height - 2 * padding)
                    )
                    r = pygame.Rect(rect.x + padding, rect.y + padding, rect.width - 2 * padding, rect.height - 2 * padding)
                    screen.blit(scaled, r)
        elif key == "Color":
            idx = dex_adapter.get_silhouette_color_index(self.parent.selected_pokemon_id)
            from config import SILHOUETTE_COLORS
            if 0 <= idx < len(SILHOUETTE_COLORS):
                color_val = SILHOUETTE_COLORS[idx]
                pygame.draw.rect(
                    screen,
                    color_val,
                    (rect.x + padding, rect.y + padding, rect.width - 2 * padding, rect.height - 2 * padding)
                )
            pygame.draw.rect(screen, (0, 0, 0), rect, 2)
