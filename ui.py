# ui.py
import os
import pygame

from config import (
    TOTAL_POKEMON, BOX_SIZE
)

class TextInput:
    def __init__(self, rect, font, text=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = text
        self.active = False
        self.cursor_pos = len(text)
        self.cursor_visible = True
        self.last_cursor_toggle = pygame.time.get_ticks()
        self.cursor_interval = 500  # milliseconds

    def handle_event(self, event):
        """Handle key and mouse events when active. Returns 'enter' if Enter was pressed."""
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[:self.cursor_pos-1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos+1:]
            elif event.key == pygame.K_LEFT:
                if self.cursor_pos > 0:
                    self.cursor_pos -= 1
            elif event.key == pygame.K_RIGHT:
                if self.cursor_pos < len(self.text):
                    self.cursor_pos += 1
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
            elif event.key == pygame.K_RETURN:
                return "enter"
            else:
                if event.unicode:
                    self.text = self.text[:self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                    self.cursor_pos += len(event.unicode)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
                # For simplicity, put cursor at end.
                self.cursor_pos = len(self.text)
            else:
                self.active = False
        return None

    def update(self):
        """Update the cursor blink state."""
        current_time = pygame.time.get_ticks()
        if current_time - self.last_cursor_toggle >= self.cursor_interval:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_toggle = current_time

    def draw(self, surface):
        """Draw the text input box, text, and blinking cursor."""
        # Draw the box
        pygame.draw.rect(surface, (255, 255, 255), self.rect)
        pygame.draw.rect(surface, (0, 0, 0), self.rect, 2)
        # Render text
        text_surface = self.font.render(self.text, True, (0, 0, 0))
        surface.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        # Draw cursor if active
        if self.active and self.cursor_visible:
            prefix = self.text[:self.cursor_pos]
            prefix_surface = self.font.render(prefix, True, (0, 0, 0))
            cursor_x = self.rect.x + 5 + prefix_surface.get_width()
            cursor_y = self.rect.y + 5
            cursor_height = self.font.get_height()
            pygame.draw.line(surface, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)


def draw_search_bar(screen, rect, text, active, error, font):
    """
    Draws the search bar with its text.
    """
    color = (255, 255, 255) if active else (200, 200, 200)
    if error:
        color = (255, 200, 200)
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, (0, 0, 0), rect, 2)
    text_surface = font.render(text, True, (0, 0, 0))
    screen.blit(text_surface, (rect.x + 5, rect.y + 5))

def draw_box_info(screen, window_width, y, current_box, num_boxes, font):
    """
    Draws the box information (e.g. "Box 3/35") centered horizontally.
    """
    text = font.render(f"Box {current_box + 1}/{num_boxes}", True, (255, 255, 255))
    screen.blit(text, (window_width // 2 - text.get_width() // 2, y))

def draw_arrow_button(screen, image, rect, mouse_pos, mouse_buttons):
    """
    Draws an arrow button using the provided image and rectangle.
    Adjusts brightness by a subtle shift if the mouse is over the button,
    and darkens the image slightly when the button is pressed.
    """
    if image:
        img = image.copy()
        if rect.collidepoint(mouse_pos):
            if mouse_buttons[0]:
                img = adjust_brightness(img, -13)
            else:
                img = adjust_brightness(img, 13)
        img = pygame.transform.smoothscale(img, (rect.width, rect.height))
        screen.blit(img, rect.topleft)

def draw_suggestions(screen, rect, suggestions, regular_font, bold_font, query=""):
    """
    Draws the suggestion dropdown below the search bar.
    The portion of each suggestion that matches 'query' is rendered in bold using bold_font.
    """
    from config import SEARCH_SUGGESTION_HEIGHT
    for i, (name, number) in enumerate(suggestions):
        sug_rect = pygame.Rect(
            rect.x,
            rect.y + rect.height + i * SEARCH_SUGGESTION_HEIGHT,
            rect.width,
            SEARCH_SUGGESTION_HEIGHT
        )
        pygame.draw.rect(screen, (230, 230, 230), sug_rect)
        pygame.draw.rect(screen, (0, 0, 0), sug_rect, 1)
        
        lower_name = name.lower()
        lower_query = query.lower()
        match_start = lower_name.find(lower_query)
        if match_start == -1:
            rendered_name = regular_font.render(name, True, (0, 0, 0))
        else:
            prefix = name[:match_start]
            match_text = name[match_start:match_start+len(query)]
            suffix = name[match_start+len(query):]
            prefix_surf = regular_font.render(prefix, True, (0, 0, 0))
            match_surf = bold_font.render(match_text, True, (0, 0, 0))
            suffix_surf = regular_font.render(suffix, True, (0, 0, 0))
            total_width = prefix_surf.get_width() + match_surf.get_width() + suffix_surf.get_width()
            rendered_name = pygame.Surface((total_width, prefix_surf.get_height()), pygame.SRCALPHA)
            rendered_name.blit(prefix_surf, (0, 0))
            rendered_name.blit(match_surf, (prefix_surf.get_width(), 0))
            rendered_name.blit(suffix_surf, (prefix_surf.get_width() + match_surf.get_width(), 0))
        
        num_text = f" (#{number})"
        num_surf = regular_font.render(num_text, True, (0, 0, 0))
        final_width = rendered_name.get_width() + num_surf.get_width()
        final_surf = pygame.Surface((final_width, rendered_name.get_height()), pygame.SRCALPHA)
        final_surf.blit(rendered_name, (0, 0))
        final_surf.blit(num_surf, (rendered_name.get_width(), 0))
        
        screen.blit(final_surf, (sug_rect.x + 5, sug_rect.y + (sug_rect.height - final_surf.get_height()) // 2))

def adjust_brightness(surface, amount):
    """
    Adjusts the brightness of the given surface.
    If amount is positive, brightens the image; if negative, darkens it.
    """
    new_surface = surface.copy()
    if amount >= 0:
        new_surface.fill((amount, amount, amount), special_flags=pygame.BLEND_RGB_ADD)
    else:
        new_surface.fill((-amount, -amount, -amount), special_flags=pygame.BLEND_RGB_SUB)
    return new_surface

def draw_ui_rect(surface, rect, color, opacity):
    """A small helper to draw a rectangle with partial opacity."""
    temp = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    r, g, b = color[:3]
    a = int(opacity * 255)
    temp.fill((r, g, b, a))
    surface.blit(temp, (rect.x, rect.y))


###
# Reworked "compute_*" methods to retrieve data from dex_adapter
###
def compute_box_completion(current_box, exclude_locked, filtered_out_set=None):
    """
    Count how many Pokémon in the given box are caught,
    ignoring locked or filtered-out items as needed.
    """
    from config import TOTAL_POKEMON, BOX_SIZE
    import dex_adapter

    start = current_box * BOX_SIZE + 1
    end = min(current_box * BOX_SIZE + BOX_SIZE, TOTAL_POKEMON)
    obtained = 0
    adjusted_total = 0
    for i in range(start, end + 1):
        key = str(i)
        locked = dex_adapter.pokemon_locked(i)
        caught = dex_adapter.pokemon_caught(i)
        if exclude_locked and locked and not caught:
            continue
        if filtered_out_set and key in filtered_out_set:
            continue
        adjusted_total += 1
        if caught:
            obtained += 1
    percentage = (obtained / adjusted_total * 100) if adjusted_total else 0
    return obtained, adjusted_total, percentage

def compute_region_completion(last_num, exclude_locked, filtered_out_set=None):
    """
    Compute region completion by first determining which region 'last_num' falls into,
    and then count caught Pokémon in that region.
    """
    import dex_adapter
    region_defs = dex_adapter.get_region_defs()
    region_name = None
    region_range = None
    for name, rng in region_defs.items():
        if rng[0] <= last_num <= rng[1]:
            region_name = name
            region_range = rng
            break
    if region_range is None:
        return "Unknown", 0, 0, 0
    start, end = region_range
    obtained = 0
    adjusted_total = 0
    from config import TOTAL_POKEMON
    for i in range(start, end + 1):
        key = str(i)
        locked = dex_adapter.pokemon_locked(i)
        caught = dex_adapter.pokemon_caught(i)
        if exclude_locked and locked and not caught:
            continue
        if filtered_out_set and key in filtered_out_set:
            continue
        adjusted_total += 1
        if caught:
            obtained += 1
    percentage = (obtained / adjusted_total * 100) if adjusted_total else 0
    return region_name, obtained, adjusted_total, percentage

def compute_national_completion(exclude_locked, filtered_out_set=None):
    """
    Count how many are caught in the entire National Dex,
    ignoring locked or filtered-out items as needed.
    """
    from config import TOTAL_POKEMON
    import dex_adapter

    obtained = 0
    adjusted_total = 0
    for i in range(1, TOTAL_POKEMON + 1):
        key = str(i)
        # Instead of directly accessing the dictionary, use the adapter functions.
        locked = dex_adapter.pokemon_locked(i)
        caught = dex_adapter.pokemon_caught(i)

        if exclude_locked and locked and not caught:
            continue
        if filtered_out_set and key in filtered_out_set:
            continue
        adjusted_total += 1
        if caught:
            obtained += 1
    percentage = (obtained / adjusted_total * 100) if adjusted_total else 0
    return obtained, adjusted_total, percentage


def compute_mark_counts(group, current_box, exclude_locked, filtered_out_set=None):
    """
    Count origin marks for the chosen group (Box, Region, All).
    """
    import dex_adapter

    pokedex_data = dex_adapter.get_pokedex_data()
    region_defs = dex_adapter.get_region_defs()

    indices = []
    if group == "Box":
        start = current_box * BOX_SIZE + 1
        end = min(current_box * BOX_SIZE + BOX_SIZE, TOTAL_POKEMON)
        indices = list(range(start, end + 1))
    elif group == "Region":
        last_num = min(current_box * BOX_SIZE + BOX_SIZE, TOTAL_POKEMON)
        region_range = None
        for name, rng in region_defs.items():
            if rng[0] <= last_num <= rng[1]:
                region_range = rng
                break
        if region_range:
            start, end = region_range
            indices = list(range(start, end + 1))
    else:
        indices = list(range(1, TOTAL_POKEMON + 1))
    
    mark_counts = {}
    valid_count = 0
    for i in indices:
        key = str(i)
        locked = pokedex_data[key].get("locked", False)
        caught = pokedex_data[key].get("caught", False)
        if exclude_locked and locked and not caught:
            continue
        if filtered_out_set and key in filtered_out_set:
            continue
        valid_count += 1
        origin_mark = pokedex_data[key].get("origin_mark")
        if origin_mark:
            mark_counts[origin_mark] = mark_counts.get(origin_mark, 0) + 1
    return mark_counts, valid_count

def get_box_title(box_index):
    """
    Returns the string like '#0001 - #0030 [01/???]' for the given box_index.
    """
    first_num = box_index * BOX_SIZE + 1
    last_num = min(box_index * BOX_SIZE + BOX_SIZE, TOTAL_POKEMON)
    box_num = box_index + 1
    total_boxes = (TOTAL_POKEMON + BOX_SIZE - 1) // BOX_SIZE
    return f"#{first_num:04d} - #{last_num:04d} [{box_num:02d}/{total_boxes:02d}]"

def draw_label_value(surface, label, value, font, x, y, width):
    """
    Draws a two-line label: 
       [label] 
       .................... [value]
    onto the given surface at (x,y), right-aligning the value.
    """
    label_surf = font.render(label, True, (255,255,255))
    value_surf = font.render(value, True, (255,255,255))
    surface.blit(label_surf, (x, y))
    surface.blit(value_surf, (x + width - value_surf.get_width(), y + label_surf.get_height()))
    return label_surf.get_height() + value_surf.get_height()

def build_formdex_list():
    """
    Build a list of form entries from the adapter's save_data.
    This function no longer accepts save_data as a param;
    we retrieve it from dex_adapter.
    """
    import dex_adapter
    save_data = dex_adapter.get_save_data()

    entries = []
    # same logic as before
    for nat in sorted(save_data, key=lambda x: int(x)):
        entry = save_data[nat]
        forms = entry.get("form")
        if forms and isinstance(forms, dict):
            sub_entries = []
            if nat in forms:
                sub_entries.append((nat, forms[nat]))
            for fk, data_sub in forms.items():
                if fk != nat:
                    sub_entries.append((fk, data_sub))
            sub_entries[1:] = sorted(sub_entries[1:], key=lambda x: x[0])
            for fk, form_data in sub_entries:
                entries.append({
                    "national": nat,
                    "form_key": fk,
                    "data": form_data
                })
    return entries
