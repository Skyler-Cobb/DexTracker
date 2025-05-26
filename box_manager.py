# box_manager.py
"""
BoxManager: Centralizes all logic for determining which Pokémon (or forms)
are displayed in each box, and handles module switches, filtering, and navigation.
Now the decoration selection uses assets.choose_decoration() from assets.py.
Additionally, if the current module has "default_shiny" set to True,
the BoxManager will expose that flag so that shiny sprites can be loaded.
"""

import config
import dex_adapter
import pygame
import os
import assets  # For the decoration selection via choose_decoration()

class BoxManager:
    def __init__(self):
        self.visible_items = []     # The list of items allowed by the active module and filter.
        self.current_box = 0        # Zero-based index of the current box.
        self.num_boxes = 1          # Computed based on the number of visible items..
        self.box_size = config.BOX_SIZE
        self.current_filter = ""    # Current filter/search query string.
        self.cached_wallpaper = None  # Cache the wallpaper so we don’t reload it every frame.
        # New attribute: default_shiny reflects the module setting for loading shiny sprites.
        self.default_shiny = False

    def initialize(self):
        """Load the wallpaper once and then refresh the visible items."""
        self.cached_wallpaper = dex_adapter.load_wallpaper()
        # Update the default_shiny flag from the current module.
        self.default_shiny = dex_adapter.get_default_shiny()
        self.refresh()

    def refresh(self):
        """
        Refresh the list of visible items based on the current filter and active module,
        recalculate the total number of boxes, and update module settings.
        """
        if self.current_filter:
            filtered, _ = dex_adapter.filter_items_by_module(self.current_filter)
            self.visible_items = filtered
        else:
            self.visible_items = dex_adapter.get_visible_items()

        total_visible = len(self.visible_items)
        self.num_boxes = max(1, (total_visible + self.box_size - 1) // self.box_size)
        if self.current_box >= self.num_boxes:
            self.current_box = self.num_boxes - 1
        
        # Update default_shiny setting on every refresh in case the module settings changed.
        self.default_shiny = dex_adapter.get_default_shiny()

    def set_filter(self, new_filter: str):
        """
        Apply a new search/filter query, reset the current box to 0,
        and refresh the visible items.
        """
        self.current_filter = new_filter.strip()
        self.current_box = 0
        self.refresh()

    def jump_to_pokemon(self, pokemon_number: int):
        """
        Given a base Pokémon number, jump to the box that contains it.
        Searches the current visible items and, if not found, falls back
        to a basic calculation.
        """
        found_index = None
        for idx, item in enumerate(self.visible_items):
            try:
                base = int(str(item.number).split('.')[0])
                if base == pokemon_number:
                    found_index = idx
                    break
            except:
                pass
        if found_index is not None:
            self.current_box = found_index // self.box_size
        else:
            self.current_box = (pokemon_number - 1) // self.box_size

    def get_num_boxes(self) -> int:
        """Return the total number of boxes available."""
        return self.num_boxes

    def set_current_box(self, box_index: int):
        """Directly set the current box if the given index is valid."""
        if 0 <= box_index < self.num_boxes:
            self.current_box = box_index

    def next_box(self):
        """Advance to the next box (with wrap-around)."""
        self.current_box = (self.current_box + 1) % self.num_boxes

    def prev_box(self):
        """Return to the previous box (with wrap-around)."""
        self.current_box = (self.current_box - 1) % self.num_boxes

    def get_items_for_box(self, box_index: int):
        """Return the slice of visible items for the given box index."""
        start_idx = box_index * self.box_size
        end_idx = start_idx + self.box_size
        return self.visible_items[start_idx:end_idx]

    def get_items_for_current_box(self):
        """Return the items for the current box."""
        return self.get_items_for_box(self.current_box)

    def switch_module(self):
        """
        Cycle to the next module (via dex_adapter). Clear any active filter,
        reset the current box to 0, refresh the visible items, and update default_shiny.
        """
        dex_adapter.module_switch()
        self.current_filter = ""
        self.current_box = 0
        self.refresh()
        # After switching modules, update default_shiny based on new module settings.
        self.default_shiny = dex_adapter.get_default_shiny()

    def get_wallpaper_for_box(self, box_index: int):
        """
        Return the cached wallpaper image for the box.
        The final scaling and positioning is handled in main.py.
        """
        return self.cached_wallpaper

    def get_decoration_for_box(self, box_index: int):
        """
        Use assets.choose_decoration() to pick an appropriate decoration image
        for the current box and active dex.
        """
        current_dex = dex_adapter.get_current_module_name()
        return assets.choose_decoration(self.current_box, current_dex)

    def jump_to_prev_region(self):
        """
        Jump to the previous region based on which region the last Pokémon in the current box is in.
        """
        region_defs = dex_adapter.get_region_defs()
        sorted_regions = sorted(region_defs.items(), key=lambda item: item[1][0])
        last_num = min(self.current_box * self.box_size + self.box_size, config.TOTAL_POKEMON)
        current_region_index = None
        for i, (rname, rng) in enumerate(sorted_regions):
            if rng[0] <= last_num <= rng[1]:
                current_region_index = i
                break
        if current_region_index is not None and current_region_index > 0:
            new_region_start = sorted_regions[current_region_index - 1][1][0]
            self.current_box = (new_region_start - 1) // self.box_size

    def jump_to_next_region(self):
        """
        Jump to the next region based on which region the last Pokémon in the current box is in.
        """
        region_defs = dex_adapter.get_region_defs()
        sorted_regions = sorted(region_defs.items(), key=lambda item: item[1][0])
        last_num = min(self.current_box * self.box_size + self.box_size, config.TOTAL_POKEMON)
        current_region_index = None
        for i, (rname, rng) in enumerate(sorted_regions):
            if rng[0] <= last_num <= rng[1]:
                current_region_index = i
                break
        if current_region_index is not None and current_region_index < len(sorted_regions) - 1:
            new_region_start = sorted_regions[current_region_index + 1][1][0]
            self.current_box = (new_region_start - 1) // self.box_size

    def get_box_completion(self, box_index: int = -1, exclude_locked: bool = False) -> tuple:
        """
        Calculate completion for the box at the given index.
        Operates on the visible items (the current module items).
        Returns a tuple: (caught_count, total_count, percentage).
        """
        if box_index == -1:
            box_index = self.current_box

        items = self.get_items_for_box(self.current_box)
        if not items:
            return (0, 0, 0)
        caught = 0
        total = 0
        for item in items:
            base = int(str(item.number).split('.')[0])
            if exclude_locked and self._is_locked(base):
                continue
            total += 1
            if self._is_caught(base):
                caught += 1
        percent = (caught / total * 100) if total else 0
        return (caught, total, percent)

    def get_module_completion(self, exclude_locked: bool = False) -> tuple:
        """
        Calculate overall completion for the current module (i.e. for all visible items).
        Returns a tuple: (caught_count, total_count, percentage).
        """
        if not self.visible_items:
            return (0, 0, 0)
        caught = 0
        total = 0
        for item in self.visible_items:
            base = int(str(item.number).split('.')[0])
            if exclude_locked and self._is_locked(base):
                continue
            total += 1
            if self._is_caught(base):
                caught += 1
        percent = (caught / total * 100) if total else 0
        return (caught, total, percent)

    def get_region_completion(self, exclude_locked: bool = False) -> tuple:
        """
        Calculate the completion for the region corresponding to the current box.
        Determines the region based on the highest base number in the current box,
        then counts all visible items in that region.
        Returns a tuple: (region_name, caught_count, total_count, percentage).
        """
        import dex_adapter
        region_defs = dex_adapter.get_region_defs()  # Expected: dict with region names as keys and (start, end) as values.
        sorted_regions = sorted(region_defs.items(), key=lambda item: item[1][0])
        
        box_items = self.get_items_for_current_box()
        if not box_items:
            return ("Unknown", 0, 0, 0)
        
        last_num = max(int(str(item.number).split('.')[0]) for item in box_items)
        current_region = None
        for rname, (r_start, r_end) in sorted_regions:
            if r_start <= last_num <= r_end:
                current_region = rname
                break
        if not current_region:
            current_region = "Unknown"
            return (current_region, 0, 0, 0)
        
        caught = 0
        total = 0
        for item in self.visible_items:
            base = int(str(item.number).split('.')[0])
            r_start, r_end = region_defs[current_region]
            if r_start <= base <= r_end:
                if exclude_locked and self._is_locked(base):
                    continue
                total += 1
                if self._is_caught(base):
                    caught += 1
        percent = (caught / total * 100) if total else 0
        return (current_region, caught, total, percent)

    def get_default_shiny(self) -> bool:
        """
        Return the current module's default_shiny setting.
        If True, the UI should load shiny sprites instead of normal ones.
        """
        return self.default_shiny

    # Internal helper methods to avoid repeated dex_adapter calls.
    def _is_caught(self, base_number: int) -> bool:
        import dex_adapter
        return dex_adapter.is_pokemon_caught(base_number)

    def _is_locked(self, base_number: int) -> bool:
        import dex_adapter
        return dex_adapter.is_pokemon_locked(base_number)
