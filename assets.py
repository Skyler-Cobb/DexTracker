# assets.py
import pygame
import os
import json
import data
import config
from config import (
    DEFAULT_WALLPAPER, UI_COMPONENTS, SPRITE_SIZE, SPRITES, 
    TOTAL_POKEMON, BOX_SIZE, RESOURCES, ERROR_IMAGE, DECORATIONS, CONFIG
)

# Simple in-memory cache for the low-res (64x64) sprites
low_res_cache = {}

# Convert hexadecimal color codes to RGBA tuples
def hex_to_rgba(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 8:  # With alpha channel
        return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4, 6))
    elif len(hex_str) == 6:  # Without alpha channel
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return (r, g, b, 255)
    else:
        return (0, 0, 0, 255)  # Default black color with full opacity

# Load silhouette colors from configuration file
def load_silhouette_colors():
    try:
        with open(CONFIG, "r") as f:
            config_data = json.load(f)
        colors_dict = config_data.get("silhouette_colors", {})
        order = ["gray", "red", "orange", "yellow", "green", "blue", "purple"]
        colors_out = []
        for color_name in order:
            if color_name in colors_dict:
                color_val = hex_to_rgba(colors_dict[color_name])
                colors_out.append(color_val)
        return colors_out if colors_out else [(60, 60, 60, 255)]
    except Exception as e:
        print("Error loading silhouette colors:", e)
        return [(60, 60, 60, 255)]  # Default gray color

SILHOUETTE_COLORS = load_silhouette_colors()

# Create silhouette of a sprite using specified color
def create_silhouette(sprite_surface, color=None):
    if color is None:
        color = SILHOUETTE_COLORS[0]
    sprite_surface = sprite_surface.convert_alpha()
    width, height = sprite_surface.get_size()
    silhouette_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Loop through each pixel of the sprite
    for x in range(width):
        for y in range(height):
            pixel = sprite_surface.get_at((x, y))
            if pixel.a > 0:  # If pixel is not transparent
                new_alpha = int(pixel.a * 0.75)  # Reduce opacity
                silhouette_surface.set_at((x, y), (color[0], color[1], color[2], new_alpha))
            else:
                silhouette_surface.set_at((x, y), (0, 0, 0, 0))  # Keep transparent pixels
    return silhouette_surface

def load_sprite(sprite_filename, shiny=False, female=False, caught=True, custom_color=None, silhouette_color_index=0):
    """
    Loads and returns a sprite with the given parameters.
    
    Parameters:
      - sprite_filename: The base filename of the sprite (e.g., "9-mega.png").
      - shiny: If True, load from the "shiny" subfolder; otherwise, use "normal".
      - female: If True, load from the "female" subfolder.
      - caught: If False, the sprite is converted into a silhouette.
      - custom_color: If provided (as an RGBA tuple), it is used for the silhouette recoloring.
      - silhouette_color_index: Index into SILHOUETTE_COLORS if custom_color isn’t provided.
    
    Returns:
      A pygame Surface representing the (possibly transformed) sprite.
    """
    # Determine the base folder based on shiny and female flags.
    base_folder = os.path.join(SPRITES, "shiny" if shiny else "normal")
    if female:
        base_folder = os.path.join(base_folder, "female")
    
    path = os.path.join(base_folder, sprite_filename)
    
    # Create a unique cache key based on all parameters.
    cache_key = f"{sprite_filename}_{'shiny' if shiny else 'normal'}_{'female' if female else 'male'}_{caught}_{silhouette_color_index}_{custom_color}"
    if cache_key in low_res_cache:
        return low_res_cache[cache_key]
    
    # Attempt to load the sprite from file; fallback to error image if not found.
    if not os.path.isfile(path):
        print("Couldn't find sprite", path)
        sprite = pygame.image.load(ERROR_IMAGE).convert_alpha()
        low_res_cache[cache_key] = sprite
        return sprite
    try:
        sprite = pygame.image.load(path).convert_alpha()
    except Exception as e:
        print("Error loading sprite from", path, e)
        sprite = pygame.image.load(ERROR_IMAGE).convert_alpha()
        low_res_cache[cache_key] = sprite
        return sprite
    
    # If the Pokémon isn't caught, apply the silhouette transformation.
    if not caught:
        if custom_color is not None:
            sprite = create_silhouette(sprite, custom_color)
        else:
            if silhouette_color_index < len(SILHOUETTE_COLORS):
                sprite = create_silhouette(sprite, SILHOUETTE_COLORS[silhouette_color_index])
            else:
                sprite = create_silhouette(sprite, SILHOUETTE_COLORS[0])
    
    low_res_cache[cache_key] = sprite
    return sprite

