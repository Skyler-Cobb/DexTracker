# dex_adapter.py

import os
import json
import pygame
import glob

# Use the new data.py (formerly infoRetrieval.py) as our primary data source.
import data as data_mod
import assets      # For functions like hex_to_rgba, create_silhouette, and sprite cache management.
import ui          # For UI helper functions.
import filter as filter_mod  # Retained for legacy filter support.

from config import CONFIG, DATA, TOTAL_POKEMON, BOX_SIZE, UI_COMPONENTS, MODULES

# Global in-memory structures
_items = []         # List of items (Item objects) loaded from data.py.
_items_dict = {}    # Dictionary mapping item number (as string) to the corresponding Item.
_name_key = {}      # Legacy name key (loaded from nameKey.json).
_config_data = {}   # Configuration data loaded from CONFIG.
_region_defs = {}   # Region definitions loaded from DATA/region_definitions.json.
_ui_image_cache = None

# UI state variables
_current_mode = "search"  # Can be 'search' or 'filter', etc.
_editing_mode = False

# Legacy mark mode (e.g. 0 => show all, 1 => show only GO, 2 => off)
_mark_mode = 0


##########################
# Region definitions
##########################
def get_region_defs():
    """
    Return the region definitions loaded from the configuration.
    """
    return _region_defs


##########################
# Initialization and saving
##########################
def init_adapter():
    """
    Initialize the adapter:
      - Load items via the new data.py and build a lookup dict.
      - Load modules for module management.
      - Load the legacy nameKey.json (if available).
      - Load config data and region definitions.
    """
    global _items, _items_dict, _name_key, _config_data, _region_defs

    # Load items using the new system.
    _items = data_mod.load_items()
    _items_dict = {str(item.number): item for item in _items}

    # Initialize module management.
    data_mod.load_modules()

    # Load legacy nameKey.json for backward compatibility.
    name_key_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nameKey.json")
    if os.path.isfile(name_key_path):
        try:
            with open(name_key_path, "r", encoding="utf-8") as f:
                _name_key = json.load(f)
        except Exception as e:
            print("Error loading nameKey.json:", e)
            _name_key = {}
    else:
        print("nameKey.json not found!")
        _name_key = {}

    # Load configuration data.
    try:
        with open(CONFIG, "r") as f:
            _config_data = json.load(f)
    except Exception as e:
        print("Error loading config.json:", e)
        _config_data = {}

    # Load region definitions.
    region_def_path = os.path.join(DATA, "region_definitions.json")
    try:
        with open(region_def_path, "r") as f:
            _region_defs = json.load(f)
    except Exception as e:
        print("Error loading region_definitions.json:", e)
        _region_defs = {}


def save_all_changes():
    """
    Save all changes to items by delegating to data.py's save_items.
    """
    global _items
    data_mod.save_items(_items)


##########################
# Configuration & UI settings
##########################
def get_config_data():
    """
    Return the loaded configuration data.
    """
    return _config_data


def get_poke_grid_scale():
    """
    Return the user-defined grid scale factor from the config data.
    """
    return _config_data.get("poke_grid_scale", 0.9)


def get_ui_opacity():
    """
    Return the UI opacity from the config data.
    """
    return _config_data.get("UI_opacity", 0.9)


def get_filtered_out_color():
    """
    Return the RGBA color for 'filtered_out' using the assets.hex_to_rgba function.
    """
    color_str = _config_data.get("filtered_out", "#00000030")
    return assets.hex_to_rgba(color_str)


def load_wallpaper():
    """
    Wrap assets.load_wallpaper().
    """
    return assets.load_wallpaper()


def set_current_mode(mode: str):
    global _current_mode
    _current_mode = mode


def get_current_mode():
    return _current_mode


def toggle_editing_mode():
    global _editing_mode
    _editing_mode = not _editing_mode


def is_editing_mode():
    return _editing_mode


##########################
# Module and legacy name key handling
##########################
def module_switch():
    """
    Actually switch to the next module by calling data.py's toggle_module,
    ensuring we use the single module list managed by data.py.
    """
    return data_mod.toggle_module()



def get_current_module():
    """
    Retrieve the current module data from data.py.
    """
    return data_mod.get_current_module()


def get_current_module_name():
    """
    Return the display name of the current module (or 'None').
    Works with both the new and legacy structures.
    """
    mod = get_current_module()
    if not mod:
        return "None"
    # prefer the convenience field we just added
    if "name" in mod:
        return mod["name"]
    # fall back to legacy nesting
    return mod.get("module", {}).get("name", "None")

