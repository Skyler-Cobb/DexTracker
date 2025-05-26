# main.py

import pygame
import sys
import os
import json
import math

import ui
import dialogue
import dex_adapter
import assets
from box_manager import BoxManager

from config import (
    TOTAL_POKEMON, BOX_SIZE, ROWS, COLUMNS, SPRITE_SIZE,
    H_PADDING, V_PADDING, BOX_TO_GRID_PADDING, SEARCH_SUGGESTION_HEIGHT,
    MAX_SUGGESTIONS, SEARCH_TO_BOX_PADDING, FONT_REGULAR,
    FONT_BOLD, RESOURCES, MARKS
)

import dex_adapter

def draw_mark_overlay(screen, item, pos, cell_size, mark_mode):
    """
    Draws the Pokémon’s mark icon over its sprite.
      - In mark_mode 0 (all marks): display the mark if it is not "error.png" or "none.png".
      - In mark_mode 1 (only GO): display the mark only if it exactly equals "7.1_GO.png".
      - In mark_mode 2 (off): do not display any mark.
    The icon is scaled to about 1/3 of the sprite size and aligned to the sprite's bottom right.
    """
    mark = dex_adapter.get_origin_mark(item.number)
    if not mark:
        return
    if mark.lower() in ("error.png", "none.png"):
        return
    if mark_mode == 2:
        return
    if mark_mode == 1 and mark != "7.1_GO.png":
        return

    icon = dex_adapter.safe_load_icon(os.path.join("origin", mark), MARKS)
    if icon is None:
        return
    mark_size = int(cell_size / 3)
    icon = pygame.transform.smoothscale(icon, (mark_size, mark_size))
    x, y = pos
    mark_x = x + cell_size - mark_size
    mark_y = y + cell_size - mark_size
    screen.blit(icon, (mark_x, mark_y))