def preload_adjacent_boxes(current_box, num_boxes, pokedex_data):
    """
    Preloads sprites for adjacent boxes to improve performance.
    Assumes that pokedex_data is a dictionary where each key corresponds to an entry with fields:
      - "image": sprite filename,
      - "shiny": boolean (default False),
      - "female": boolean (default False)
    """
    boxes_to_preload = []
    if current_box - 1 >= 0:
        boxes_to_preload.append(current_box - 1)
    if current_box + 1 < num_boxes:
        boxes_to_preload.append(current_box + 1)
        
    for box in boxes_to_preload:
        start_index = box * BOX_SIZE
        end_index = min(start_index + BOX_SIZE, TOTAL_POKEMON)
        for idx in range(start_index, end_index):
            key = str(idx + 1)
            data = pokedex_data.get(key, {})
            sprite_filename = data.get("image", "")
            shiny = data.get("shiny", False)
            female = data.get("female", False)
            load_sprite(sprite_filename, shiny, female)

def choose_decoration(current_box, current_dex):
    """Picks an appropriate decoration image from the decorations folder
       based on which dex is active and which box number we're on."""
    if current_dex == "formdex":
        # formdex-specific decoration
        formdex_path = os.path.join(UI_COMPONENTS, "decorations", "decoration-formdex.png")
        try:
            return pygame.image.load(formdex_path).convert_alpha()
        except Exception as e:
            print("Error loading formdex decoration:", e)
            return None
    else:
        # National dex decoration logic
        decor_numbers = [1, 152, 252, 387, 494, 650, 722, 810, 891, 906, 1009]
        last_num = min(current_box * BOX_SIZE + BOX_SIZE, TOTAL_POKEMON)
        chosen = decor_numbers[0]
        # Find the highest starter number that's less than the last Pokémon in the box
        for num in decor_numbers:
            if last_num >= num:
                chosen = num
            else:
                break
        filename = f"national-{chosen:04d}.png"
        path = os.path.join(DECORATIONS, filename)
        try:
            return pygame.image.load(path).convert_alpha()
        except Exception as e:
            print("Error loading national decoration:", e)
            return None

def load_wallpaper():
    """Attempt to load the wallpaper image. Returns the Surface (or None on failure)."""
    if os.path.isfile(DEFAULT_WALLPAPER):
        try:
            wallpaper_raw = pygame.image.load(DEFAULT_WALLPAPER)
            print("Wallpaper loaded. Raw size:", wallpaper_raw.get_size())
            return wallpaper_raw
        except Exception as e:
            print("Exception during wallpaper loading:", e)
    else:
        print("Wallpaper file not found at path:", DEFAULT_WALLPAPER)
    return None

def load_ui_images():
    """
    Load UI arrow images from the UI components folder.
    Returns a tuple: (left_arrow, right_arrow) or (None, None) if failed.
    """
    left_path = os.path.join(UI_COMPONENTS, "arrow-left.png")
    right_path = os.path.join(UI_COMPONENTS, "arrow-right.png")
    try:
        left_img = pygame.image.load(left_path).convert_alpha()
        right_img = pygame.image.load(right_path).convert_alpha()
        return left_img, right_img
    except Exception as e:
        print("Failed to load UI arrow images:", e)
        return None, None

def load_form_symbols(name=""):
    """
    Load all form symbols that a given Pokémon has, in order.

    This function uses the data from data.load_form_data(), which returns a dictionary
    mapping Pokémon names to lists of relative image paths representing their forms.
    It then constructs the full image path by combining config.FORM_MARKS (the base directory)
    with each relative path, and loads the images via pygame. If an image file does not exist
    or loading the image fails, an error is printed and that image is skipped.

    Parameters:
        name (str): The name of the Pokémon whose form symbols should be loaded.

    Returns:
        list: A list of pygame Surface objects that represent the form symbols for the Pokémon.
              Returns an empty list if the Pokémon name is not found in the form data.
    """
    # Load the form data from the JSON file via the helper function in data.py.
    form_data = data.load_form_data()
    if name not in form_data:
        return []

    symbols = []
    # Iterate through each relative image path for the given Pokémon.
    for relative_path in form_data[name]:
        # Build the full path using config.FORM_MARKS as the base directory.
        full_path = os.path.join(config.FORM_MARKS, relative_path)
        if os.path.isfile(full_path):
            try:
                # Attempt to load the image using pygame.
                image = pygame.image.load(full_path)
                symbols.append(image)
            except Exception as e:
                print(f"Error loading image at {full_path}: {e}")
        else:
            print(f"Form symbol file not found at path: {full_path}")
    
    return symbols