def get_default_shiny():
    """
    Return the default_shiny flag from the current module.
    If not set, defaults to False.
    """
    mod = get_current_module()
    if mod is None:
        return False
    return mod.get("default_shiny", False)




##########################
# Item and Pokémon data access (new system)
##########################
def get_items():
    """
    Return the list of loaded Item objects.
    """
    return _items


def get_items_dict():
    """
    Return a dictionary mapping item numbers (as strings) to their Item objects.
    """
    return _items_dict


def get_pokemon_name(numeric_id: int) -> str:
    """
    Return a Pokémon's name by searching for its item in _items_dict.
    Falls back to the legacy name key if necessary.
    """
    item = _items_dict.get(str(numeric_id))
    if item:
        return item.name
    for name, num in _name_key.items():
        if num == numeric_id:
            return name
    return "Unknown"


def get_pokemon_info(numeric_id: int):
    """
    Retrieve the Item corresponding to the given numeric_id.
    """
    return _items_dict.get(str(numeric_id))


def is_pokemon_caught(numeric_id: int) -> bool:
    """
    Return True if the Pokémon (as an Item) is marked as caught.
    """
    item = _items_dict.get(str(numeric_id))
    if item and item.marks:
        return bool(item.marks.get("flag", False))
    return False


def set_pokemon_caught(numeric_id: int, caught: bool):
    """
    Set the caught status for the Pokémon and save changes.
    """
    item = _items_dict.get(str(numeric_id))
    if item and item.marks is not None:
        item.marks["flag"] = caught
        save_all_changes()


def toggle_pokemon_caught(numeric_id: int):
    """
    Toggle the caught status for the Pokémon.
    Invalidate the sprite cache if necessary.
    """
    item = _items_dict.get(str(numeric_id))
    if item and item.marks is not None:
        current = bool(item.marks.get("flag", False))
        item.marks["flag"] = not current
        if str(numeric_id) in assets.low_res_cache:
            del assets.low_res_cache[str(numeric_id)]
        save_all_changes()


def set_form_caught(nat_key: str, form_key: str, caught: bool):
    """
    For formdex usage: set the caught status for a specific form.
    This implementation finds the matching item based on its number.
    """
    for item in _items:
        if item.number == form_key:
            item.marks["flag"] = caught
            save_all_changes()
            break


def toggle_form_caught(nat_key: str, form_key: str):
    """
    Toggle the caught status for a specific form.
    """
    for item in _items:
        if item.number == form_key:
            current = bool(item.marks.get("flag", False))
            item.marks["flag"] = not current
            save_all_changes()
            break


def get_origin_mark(numeric_id: int):
    """
    Return the origin mark for the Pokémon.
    """
    item = _items_dict.get(str(numeric_id))
    if item and item.marks:
        return item.marks.get("origin", None)
    return None


def set_origin_mark(numeric_id: int, mark_filename: str or None):
    """
    Set the origin mark for the Pokémon and save changes.
    """
    item = _items_dict.get(str(numeric_id))
    if item:
        item.marks["origin"] = mark_filename
        save_all_changes()


def filter_items_by_module(search_query=""):
    """
    Filter items based on the current module and an optional search query.
    Delegates to data.py's filter_items_by_module.
    Returns a tuple: (filtered_items, filtered_dict).
    """
    filtered_items, filtered_dict = data_mod.filter_items_by_module(_items, search_query)
    return filtered_items, filtered_dict


def load_item_image(numeric_id: int, form_key=None):
    """
    Load and return the image for the given Pokémon.
    Delegates to data.py's load_image to handle forms and special cases.
    """
    item = _items_dict.get(str(numeric_id))
    if item:
        image_path = item.image
        return data_mod.load_image(image_path, form=item.form if not form_key else form_key)
    error_path = os.path.join(assets.RESOURCE_FOLDER, "sprites", "_err.png")
    return pygame.image.load(error_path).convert_alpha()

def get_catch_methods(pokemon_id, game_id):
    """
    Retrieve the encounter methods for a given Pokémon in a specific game.
    The Pokémon info is expected to have a 'games' attribute that is a list of dictionaries,
    each with keys "game" and "encounter_methods". Game names are normalized by lowercasing
    and removing dashes/spaces to match internal keys.
    """
    # Get the Pokémon info (this function should already exist in your module).
    info = get_pokemon_info(pokemon_id)
    if not info or not hasattr(info, "games"):
        return []
    # Normalize the target game_id.
    normalized_target = game_id.lower().replace("-", "").replace(" ", "")
    for entry in info.games:
        game_name = entry.get("game", "")
        normalized_game = game_name.lower().replace("-", "").replace(" ", "")
        if normalized_game == normalized_target:
            # Return the encounter_methods list if available.
            return entry.get("encounter_methods", [])
    return []

