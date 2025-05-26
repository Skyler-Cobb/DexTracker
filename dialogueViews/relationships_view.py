"""
relationships_view.py

Displays a Pokémon’s evolutionary and alternate form relationships.
The Evolutions section now shows at least one icon (the current Pokémon’s sprite if no evolutions exist).
For both Evolutions and Forms, an outline is drawn around the icon that represents the currently active Pokémon.
The outline is drawn in dark gray and is slightly larger than the icon to provide padding.
"""

import os
import pygame
from .base_view import BaseView
import dex_adapter
import assets  # For loading form symbol images.
import data    # For get_form_items and access to all items.

from config import FONT_REGULAR, FORM_MARKS

# Constants
OUTLINE_COLOR = (60, 60, 60)
OUTLINE_PADDING = 6          # Extra padding for outline.
OUTLINE_THICKNESS = 3        # Thickness of the outline.
SCROLL_STEP = 10             # Base step (in pixels) for target offset adjustments.
SCROLL_SPEED = 15.0          # Scroll speed in pixels per second for smooth interpolation.
ICON_SIZE = 50               # Size for form icons.
ICON_GAP = 10                # Gap between icons.
BUTTON_WIDTH = 60            # Width of the "..." button area.
SCROLLBAR_HEIGHT = 6         # Height of the horizontal scroll bar.
SCROLLBAR_MARGIN = 2         # Space between icon area and scroll bar.
KEY_SCROLL_SPEED = 200       # Pixels per second when arrow keys are held down.