def main():
    pygame.init()

    dex_adapter.init_adapter()
    box_mgr = BoxManager()
    box_mgr.initialize()

    SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 600
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DexTracker")
    clock = pygame.time.Clock()

    # --- UI state variables ---
    editing_mode = False
    current_mode = "search"  # Modes: "search" → "filter" → "highlight" → "search" ...
    mark_mode = 0  # 0: all marks, 1: only GO, 2: off
    exclude_locked = False
    dropdown_expanded = False
    mark_group_selection = "Box"

    top_bar_y = 10
    top_bar_h = 30
    gap = 5

    # --- Top Bar Buttons Setup ---
    editing_button_rect = pygame.Rect(10, top_bar_y, 120, top_bar_h)
    search_bar_x = editing_button_rect.right + gap
    buttons_total_width = 30 * 4 + gap * 5  # Four buttons: mode toggle, mark, clear, settings.
    search_bar_width = SCREEN_WIDTH - 10 - buttons_total_width - editing_button_rect.right
    search_bar_rect = pygame.Rect(search_bar_x, top_bar_y, search_bar_width, top_bar_h)

    buttons_x = search_bar_rect.right + gap
    mode_toggle_btn_rect = pygame.Rect(buttons_x, top_bar_y, 30, top_bar_h)
    mark_btn_rect = pygame.Rect(mode_toggle_btn_rect.right + gap, top_bar_y, 30, top_bar_h)
    clear_btn_rect = pygame.Rect(mark_btn_rect.right + gap, top_bar_y, 30, top_bar_h)
    settings_btn_rect = pygame.Rect(clear_btn_rect.right + gap, top_bar_y, 30, top_bar_h)

    # --- Create Search Bar Input ---
    search_input = ui.TextInput(search_bar_rect, None)

    # Note: The Dex (module switch) button will be re-calculated later after the wallpaper is computed.

    background_color = (153, 153, 153)

    # --- Load Config Data ---
    poke_grid_scale = dex_adapter.get_poke_grid_scale()
    UI_opacity = dex_adapter.get_ui_opacity()
    filtered_out_color = dex_adapter.get_filtered_out_color()
    region_defs = dex_adapter.get_region_defs()

    # --- Wallpaper ---
    wallpaper = box_mgr.get_wallpaper_for_box(box_mgr.current_box)
    scaled_wallpaper = None
    wp_rect = None
    if wallpaper:
        wallpaper = wallpaper.convert_alpha()
        target_h = int(SCREEN_HEIGHT * 0.85)
        scale_wp = target_h / wallpaper.get_height()
        target_w = int(wallpaper.get_width() * scale_wp)
        scaled_wallpaper = pygame.transform.smoothscale(wallpaper, (target_w, target_h))
        wp_rect = scaled_wallpaper.get_rect()
        wp_rect.midbottom = (SCREEN_WIDTH // 2, SCREEN_HEIGHT)
    else:
        wp_rect = pygame.Rect(0, SCREEN_HEIGHT - 300, SCREEN_WIDTH, 300)

    # --- Recalculate Dex Toggle (Module Switch) Button based on wallpaper ---
    # The button's right side stays as before (10px from the screen edge) while its left edge is set
    # to be 10px to the right of the wallpaper’s right edge.
    # Its height is dynamically chosen to be tall enough for the module name.
    # (Note: main_font is loaded below, so we will update dex_toggle_rect after loading fonts.)

    # --- Box Row (positioned just above wallpaper) ---
    box_row_width = int(wp_rect.width * 0.6)
    box_row_height = 40
    gap_y = wp_rect.top - search_bar_rect.bottom
    box_row_y = search_bar_rect.bottom + gap_y // 2 - box_row_height // 2
    box_row_rect = pygame.Rect(
        wp_rect.x + (wp_rect.width - box_row_width) // 2,
        box_row_y, box_row_width, box_row_height
    )
    box_left_arrow = pygame.Rect(box_row_rect.x - 30 - gap, box_row_y, 30, box_row_height)
    box_right_arrow = pygame.Rect(box_row_rect.right + gap, box_row_y, 30, box_row_height)

    # --- Pokémon Grid Scaling ---
    natural_grid_width = COLUMNS * SPRITE_SIZE + (COLUMNS - 1) * H_PADDING
    natural_grid_height = ROWS * SPRITE_SIZE + (ROWS - 1) * V_PADDING
    scaled_grid_width = int(wp_rect.width * poke_grid_scale)
    scale_factor = scaled_grid_width / natural_grid_width
    scaled_grid_height = int(natural_grid_height * scale_factor)
    grid_x = wp_rect.x + (wp_rect.width - scaled_grid_width) // 2
    grid_y = wp_rect.y + (wp_rect.height - scaled_grid_height) // 2

    # --- Load Icons ---
    left_arrow_img = dex_adapter.get_ui_image("arrow-left.png")
    right_arrow_img = dex_adapter.get_ui_image("arrow-right.png")
    search_icon = dex_adapter.safe_load_icon("search.png")
    filter_icon = dex_adapter.safe_load_icon("filter.png")
    highlight_icon = dex_adapter.safe_load_icon("highlight.png")
    clear_icon = dex_adapter.safe_load_icon("clear.png")
    mark_on_icon = dex_adapter.safe_load_icon("mark-ON.png")
    mark_go_icon = dex_adapter.safe_load_icon("mark-GO.png")
    mark_off_icon = dex_adapter.safe_load_icon("mark-OFF.png")
    settings_icon = dex_adapter.safe_load_icon("settings.png")

    # --- Load Fonts ---
    from config import FONT_REGULAR, FONT_BOLD
    main_font = dex_adapter.load_font(FONT_REGULAR, 20)
    button_font = dex_adapter.load_font(FONT_REGULAR, 16)
    close_x_font = dex_adapter.load_font(FONT_BOLD, 14)
    sidebar_font = dex_adapter.load_font(FONT_REGULAR, 14)

    search_input.font = main_font

    # --- Now that main_font is available, recalc dex_toggle_rect (Module Button) ---
    module_button_height = main_font.get_height() + 10
    module_button_right = SCREEN_WIDTH - 10
    module_button_left = wp_rect.right + 10  # 10px gap from the wallpaper
    module_button_width = module_button_right - module_button_left
    dex_toggle_rect = pygame.Rect(module_button_left, SCREEN_HEIGHT - 10 - module_button_height,
                                  module_button_width, module_button_height)

    # --- Property Dialog for Editing ---
    prop_dialog = dialogue.PropertyDialog(SCREEN_WIDTH, SCREEN_HEIGHT)

    # --- Suggestions ---
    suggestions = []
    last_filter_text = ""
    filter_update_interval = 300
    last_filter_update_time = pygame.time.get_ticks()

    # --- Sidebar Setup ---
    sidebar_width = 190
    sidebar_rect = pygame.Rect(
        10, editing_button_rect.bottom + 5, sidebar_width,
        SCREEN_HEIGHT - (editing_button_rect.bottom + 5)
    )

    def build_suggestions(search_text):
        if not search_text:
            return []
        text_lower = search_text.lower()
        all_items = dex_adapter.get_items()
        result = []
        for item in all_items:
            if text_lower in item.name.lower():
                result.append((item.name, item.number))
            if len(result) >= MAX_SUGGESTIONS:
                break
        return result

    running = True
    while running:
        suggestion_clicked = False  # Flag to prevent propagation if a suggestion is clicked.
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # Give priority to property dialog events.
            if prop_dialog.is_open():
                if prop_dialog.handle_event(event, search_input, suggestions):
                    continue

            if event.type == pygame.MOUSEWHEEL and not prop_dialog.is_open():
                if event.y < 0:
                    box_mgr.next_box()
                    dex_adapter.save_all_changes()
                elif event.y > 0:
                    box_mgr.prev_box()
                    dex_adapter.save_all_changes()
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Deselect the search bar if clicking outside its area.
                if not search_bar_rect.collidepoint(event.pos):
                    search_input.active = False

                # Sidebar dropdown toggle.
                sb_x = sidebar_rect.x
                dropdown_rect = pygame.Rect(sb_x + 10, sidebar_rect.y + 80, sidebar_rect.width - 20, 25)
                if dropdown_rect.collidepoint(event.pos):
                    dropdown_expanded = not dropdown_expanded
                    pygame.event.clear(pygame.MOUSEBUTTONDOWN)
                    continue

                # Settings button.
                if settings_btn_rect.collidepoint(event.pos):
                    print("Settings button clicked.")
                    continue

                # Combined mode toggle button.
                if mode_toggle_btn_rect.collidepoint(event.pos):
                    if current_mode == "search":
                        current_mode = "filter"
                    elif current_mode == "filter":
                        current_mode = "highlight"
                    elif current_mode == "highlight":
                        current_mode = "search"
                    search_input.text = ""
                    suggestions.clear()
                    continue

                # Dex (module switch) button.
                if dex_toggle_rect.collidepoint(event.pos):
                    box_mgr.switch_module()
                    suggestions.clear()
                    continue

                # Top bar buttons: editing, mark, clear.
                if editing_button_rect.collidepoint(event.pos):
                    editing_mode = not editing_mode
                    continue
                if mark_btn_rect.collidepoint(event.pos):
                    mark_mode = (mark_mode + 1) % 3
                    continue
                if clear_btn_rect.collidepoint(event.pos):
                    search_input.text = ""
                    suggestions.clear()
                    last_filter_text = ""
                    if current_mode == "filter":
                        box_mgr.set_filter("")
                    continue

                # Suggestion click handling.
                for i, (name, idx) in enumerate(suggestions):
                    sg_rect = pygame.Rect(
                        search_bar_rect.x,
                        search_bar_rect.y + search_bar_rect.height + i * SEARCH_SUGGESTION_HEIGHT,
                        search_bar_rect.width,
                        SEARCH_SUGGESTION_HEIGHT
                    )
                    if sg_rect.collidepoint(event.pos):
                        try:
                            base = int(str(idx).split('.')[0])
                            box_mgr.jump_to_pokemon(base)
                        except Exception:
                            pass
                        search_input.text = ""
                        search_input.active = False
                        suggestions.clear()
                        suggestion_clicked = True
                        break
                if suggestion_clicked:
                    continue

                # Activate search bar when clicked.
                if search_bar_rect.collidepoint(event.pos):
                    search_input.active = True

                # ===== Grid click: check for Pokémon cell clicks =====
                items_in_box = box_mgr.get_items_for_current_box()
                for row in range(ROWS):
                    for col in range(COLUMNS):
                        idx_ = row * COLUMNS + col
                        if idx_ >= len(items_in_box):
                            break
                        item = items_in_box[idx_]
                        cell_x = grid_x + int(col * (SPRITE_SIZE + H_PADDING) * scale_factor)
                        cell_y = grid_y + int(row * (SPRITE_SIZE + V_PADDING) * scale_factor)
                        cell_size = int(SPRITE_SIZE * scale_factor)
                        cell_rect = pygame.Rect(cell_x, cell_y, cell_size, cell_size)
                        if cell_rect.collidepoint(event.pos):
                            # Instead of converting to int and losing decimal info,
                            # preserve the full identifier (e.g., "26" or "26.01")
                            full_id = str(item.number)
                            if editing_mode:
                                prop_dialog.open(full_id)
                            else:
                                dex_adapter.toggle_pokemon_caught(full_id)
                                if hasattr(dex_adapter, "clear_sprite_cache"):
                                    dex_adapter.clear_sprite_cache()
                            break

            elif event.type == pygame.KEYDOWN and not prop_dialog.is_open():
                if search_input.active:
                    if event.key == pygame.K_ESCAPE:
                        search_input.active = False
                        continue
                    result = search_input.handle_event(event)
                    if current_mode == "search" and result == "enter":
                        if suggestions:
                            _, idx = suggestions[0]
                            try:
                                base = int(str(idx).split('.')[0])
                                box_mgr.jump_to_pokemon(base)
                            except Exception:
                                pass
                        search_input.text = ""
                        search_input.active = False
                        suggestions.clear()
                        continue
                else:
                    if event.key == pygame.K_LEFT:
                        box_mgr.prev_box()
                        dex_adapter.save_all_changes()
                    elif event.key == pygame.K_RIGHT:
                        box_mgr.next_box()
                        dex_adapter.save_all_changes()
                    elif event.key == pygame.K_UP:
                        box_mgr.jump_to_prev_region()
                        dex_adapter.save_all_changes()
                    elif event.key == pygame.K_DOWN:
                        box_mgr.jump_to_next_region()
                        dex_adapter.save_all_changes()
                    elif event.key == pygame.K_ESCAPE:
                        if current_mode in ("filter", "highlight"):
                            current_mode = "search"
                            box_mgr.set_filter("")
                        else:
                            running = False

        # --- Mode-specific updates ---
        if current_mode == "filter":
            current_time = pygame.time.get_ticks()
            if (search_input.text != last_filter_text and
                current_time - last_filter_update_time >= filter_update_interval):
                box_mgr.set_filter(search_input.text)
                last_filter_text = search_input.text
                last_filter_update_time = current_time
        elif current_mode == "highlight":
            if search_input.text != last_filter_text:
                box_mgr.current_filter = ""
                box_mgr.refresh()
                last_filter_text = search_input.text
        else:
            text_now = search_input.text
            if text_now != last_filter_text:
                suggestions = build_suggestions(text_now)[:MAX_SUGGESTIONS]
                last_filter_text = text_now

        # --- Drawing Section ---
        # Fill background.
        screen.fill(background_color)

        # --- Draw Decoration in Background ---
        decoration_surf = box_mgr.get_decoration_for_box(box_mgr.current_box)
        if decoration_surf:
            scale_factor_dec = SCREEN_HEIGHT / decoration_surf.get_height()
            new_width = int(decoration_surf.get_width() * scale_factor_dec)
            scaled_decoration = pygame.transform.smoothscale(decoration_surf, (new_width, SCREEN_HEIGHT))
            dec_rect = scaled_decoration.get_rect()
            dec_rect.top = 0
            dec_rect.right = SCREEN_WIDTH
            screen.blit(scaled_decoration, dec_rect)

        # --- Draw Wallpaper ---
        if scaled_wallpaper:
            screen.blit(scaled_wallpaper, wp_rect)
        else:
            pygame.draw.rect(screen, (100, 100, 100), wp_rect)

        # --- Draw the Pokémon Grid ---
        items_this_box = box_mgr.get_items_for_current_box()
        for row in range(ROWS):
            for col in range(COLUMNS):
                idx_ = row * COLUMNS + col
                if idx_ >= len(items_this_box):
                    break
                item = items_this_box[idx_]
                sprite_surf = dex_adapter.load_sprite(item.number)
                if current_mode == "highlight" and search_input.text.strip():
                    if hasattr(item, "get"):
                        item_dict = item
                    else:
                        item_dict = dex_adapter.build_item_dict(item.number)
                    if not dex_adapter.filter_item(item_dict, search_input.text):
                        sprite_surf = assets.create_silhouette(sprite_surf, filtered_out_color)
                cell_x = grid_x + int(col * (SPRITE_SIZE + H_PADDING) * scale_factor)
                cell_y = grid_y + int(row * (SPRITE_SIZE + V_PADDING) * scale_factor)
                cell_size = int(SPRITE_SIZE * scale_factor)
                scaled_sprite = pygame.transform.smoothscale(sprite_surf, (cell_size, cell_size))
                screen.blit(scaled_sprite, (cell_x, cell_y))
                draw_mark_overlay(screen, item, (cell_x, cell_y), cell_size, mark_mode)

        # --- Draw Top Bar Buttons ---
        def draw_button(rect):
            pygame.draw.rect(screen, (230, 230, 230), rect)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)

        draw_button(editing_button_rect)
        edit_label = "Edit: ON" if editing_mode else "Edit: OFF"
        edit_surf = main_font.render(edit_label, True, (0, 0, 0))
        screen.blit(edit_surf, (editing_button_rect.x + 5, editing_button_rect.y + 5))

        draw_button(mode_toggle_btn_rect)
        if current_mode == "search" and search_icon:
            icon = pygame.transform.smoothscale(search_icon, (mode_toggle_btn_rect.width, mode_toggle_btn_rect.height))
            screen.blit(icon, mode_toggle_btn_rect)
        elif current_mode == "filter" and filter_icon:
            icon = pygame.transform.smoothscale(filter_icon, (mode_toggle_btn_rect.width, mode_toggle_btn_rect.height))
            screen.blit(icon, mode_toggle_btn_rect)
        elif current_mode == "highlight" and highlight_icon:
            icon = pygame.transform.smoothscale(highlight_icon, (mode_toggle_btn_rect.width, mode_toggle_btn_rect.height))
            screen.blit(icon, mode_toggle_btn_rect)

        draw_button(mark_btn_rect)
        if mark_mode == 0 and mark_on_icon:
            screen.blit(pygame.transform.smoothscale(mark_on_icon, (mark_btn_rect.width, mark_btn_rect.height)), mark_btn_rect)
        elif mark_mode == 1 and mark_go_icon:
            screen.blit(pygame.transform.smoothscale(mark_go_icon, (mark_btn_rect.width, mark_btn_rect.height)), mark_btn_rect)
        else:
            if mark_off_icon:
                screen.blit(pygame.transform.smoothscale(mark_off_icon, (mark_btn_rect.width, mark_btn_rect.height)), mark_btn_rect)

        draw_button(clear_btn_rect)
        if clear_icon:
            screen.blit(pygame.transform.smoothscale(clear_icon, (clear_btn_rect.width, clear_btn_rect.height)), clear_btn_rect)

        draw_button(settings_btn_rect)
        if settings_icon:
            screen.blit(pygame.transform.smoothscale(settings_icon, (settings_btn_rect.width, settings_btn_rect.height)), settings_btn_rect)

        # --- Draw the Search Bar ---
        ui.draw_search_bar(screen, search_bar_rect, search_input.text, search_input.active, False, main_font)
        if search_input.active:
            text_width, _ = main_font.size(search_input.text)
            cursor_x = search_bar_rect.x + text_width + 2
            cursor_y = search_bar_rect.y + 4
            cursor_height = main_font.get_height() - 8
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                pygame.draw.line(screen, (0, 0, 0), (cursor_x, cursor_y), (cursor_x, cursor_y + cursor_height), 2)

        # --- Draw the Module (Dex Toggle) Button ---
        draw_button(dex_toggle_rect)
        mod_name = dex_adapter.get_current_module_name()
        # Show only the module name (no "Module: " prefix)
        mod_label = f"{mod_name}"
        mod_surf = main_font.render(mod_label, True, (0, 0, 0))
        mx = dex_toggle_rect.centerx - mod_surf.get_width() // 2
        my = dex_toggle_rect.centery - mod_surf.get_height() // 2
        screen.blit(mod_surf, (mx, my))

        # --- Draw Box Arrow Buttons ---
        if left_arrow_img:
            ui.draw_arrow_button(screen, left_arrow_img, box_left_arrow, pygame.mouse.get_pos(), pygame.mouse.get_pressed())
        if right_arrow_img:
            ui.draw_arrow_button(screen, right_arrow_img, box_right_arrow, pygame.mouse.get_pos(), pygame.mouse.get_pressed())

        # --- Draw Box Title with Range ---
        # Compute the rounded down values for the first and last Pokémon numbers in the current box.
        if items_this_box:
            first_val = math.floor(float(items_this_box[0].number))
            last_val = math.floor(float(items_this_box[-1].number))
        else:
            first_val = last_val = 0
        box_label_text = f"Box {box_mgr.current_box + 1:02d}/{box_mgr.get_num_boxes():02d} " \
                         f"(#{first_val:04d} - #{last_val:04d})"
        box_surf = main_font.render(box_label_text, True, (0, 0, 0))
        bx = box_row_rect.centerx - box_surf.get_width() // 2
        by = box_row_rect.centery - box_surf.get_height() // 2
        box_bg_rect = pygame.Rect(bx - 5, by - 2, box_surf.get_width() + 10, box_surf.get_height() + 4)
        # Draw a wide light gray background with dark gray borders.
        pygame.draw.rect(screen, (211, 211, 211), box_bg_rect)
        pygame.draw.rect(screen, (100, 100, 100), box_bg_rect, 1)
        screen.blit(box_surf, (bx, by))

        # --- Draw Sidebar ---
        pygame.draw.rect(screen, (230, 230, 230), sidebar_rect)
        pygame.draw.rect(screen, (0, 0, 0), sidebar_rect, 2)
        sb_x = sidebar_rect.x
        sb_y = sidebar_rect.y + 10
        line_spacing = 5

        # Sidebar: Box Completion
        bc_caught, bc_total, bc_percent = box_mgr.get_box_completion()
        box_label_line = "Box Completion:"
        box_label_surf = sidebar_font.render(box_label_line, True, (0, 0, 0))
        screen.blit(box_label_surf, (sb_x + 10, sb_y))
        sb_y += sidebar_font.get_height()
        box_value_line = f"{bc_caught}/{bc_total} ({bc_percent:.1f}%)"
        box_value_surf = sidebar_font.render(box_value_line, True, (0, 0, 0))
        screen.blit(box_value_surf, (sidebar_rect.right - box_value_surf.get_width() - 10, sb_y))
        sb_y += sidebar_font.get_height() * 2

        # Sidebar: Region Completion
        r_name, r_caught, r_total, r_percent = box_mgr.get_region_completion()
        region_label_line = f"{r_name} Completion:"
        region_label_surf = sidebar_font.render(region_label_line, True, (0, 0, 0))
        screen.blit(region_label_surf, (sb_x + 10, sb_y))
        sb_y += sidebar_font.get_height()
        region_value_line = f"{r_caught}/{r_total} ({r_percent:.1f}%)"
        region_value_surf = sidebar_font.render(region_value_line, True, (0, 0, 0))
        screen.blit(region_value_surf, (sidebar_rect.right - region_value_surf.get_width() - 10, sb_y))
        sb_y += sidebar_font.get_height() * 2

        # Sidebar: National Completion
        nc_caught, nc_total, nc_percent = box_mgr.get_module_completion()
        nat_label_line = "National Completion:"
        nat_label_surf = sidebar_font.render(nat_label_line, True, (0, 0, 0))
        screen.blit(nat_label_surf, (sb_x + 10, sb_y))
        sb_y += sidebar_font.get_height()
        nat_value_line = f"{nc_caught}/{nc_total} ({nc_percent:.1f}%)"
        nat_value_surf = sidebar_font.render(nat_value_line, True, (0, 0, 0))
        screen.blit(nat_value_surf, (sidebar_rect.right - nat_value_surf.get_width() - 10, sb_y))
        sb_y += sidebar_font.get_height() * 2

        # "Ignore Locked?" Checkbox
        checkbox_rect = pygame.Rect(sb_x + 10, sb_y, 20, 20)
        pygame.draw.rect(screen, (255, 255, 255), checkbox_rect)
        pygame.draw.rect(screen, (0, 0, 0), checkbox_rect, 1)
        if exclude_locked:
            pygame.draw.line(screen, (0, 0, 0), (checkbox_rect.x + 2, checkbox_rect.y + 2),
                             (checkbox_rect.right - 2, checkbox_rect.bottom - 2), 2)
            pygame.draw.line(screen, (0, 0, 0), (checkbox_rect.x + 2, checkbox_rect.bottom - 2),
                             (checkbox_rect.right - 2, checkbox_rect.y + 2), 2)
        locked_label = sidebar_font.render("Ignore Locked?", True, (0, 0, 0))
        screen.blit(locked_label, (checkbox_rect.right + 5, checkbox_rect.y))
        sb_y += 20 + 2 * line_spacing

        # Dropdown for mark group ("Box", "Region", "All")
        dropdown_rect = pygame.Rect(sb_x + 10, sb_y, sidebar_rect.width - 20, 25)
        pygame.draw.rect(screen, (255, 255, 255), dropdown_rect)
        pygame.draw.rect(screen, (0, 0, 0), dropdown_rect, 1)
        mg_label = sidebar_font.render(mark_group_selection, True, (0, 0, 0))
        screen.blit(mg_label, (dropdown_rect.x + 5, dropdown_rect.y + 4))
        if dropdown_expanded:
            opts = ["Box", "Region", "All"]
            for i, option in enumerate(opts):
                opt_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.y + 25 * (i + 1),
                                       dropdown_rect.width, 25)
                pygame.draw.rect(screen, (230, 230, 230), opt_rect)
                pygame.draw.rect(screen, (0, 0, 0), opt_rect, 1)
                text_surf = sidebar_font.render(option, True, (0, 0, 0))
                screen.blit(text_surf, (opt_rect.x + 5, opt_rect.y + 4))

        # --- Draw Suggestions ---
        ui.draw_suggestions(screen, search_bar_rect, suggestions, main_font, main_font, query=search_input.text)

        if prop_dialog.is_open():
            prop_dialog.draw(screen)

        search_input.update()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