# --- Module‑aware item helpers ---------------------------------------------
def get_visible_items():
    """
    Return the list of Item objects that pass the *current* module filter.
    Cached for the duration of a frame.
    """
    items, _ = data_mod.filter_items_by_module(_items)
    return items

def get_visible_numbers():
    """Convenience: list of item.number strings in the current module."""
    return [itm.number for itm in get_visible_items()]

def get_visible_count():
    return len(get_visible_items())


##########################
# Legacy functions (dummy or simple wrappers)
##########################
def get_pokedex_data():
    """
    Legacy: Return a dictionary representation of all items from items.json.
    Each key is the item's number (as a string) and the value is a dictionary
    containing all properties from the item. It also provides legacy keys:
      - "caught": equivalent to marks["flag"]
      - "silhouette_color_index": from marks if available, defaults to 0.
    """
    legacy_data = {}
    for key, item in _items_dict.items():
        legacy_data[key] = {
            "name": item.name,
            "form": item.form,
            "image": item.image,
            "categories": item.categories,
            "number": item.number,
            "stats": item.stats,
            "tags": item.tags,
            "marks": item.marks,
            "cosmetic_gender_diff": item.cosmetic_gender_diff,
            "form_symbols": item.form_symbols,
            "games": item.games,
            "evolutions": item.evolutions,
            # Legacy aliases for compatibility with assets.load_sprite:
            "caught": item.marks.get("flag", False),
            "silhouette_color_index": item.marks.get("silhouette_color_index", 0)
        }
    return legacy_data


def get_save_data():
    """
    Legacy: Return save data.
    In the new system, all changes are stored in items.
    This dummy implementation returns an empty dict.
    """
    return {}


def pokemon_caught(numeric_id: int) -> bool:
    """
    Legacy alias for is_pokemon_caught.
    """
    return is_pokemon_caught(numeric_id)


def pokemon_locked(numeric_id: int) -> bool:
    """
    Legacy: Return True if the Pokémon is locked.
    Dummy implementation always returns False.
    """
    return False


def get_current_box_list(current_box: int):
    """
    Return a list of Pokémon numbers for the specified box.
    """
    from config import TOTAL_POKEMON, BOX_SIZE
    start = current_box * BOX_SIZE + 1
    end = min(current_box * BOX_SIZE + BOX_SIZE, TOTAL_POKEMON)
    return list(range(start, end + 1))


def set_silhouette_color_index(numeric_id: int, index: int):
    """
    Update the silhouette color index for the given Pokémon.
    """
    item = _items_dict.get(str(numeric_id))
    if item:
        item.marks["silhouette_color_index"] = index
        save_all_changes()


def get_silhouette_color_index(numeric_id: int) -> int:
    """
    Return the silhouette color index for the given Pokémon.
    """
    item = _items_dict.get(str(numeric_id))
    if item:
        return item.marks.get("silhouette_color_index", 0)
    return 0


def create_silhouette(surface, color):
    """
    Wrap assets.create_silhouette.
    """
    return assets.create_silhouette(surface, color)


def load_decoration(current_box: int, current_dex: str):
    """
    Wrap assets.choose_decoration to load a decoration based on box and dex.
    """
    return assets.choose_decoration(current_box, current_dex)


def filter_item(item_dict: dict, filter_text: str) -> bool:
    """
    Legacy: Filter a single item dict.
    Delegates to filter_mod.filter_item.
    """
    try:
        return filter_mod.filter_item(item_dict, filter_text)
    except Exception as e:
        print(f"Error filtering item {item_dict.get('key','?')}: {e}")
        return False


def bulk_filter_items(all_items: list, filter_text: str) -> dict:
    """
    Legacy: For a list of item dicts, return a dict mapping keys to whether they passed the filter.
    """
    results = {}
    for item_dict in all_items:
        key = item_dict.get("key")
        if key:
            results[key] = filter_item(item_dict, filter_text)
    return results


def build_item_dict(numeric_id: int) -> dict:
    """
    Legacy: Build a dict for filtering purposes.
    """
    key = str(numeric_id)
    d = {"key": key}
    item = _items_dict.get(key)
    if item:
        d.update({
            "caught": item.marks.get("flag", False),
            "silhouette_color_index": item.marks.get("silhouette_color_index", 0),
            "origin_mark": item.marks.get("origin", None),
            "form": item.form
        })
    return d