class RelationshipsView(BaseView):
    """
    Displays evolution and form icons.

    - Evolutions and forms are clickable icons.
    - Icons are stored as (pygame.Rect, id) tuples.
    """
    def __init__(self, parent_dialog):
        super().__init__(parent_dialog)
        self.evolution_icon_rects = []  # (pygame.Rect, evolution_id)
        self.form_icon_rects = []       # For form icons in the visible (scroll) area.
        # Scrolling variables.
        self.form_scroll_offset = 0     # Current scroll offset (pixels).
        self.target_scroll_offset = 0   # Target scroll offset (pixels).
        self.forms_area_button_rect = None  # Rectangle for the "..." button.
        self.forms_popup_active = False
        self.popup_form_icon_rects = []
        self.popup_rect = None          # Popup rectangle when active.
        self._forms_area_rect = None    # The visible rectangle for icons (for event handling).
        self.last_update_time = pygame.time.get_ticks()  # For time‑based interpolation.

        # Cache for form images to avoid expensive operations every frame.
        self.cached_form_images = []
        self.cached_form_images_scaled = []

        # New variables for scroll bar dragging.
        self.dragging_scroll = False
        self.scroll_drag_start_x = 0
        self.initial_scroll_offset = 0
        self.scroll_handle_rect = None
        self.scroll_track_rect = None
        self._max_scroll = 0
        self._scroll_track_width = 0

    def refresh(self):
        """Reset state when a new Pokémon is loaded."""
        self.form_scroll_offset = 0
        self.target_scroll_offset = 0
        self.forms_popup_active = False
        self.evolution_icon_rects = []
        self.form_icon_rects = []
        self.popup_form_icon_rects = []
        self.last_update_time = pygame.time.get_ticks()

        # Cache form images and pre-scale them to avoid repeated scaling every frame.
        pokemon_name = getattr(self.parent.pokemon_info, "name", "")
        self.cached_form_images = assets.load_form_symbols(pokemon_name)
        if self.cached_form_images:
            self.cached_form_images_scaled = [
                pygame.transform.smoothscale(img, (ICON_SIZE, ICON_SIZE))
                for img in self.cached_form_images
            ]
        else:
            self.cached_form_images_scaled = []

    def handle_event(self, event):
        """
        Process events for evolutions and forms.
        - Mouse wheel, arrow keys, and scroll bar dragging update the target scroll offset.
        - Clicking in the "..." button area is prioritized.
        - Only icons that are fully visible within the icons area are clickable.
        """
        if self.parent.current_page != "Relationships":
            return False

        # --- Scroll Bar Dragging Handling ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # If the scroll bar handle was clicked, start dragging.
            if self.scroll_handle_rect and self.scroll_handle_rect.collidepoint(event.pos):
                self.dragging_scroll = True
                self.scroll_drag_start_x = event.pos[0]
                self.initial_scroll_offset = self.target_scroll_offset
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_scroll:
                self.dragging_scroll = False
                return True
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging_scroll and self.scroll_track_rect:
                dx = event.pos[0] - self.scroll_drag_start_x
                if self._scroll_track_width > 0:
                    new_target = self.initial_scroll_offset + (dx / self._scroll_track_width) * self._max_scroll
                    new_target = max(0, min(new_target, self._max_scroll))
                    self.target_scroll_offset = new_target
                    return True

        # --- Delegate to popup if active ---
        if self.forms_popup_active:
            if self.handle_forms_popup_event(event):
                return True

        # --- Mouse wheel scrolling ---
        if event.type == pygame.MOUSEWHEEL:
            mouse_pos = pygame.mouse.get_pos()
            if self._forms_area_rect and self._forms_area_rect.collidepoint(mouse_pos):
                total_forms_width = len(self.cached_form_images_scaled) * ICON_SIZE + (len(self.cached_form_images_scaled) - 1) * ICON_GAP
                available_width = self._forms_area_rect.width
                max_scroll = max(0, total_forms_width - available_width)
                # event.y is positive for scroll-up.
                self.target_scroll_offset = max(0, min(max_scroll, self.target_scroll_offset - event.y * SCROLL_STEP))
                return True

        # --- Arrow-key events (single press fallback) ---
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.target_scroll_offset = max(0, self.target_scroll_offset - SCROLL_STEP)
                return True
            elif event.key == pygame.K_RIGHT:
                total_forms_width = len(self.cached_form_images_scaled) * ICON_SIZE + (len(self.cached_form_images_scaled) - 1) * ICON_GAP
                available_width = self._forms_area_rect.width if self._forms_area_rect else 0
                max_scroll = max(0, total_forms_width - available_width)
                self.target_scroll_offset = min(max_scroll, self.target_scroll_offset + SCROLL_STEP)
                return True

        # --- Process mouse clicks on icons ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            # Priority: check for "..." button clicks.
            if self.forms_area_button_rect and self.forms_area_button_rect.collidepoint(pos):
                self.forms_popup_active = True
                return True
            # Check evolution icons.
            for (rect, evo_id) in self.evolution_icon_rects:
                if rect.collidepoint(pos):
                    self.parent.open(evo_id, keep_tab=True)
                    return True
            # Check form icons (only if fully visible).
            if self._forms_area_rect:
                for (rect, form_id) in self.form_icon_rects:
                    if self._forms_area_rect.contains(rect) and rect.collidepoint(pos):
                        if form_id is not None:
                            self.parent.open(form_id, keep_tab=True)
                        return True
        return False

    def draw(self, screen, start_y):
        """
        Draw Evolutions and Forms sections.
        Updates the scroll offset smoothly (time‑based) before drawing forms.
        """
        y = start_y + 10
        self.evolution_icon_rects = []

        # --- Evolutions Section ---
        evol = getattr(self.parent.pokemon_info, "evolutions", [])
        if not (isinstance(evol, list) and len(evol) > 1):
            evol = [self.parent.selected_pokemon_id]

        evolution_label = self.parent.main_font.render("Evolutions:", True, (0, 0, 0))
        label_x = self.parent.dialog_rect.x + 20
        screen.blit(evolution_label, (label_x, y))
        y += evolution_label.get_height() + 5

        total_evo_width = len(evol) * ICON_SIZE + (len(evol) - 1) * ICON_GAP
        start_x = self.parent.dialog_rect.centerx - total_evo_width // 2

        for evo in evol:
            evo_id = evo.get("id") if isinstance(evo, dict) else evo
            if not evo_id:
                continue
            evo_info = dex_adapter.get_pokemon_info(evo_id)
            evo_gender = getattr(evo_info, "cosmetic_gender_diff", False) and self.parent.female_state
            try:
                sprite = dex_adapter.load_sprite(evo_id,
                                                 shiny=self.parent.shiny_state,
                                                 female=evo_gender,
                                                 caught=True)
            except Exception:
                continue
            scaled_sprite = pygame.transform.smoothscale(sprite, (ICON_SIZE, ICON_SIZE))
            rect = pygame.Rect(start_x, y, ICON_SIZE, ICON_SIZE)
            screen.blit(scaled_sprite, rect)
            if str(evo_id) == str(self.parent.selected_pokemon_id):
                outline_rect = rect.inflate(OUTLINE_PADDING, OUTLINE_PADDING)
                pygame.draw.rect(screen, OUTLINE_COLOR, outline_rect, OUTLINE_THICKNESS)
            self.evolution_icon_rects.append((rect, evo_id))
            start_x += ICON_SIZE + ICON_GAP

        y += ICON_SIZE + 10

        # --- Forms Section (Scrollable) ---
        self.form_icon_rects = []
        if self.cached_form_images_scaled and len(self.cached_form_images_scaled) > 1:
            form_label = self.parent.main_font.render("Forms:", True, (0, 0, 0))
            screen.blit(form_label, (self.parent.dialog_rect.x + 20, y))
            y += form_label.get_height() + 5

            forms_area_x = self.parent.dialog_rect.x + 20
            available_width = self.parent.dialog_rect.width - 40
            total_forms_width = len(self.cached_form_images_scaled) * ICON_SIZE + (len(self.cached_form_images_scaled) - 1) * ICON_GAP

            if total_forms_width > available_width:
                show_scroll = True
                scroll_area_width = available_width - BUTTON_WIDTH
            else:
                show_scroll = False
                scroll_area_width = available_width

            # Define the icons area with a light background and border.
            icons_area_rect = pygame.Rect(forms_area_x, y, scroll_area_width, ICON_SIZE)
            bg_color = (230, 230, 230)
            border_color = (180, 180, 180)
            pygame.draw.rect(screen, bg_color, icons_area_rect)
            pygame.draw.rect(screen, border_color, icons_area_rect, 1)
            self._forms_area_rect = icons_area_rect

            # --- Time-based update for scroll offset ---
            current_time = pygame.time.get_ticks()
            dt = (current_time - self.last_update_time) / 1000.0
            self.last_update_time = current_time

            # Continuous arrow-key scrolling: check current key state.
            keys = pygame.key.get_pressed()
            {
                # Calculate max scroll based on current icons area.
            }
            total_forms_width = len(self.cached_form_images_scaled) * ICON_SIZE + (len(self.cached_form_images_scaled) - 1) * ICON_GAP
            available_width = self._forms_area_rect.width
            max_scroll = max(0, total_forms_width - available_width)
            if keys[pygame.K_LEFT]:
                self.target_scroll_offset = max(0, self.target_scroll_offset - KEY_SCROLL_SPEED * dt)
            if keys[pygame.K_RIGHT]:
                self.target_scroll_offset = min(max_scroll, self.target_scroll_offset + KEY_SCROLL_SPEED * dt)

            # Interpolate current scroll offset toward target.
            diff = self.target_scroll_offset - self.form_scroll_offset
            self.form_scroll_offset += diff * min(1, dt * SCROLL_SPEED)
            if abs(diff) < 0.5:
                self.form_scroll_offset = self.target_scroll_offset

            # Set clip to icons_area_rect.
            prev_clip = screen.get_clip()
            screen.set_clip(icons_area_rect)
            icon_x = icons_area_rect.x - self.form_scroll_offset
            temp_icon_rects = []
            base_number = str(self.parent.pokemon_info.number).split('.')[0]
            all_forms = data.get_form_items(dex_adapter.get_items(), base_number)
            for idx, scaled_sprite in enumerate(self.cached_form_images_scaled):
                icon_rect = pygame.Rect(icon_x, y, ICON_SIZE, ICON_SIZE)
                screen.blit(scaled_sprite, icon_rect)
                target_id = all_forms[idx].number if idx < len(all_forms) else None
                temp_icon_rects.append((icon_rect, target_id))
                icon_x += ICON_SIZE + ICON_GAP
            screen.set_clip(prev_clip)
            self.form_icon_rects = temp_icon_rects

            # Draw outlines only for icons completely visible.
            for (icon_rect, target_id) in self.form_icon_rects:
                if target_id is not None and str(target_id) == str(self.parent.selected_pokemon_id):
                    if icons_area_rect.contains(icon_rect):
                        outline_rect = icon_rect.inflate(OUTLINE_PADDING, OUTLINE_PADDING)
                        pygame.draw.rect(screen, OUTLINE_COLOR, outline_rect, OUTLINE_THICKNESS)

            y += ICON_SIZE  # Reserve space for icons area.

            if show_scroll:
                # --- Draw Horizontal Scroll Bar ---
                scroll_bar_rect = pygame.Rect(icons_area_rect.x,
                                              icons_area_rect.bottom + SCROLLBAR_MARGIN,
                                              icons_area_rect.width,
                                              SCROLLBAR_HEIGHT)
                track_color = (200, 200, 200)
                pygame.draw.rect(screen, track_color, scroll_bar_rect)
                max_scroll = total_forms_width - icons_area_rect.width
                if max_scroll > 0:
                    visible_ratio = icons_area_rect.width / total_forms_width
                    scroll_handle_width = visible_ratio * icons_area_rect.width
                    scroll_handle_x = icons_area_rect.x + (self.form_scroll_offset / max_scroll) * (icons_area_rect.width - scroll_handle_width)
                else:
                    scroll_handle_width = icons_area_rect.width
                    scroll_handle_x = icons_area_rect.x
                handle_color = (150, 150, 150)
                # Store the scroll handle rect for dragging.
                self.scroll_handle_rect = pygame.Rect(int(scroll_handle_x),
                                                 scroll_bar_rect.y,
                                                 int(scroll_handle_width),
                                                 scroll_bar_rect.height)
                pygame.draw.rect(screen, handle_color, self.scroll_handle_rect)
                # Store scroll track rect and related metrics.
                self.scroll_track_rect = pygame.Rect(icons_area_rect.x,
                                                     scroll_bar_rect.y,
                                                     icons_area_rect.width,
                                                     scroll_bar_rect.height)
                self._max_scroll = max_scroll
                self._scroll_track_width = icons_area_rect.width - scroll_handle_width

                # Draw the separate "..." button area to the right.
                button_rect = pygame.Rect(icons_area_rect.right, y - ICON_SIZE - SCROLLBAR_MARGIN, BUTTON_WIDTH, ICON_SIZE)
                self.forms_area_button_rect = button_rect
                pygame.draw.rect(screen, bg_color, button_rect)
                pygame.draw.rect(screen, border_color, button_rect, 1)
                dots_text = self.parent.main_font.render("...", True, (0, 0, 0))
                dots_rect = dots_text.get_rect(center=button_rect.center)
                screen.blit(dots_text, dots_rect)
                y += SCROLLBAR_HEIGHT + SCROLLBAR_MARGIN + 10
            else:
                self.forms_area_button_rect = None
                y += 10  # Extra margin if no scrolling.
        else:
            self._forms_area_rect = None
            self.forms_area_button_rect = None

        # Draw popup if active.
        if self.forms_popup_active:
            self.draw_forms_popup(screen)

        return y

    def draw_forms_popup(self, screen):
        """
        Draw a modal popup dialog showing all form icons in a wrapped grid.
        The entire grid is centered both horizontally and vertically within the popup.
        """
        popup_width = self.parent.dialog_rect.width - 100
        popup_height = self.parent.dialog_rect.height - 150
        popup_x = self.parent.dialog_rect.x + 50
        popup_y = self.parent.dialog_rect.y + 75
        self.popup_rect = pygame.Rect(popup_x, popup_y, popup_width, popup_height)
        pygame.draw.rect(screen, (240, 240, 240), self.popup_rect)
        pygame.draw.rect(screen, (0, 0, 0), self.popup_rect, 2)

        title_text = self.parent.main_font.render("All Forms", True, (0, 0, 0))
        title_rect = title_text.get_rect(centerx=self.popup_rect.centerx, top=self.popup_rect.y + 10)
        screen.blit(title_text, title_rect)

        icon_size = ICON_SIZE
        gap = ICON_GAP
        available_width = self.popup_rect.width - 40  # margins
        cols = int((available_width + gap) // (icon_size + gap))
        # Partition icons into rows.
        scaled_form_images = self.cached_form_images_scaled
        base_number = str(self.parent.pokemon_info.number).split('.')[0]
        all_forms = data.get_form_items(dex_adapter.get_items(), base_number)
        rows = [scaled_form_images[i:i+cols] for i in range(0, len(scaled_form_images), cols)]
        # Compute total grid height.
        num_rows = len(rows)
        total_grid_height = num_rows * icon_size + (num_rows - 1) * gap
        # Vertically center the grid within the popup below the title.
        remaining_height = self.popup_rect.height - (title_rect.bottom + 20)
        vertical_offset = title_rect.bottom + 20 + (remaining_height - total_grid_height) / 2

        self.popup_form_icon_rects = []
        current_y = vertical_offset

        for row in rows:
            row_count = len(row)
            row_total_width = row_count * icon_size + (row_count - 1) * gap
            row_start_x = self.popup_rect.x + 20 + (available_width - row_total_width) / 2  # Center row.
            current_x = row_start_x
            for idx, scaled_sprite in enumerate(row):
                icon_rect = pygame.Rect(int(current_x), int(current_y), icon_size, icon_size)
                screen.blit(scaled_sprite, icon_rect)
                overall_idx = rows.index(row) * cols + idx
                target_id = all_forms[overall_idx].number if overall_idx < len(all_forms) else None
                if target_id is not None and str(target_id) == str(self.parent.selected_pokemon_id):
                    outline_rect = icon_rect.inflate(OUTLINE_PADDING, OUTLINE_PADDING)
                    pygame.draw.rect(screen, OUTLINE_COLOR, outline_rect, OUTLINE_THICKNESS)
                self.popup_form_icon_rects.append((icon_rect, target_id))
                current_x += icon_size + gap
            current_y += icon_size + gap

    def handle_forms_popup_event(self, event):
        """
        Handle events when the forms popup is active.
        - Clicking outside dismisses the popup.
        - Clicking on a form icon opens that form.
        - Pressing Escape dismisses the popup.
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.popup_rect and self.popup_rect.collidepoint(event.pos):
                for rect, target_id in self.popup_form_icon_rects:
                    if rect.collidepoint(event.pos):
                        if target_id is not None:
                            self.parent.open(target_id, keep_tab=True)
                        self.forms_popup_active = False
                        return True
            else:
                self.forms_popup_active = False
                return True
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.forms_popup_active = False
                return True
        return False
