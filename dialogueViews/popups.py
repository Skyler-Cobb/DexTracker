# dialogueViews/popups.py
import pygame
from config import SILHOUETTE_COLORS, FONT_REGULAR

POPUP_BG_COLOR = (240, 240, 240)
POPUP_BORDER_COLOR = (0, 0, 0)

class PopupManager:
    def __init__(self, parent_rect, parent_dialog):
        self.parent_dialog = parent_dialog
        self.popup_rect = pygame.Rect(
            parent_rect.centerx - 150,
            parent_rect.centery - 100,
            300,
            200
        )
        self.active_popup = None  # Can be "Origin", "Source", or "Color"

    def show_popup(self, which):
        self.active_popup = which

    def hide_all(self):
        self.active_popup = None

    def is_active(self):
        return self.active_popup is not None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.popup_rect.collidepoint(event.pos):
                self.hide_all()
            else:
                if self.active_popup in ["Origin", "Source"]:
                    self._handle_popup_icons(event.pos)
                elif self.active_popup == "Color":
                    self._handle_popup_color(event.pos)

    def draw(self, screen):
        if not self.is_active():
            return
        pygame.draw.rect(screen, POPUP_BG_COLOR, self.popup_rect)
        pygame.draw.rect(screen, POPUP_BORDER_COLOR, self.popup_rect, 2)
        if self.active_popup == "Origin":
            title = "Select Origin Mark"
        elif self.active_popup == "Source":
            title = "Select Source Mark"
        else:
            title = "Select Color"
        title_surf = pygame.font.Font(FONT_REGULAR, 20).render(title, True, (0, 0, 0))
        title_rect = title_surf.get_rect(center=(self.popup_rect.centerx, self.popup_rect.y + 15))
        screen.blit(title_surf, title_rect)
        if self.active_popup in ["Origin", "Source"]:
            images_dict = self.parent_dialog.origin_mark_images if self.active_popup == "Origin" else self.parent_dialog.source_mark_images
            self._draw_popup_icons(screen, list(images_dict.keys()), images_dict)
        elif self.active_popup == "Color":
            self._draw_popup_color(screen)

    def _handle_popup_icons(self, click_pos):
        icon_size = 40
        gap = 10
        cols = 5
        x_start = self.popup_rect.x + 10
        y_start = self.popup_rect.y + 40
        col = row = 0
        images_dict = self.parent_dialog.origin_mark_images if self.active_popup == "Origin" else self.parent_dialog.source_mark_images
        for fn in list(images_dict.keys()):
            rx = x_start + col * (icon_size + gap)
            ry = y_start + row * (icon_size + gap)
            r = pygame.Rect(rx, ry, icon_size, icon_size)
            if r.collidepoint(click_pos):
                # Clear mark if special filename.
                if fn in ["error.png", "REMOVE.png"]:
                    import dex_adapter
                    if self.active_popup == "Origin":
                        dex_adapter.set_origin_mark(self.parent_dialog.selected_pokemon_id, None)
                    else:
                        if hasattr(dex_adapter, "set_source_mark"):
                            dex_adapter.set_source_mark(self.parent_dialog.selected_pokemon_id, None)
                else:
                    import dex_adapter
                    if self.active_popup == "Origin":
                        dex_adapter.set_origin_mark(self.parent_dialog.selected_pokemon_id, fn)
                    else:
                        if hasattr(dex_adapter, "set_source_mark"):
                            dex_adapter.set_source_mark(self.parent_dialog.selected_pokemon_id, fn)
                self.hide_all()
                return
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def _handle_popup_color(self, click_pos):
        swatch = 30
        gap = 10
        cols = 4
        x_start = self.popup_rect.x + 10
        y_start = self.popup_rect.y + 40
        col = row = 0
        for i, col_val in enumerate(SILHOUETTE_COLORS):
            rx = x_start + col * (swatch + gap)
            ry = y_start + row * (swatch + gap)
            r = pygame.Rect(rx, ry, swatch, swatch)
            if r.collidepoint(click_pos):
                import dex_adapter
                dex_adapter.set_silhouette_color_index(self.parent_dialog.selected_pokemon_id, i)
                self.hide_all()
                return
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def _draw_popup_icons(self, screen, options, images_dict):
        icon_size = 40
        gap = 10
        cols = 5
        x_start = self.popup_rect.x + 10
        y_start = self.popup_rect.y + 40
        col = row = 0
        for fn in options:
            rx = x_start + col * (icon_size + gap)
            ry = y_start + row * (icon_size + gap)
            r = pygame.Rect(rx, ry, icon_size, icon_size)
            if fn in images_dict:
                img = images_dict[fn]
                scaled = pygame.transform.smoothscale(img, (icon_size, icon_size))
                screen.blit(scaled, r)
            col += 1
            if col >= cols:
                col = 0
                row += 1

    def _draw_popup_color(self, screen):
        swatch = 30
        gap = 10
        cols = 4
        x_start = self.popup_rect.x + 10
        y_start = self.popup_rect.y + 40
        col = row = 0
        for i, col_val in enumerate(SILHOUETTE_COLORS):
            rx = x_start + col * (swatch + gap)
            ry = y_start + row * (swatch + gap)
            r = pygame.Rect(rx, ry, swatch, swatch)
            pygame.draw.rect(screen, col_val, r)
            pygame.draw.rect(screen, (0,0,0), r, 1)
            col += 1
            if col >= cols:
                col = 0
                row += 1