def set_pokemon_locked(numeric_id: int, locked: bool):
    """
    Legacy: Set the locked status for the Pokémon.
    Dummy implementation: store in marks under 'locked'.
    """
    item = _items_dict.get(str(numeric_id))
    if item:
        item.marks["locked"] = locked
        save_all_changes()


def get_mark_mode() -> int:
    """
    Legacy: Return the current mark mode.
    """
    return _mark_mode


def set_mark_mode(mode: int):
    """
    Legacy: Set the current mark mode.
    """
    global _mark_mode
    _mark_mode = mode


##########################
# UI image and font loading
##########################
def load_source_mark(filename):
    """
    Load a source mark with a given filename.
    """
    path = os.path.join("source",filename)
    return data_mod.load_icon(path)

def load_origin_mark(filename):
    """
    Load an origin mark with a given filename.
    """
    path = os.path.join("origin",filename)
    return data_mod.load_icon(path)

def load_mark_images(marks_folder):
    """
    Load mark images from the specified folder.
    Returns a dict mapping filenames to loaded pygame.Surface objects.
    """
    mark_images = {}
    try:
        for filename in os.listdir(marks_folder):
            if filename.lower().endswith(".png"):
                path = os.path.join(marks_folder, filename)
                mark_images[filename] = pygame.image.load(path).convert_alpha()
    except Exception as e:
        print("Error loading mark images:", e)
    return mark_images


def load_ui_images():
    """
    Load UI images.
    This function scans the folder for PNG files and returns a dictionary mapping filenames to loaded images.
    """
    ui_images = {}
    try:
        for filename in os.listdir(UI_COMPONENTS):
            if filename.lower().endswith(".png"):
                path = os.path.join(UI_COMPONENTS, filename)
                ui_images[filename] = pygame.image.load(path).convert_alpha()
    except Exception as e:
        print("Error loading ui images:", e)
    return ui_images


def safe_load_icon(filename: str, location: str = UI_COMPONENTS):
    """
    Safely load an icon image from the UI components folder.
    If loading fails, returns None.
    """
    path = os.path.join(location, filename)
    try:
        return pygame.image.load(path).convert_alpha()
    except Exception as e:
        print(f"Failed to load icon '{filename}': {e}")
        return None

def load_sprite(numeric_id: int, shiny: bool = None, female: bool = None, 
                caught: bool = None, silhouette_color_index: int = None):
    legacy_data = get_pokedex_data()
    key = str(numeric_id)
    item_data = legacy_data.get(key, {})
    sprite_filename = item_data.get("image", "")
    # Use explicit parameter if provided; otherwise, fall back to legacy data.
    if shiny is None:
        shiny = item_data.get("shiny", False)
    # Override shiny based on the current module's default setting.
    if get_default_shiny():
        shiny = True
    if female is None:
        female = item_data.get("female", False)
    if caught is None:
        caught = item_data.get("caught", False)
    if silhouette_color_index is None:
        silhouette_color_index = item_data.get("silhouette_color_index", 0)
    return assets.load_sprite(
        sprite_filename, 
        shiny=shiny, 
        female=female, 
        caught=caught, 
        silhouette_color_index=silhouette_color_index
    )


def load_font(font_path, size):
    """
    Attempt to load a TTF font. If that fails, fallback to pygame's default font.
    """
    try:
        return pygame.font.Font(font_path, size)
    except Exception as e:
        print(f"Font load error {font_path}: {e}")
        return pygame.font.SysFont(None, size)

def render_text_with_fallback(text, main_font, fallback_font, color):
    """
    Render text using the main_font for most characters but use fallback_font
    for any character in the fallback_set.
    """
    fallback_set = {"\u2642", "\u2640"}
    surfaces = []
    total_width = 0
    max_height = 0
    for char in text:
        # If the character is one of the missing symbols, use the fallback font.
        if char in fallback_set:
            surf = fallback_font.render(char, True, color)
        else:
            surf = main_font.render(char, True, color)
        surfaces.append(surf)
        total_width += surf.get_width()
        max_height = max(max_height, surf.get_height())
    # Create a surface to composite all the characters.
    result = pygame.Surface((total_width, max_height), pygame.SRCALPHA)
    x = 0
    for surf in surfaces:
        result.blit(surf, (x, 0))
        x += surf.get_width()
    return result


def get_ui_image(filename):
    """
    Return a specific UI image by filename.
    Uses a cache to avoid reloading images on every call.
    """
    global _ui_image_cache
    if _ui_image_cache is None:
        _ui_image_cache = load_ui_images()
    image = _ui_image_cache.get(filename)
    if image is None:
        print(f"UI image '{filename}' not found.")
    return image
