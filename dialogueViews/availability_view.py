# dialogueViews/availability_view.py
import os
import pygame
import numpy as np
import pygame.surfarray
from .base_view import BaseView
import dex_adapter
from config import GAMES  # Direct path to game images

# Adjust this constant to scale the grid images and gaps.
GRID_SCALE = 1.0  # Increase for larger icons; decrease for more compact grid.

class AvailabilityView(BaseView):
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        # Scrolling variable.
        self.scroll_offset = 0

        # Base sizes (at GRID_SCALE=1.0) for icons and gaps.
        self.base_icon_size = 70    # Base size for each game icon.
        self.base_icon_gap = 15     # Gap between icons.
        
        # Use the GAMES path imported from config.
        self.games_dir = GAMES

        # Define the order of games using groups (order is preserved but not displayed).
        # You can adjust these groups as needed; they are only used for ordering.
        self.game_groups = [
            ("Gen 1", [["red", "blue", "yellow"]]),
            ("Gen 2", [["gold", "silver", "crystal"]]),
            ("Gen 3", [["ruby", "sapphire", "emerald"], ["firered", "leafgreen"], ["colosseum", "xd"]]),
            ("Gen 4", [["diamond", "pearl", "platinum"], ["heartgold", "soulsilver"]]),
            ("Gen 5", [["black", "white"], ["black2", "white2"]]),
            ("Gen 6", [["x", "y"], ["omegaruby", "alphasapphire"]]),
            ("Gen 7", [["sun", "moon"], ["ultrasun", "ultramoon"], ["letsgopikachu", "letsgoeevee"]]),
            ("Gen 8", [["sword", "shield", "swsh-dlc"], ["brilliantdiamond", "shiningpearl"], ["legendsarceus"]]),
            ("Gen 9", [["scarlet", "violet", "sv-dlc"]]),
            ("Misc", [["pokewalker", "dreamradar", "dreamworld", "go", "home"]])
        ]
        # Flatten the game IDs from our groups into a single list in the desired order.
        self.all_game_ids = []
        for _, rows in self.game_groups:
            for row in rows:
                for game_id in row:
                    self.all_game_ids.append(game_id)

        # Pre-load game icons.
        self.icons = {}  # game_id -> pygame.Surface (scaled icon)
        for game_id in self.all_game_ids:
            # Try .png first, then .jpg.
            path_png = os.path.join(self.games_dir, f"{game_id}.png")
            path_jpg = os.path.join(self.games_dir, f"{game_id}.jpg")
            image = None
            if os.path.exists(path_png):
                try:
                    image = pygame.image.load(path_png).convert_alpha()
                except Exception:
                    image = None
            elif os.path.exists(path_jpg):
                try:
                    image = pygame.image.load(path_jpg).convert_alpha()
                except Exception:
                    image = None
            if image:
                self.icons[game_id] = pygame.transform.smoothscale(
                    image, (int(self.base_icon_size * GRID_SCALE), int(self.base_icon_size * GRID_SCALE))
                )
            else:
                self.icons[game_id] = None

        # For detecting clicks, store icon rects as a list of tuples (rect, game_id).
        self.icon_rects = []

        # Popup for catch methods.
        self.popup_methods = None  # When not None, a popup is active (list of method strings).
        self.popup_game = None     # The game_id for which the popup is active.
        self.popup_rect = None     # Defined when drawing the popup.

    def refresh(self):
        # Called when a new Pokémon is loaded.
        self.scroll_offset = 0
        self.icon_rects = []
        self.popup_methods = None
        self.popup_game = None

    def handle_event(self, event):
        # Handle scrolling using mouse wheel events.
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up.
                self.scroll_offset = min(self.scroll_offset + 20, 0)
                return True
            elif event.button == 5:  # Scroll down.
                self.scroll_offset -= 20
                return True

            # If a popup is active, dismiss it on click outside.
            if self.popup_methods is not None and self.popup_rect:
                if not self.popup_rect.collidepoint(event.pos):
                    self.popup_methods = None
                    self.popup_game = None
                    return True
                else:
                    # (Further popup interaction can be added here.)
                    return True

            # Check for clicks on game icons.
            for rect, game_id in self.icon_rects:
                if rect.collidepoint(event.pos):
                    # Normalize availability data.
                    available_games_raw = getattr(self.parent.pokemon_info, "games", [])
                    available_games = set()
                    for entry in available_games_raw:
                        name = entry.get("game", "").lower().replace("-", "").replace(" ", "")
                        available_games.add(name)
                    norm_game = game_id.lower().replace("-", "").replace(" ", "")
                    if norm_game in available_games:
                        # Retrieve catch methods (using our dex_adapter function).
                        methods = dex_adapter.get_catch_methods(self.parent.selected_pokemon_id, game_id)
                        self.popup_methods = methods
                        self.popup_game = game_id
                        return True
        return False

    def draw(self, screen, start_y):
        # Calculate effective sizes based on GRID_SCALE.
        icon_size = int(self.base_icon_size * GRID_SCALE)
        icon_gap = int(self.base_icon_gap * GRID_SCALE)
        self.icon_rects = []  # Reset each draw call.

        # Define a scrollable area within the dialog.
        scroll_area = pygame.Rect(
            self.parent.dialog_rect.x + 20,
            start_y,
            self.parent.dialog_rect.width - 40,
            self.parent.dialog_rect.bottom - start_y - 20
        )
        # Set clipping to the scroll area.
        prev_clip = screen.get_clip()
        screen.set_clip(scroll_area)

        # Normalize available games from the Pokémon's data.
        available_games_raw = getattr(self.parent.pokemon_info, "games", [])
        available_games = set()
        for entry in available_games_raw:
            name = entry.get("game", "").lower().replace("-", "").replace(" ", "")
            available_games.add(name)

        # Determine number of columns that fit in the scroll area.
        col_count = max(1, (scroll_area.width + icon_gap) // (icon_size + icon_gap))
        total_grid_width = col_count * (icon_size + icon_gap) - icon_gap
        grid_x_start = scroll_area.x + (scroll_area.width - total_grid_width) // 2

        # Draw each game icon in a grid.
        for i, game_id in enumerate(self.all_game_ids):
            col = i % col_count
            row = i // col_count
            x = grid_x_start + col * (icon_size + icon_gap)
            y_pos = start_y + row * (icon_size + icon_gap) + self.scroll_offset
            icon = self.icons.get(game_id)
            if icon is None:
                continue
            norm_game = game_id.lower().replace("-", "").replace(" ", "")
            if norm_game in available_games:
                draw_icon = icon
            else:
                draw_icon = self.convert_to_grayscale(icon)
            rect = pygame.Rect(x, y_pos, icon_size, icon_size)
            screen.blit(draw_icon, rect)
            self.icon_rects.append((rect, game_id))

        # Restore previous clipping.
        screen.set_clip(prev_clip)
        # Draw a border for the scroll area.
        pygame.draw.rect(screen, (0, 0, 0), scroll_area, 2)

        # If a popup is active, draw it.
        if self.popup_methods is not None:
            self.draw_popup(screen)

        return scroll_area.bottom

    def draw_popup(self, screen):
        # Draw a popup window listing catch methods.
        popup_width = 300
        popup_height = 200
        popup_x = self.parent.dialog_rect.centerx - popup_width // 2
        popup_y = self.parent.dialog_rect.centery - popup_height // 2
        self.popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(screen, (240, 240, 240), self.popup_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.popup_rect, 2)

        # Draw title.
        title_font = self.parent.main_font
        title_text = f"Catch Methods for {self.popup_game.capitalize()}"
        title_surf = title_font.render(title_text, True, (0, 0, 0))
        title_rect = title_surf.get_rect(centerx=self.popup_rect.centerx, top=self.popup_rect.y + 10)
        screen.blit(title_surf, title_rect)

        # List the catch methods.
        method_font = self.parent.small_font
        y_text = title_rect.bottom + 10
        if self.popup_methods:
            for method in self.popup_methods:
                method_surf = method_font.render(method, True, (0, 0, 0))
                screen.blit(method_surf, (self.popup_rect.x + 10, y_text))
                y_text += method_surf.get_height() + 5
        else:
            none_surf = method_font.render("None", True, (0, 0, 0))
            screen.blit(none_surf, (self.popup_rect.x + 10, y_text))

    def convert_to_grayscale(self, surface):
        """
        Convert a pygame Surface to a darkened grayscale version.
        """
        arr = pygame.surfarray.array3d(surface).astype('float')
        luminance = (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2])
        gray_arr = np.stack((luminance,) * 3, axis=-1).astype('uint8')
        gray_surface = pygame.surfarray.make_surface(gray_arr)
        dark_surface = gray_surface.copy()
        dark_surface.fill((50, 50, 50), special_flags=pygame.BLEND_MULT)
        return dark_surface
