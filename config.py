import os

# Determine the base directory of this script.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOTAL_POKEMON = 1025  # Problematic, should have anything using it remade not to

# Box configuration: 5 rows x 6 columns (30 per box)
BOX_SIZE = 30
ROWS = 5
COLUMNS = 6

# Target sprite dimensions (display size)
SPRITE_SIZE = 64

# Spacing & positioning
H_PADDING = 10
V_PADDING = 10
SEARCH_TO_BOX_PADDING = 10
BOX_TO_GRID_PADDING = 30

# File paths (now using BASE_DIR)
SAVE_FILE = os.path.join(BASE_DIR, "save_data.json")
NAME_KEY_FILE = os.path.join(BASE_DIR, "nameKey.json")

# Resource paths
RESOURCES = os.path.join(BASE_DIR, "resources")
IMAGES = os.path.join(RESOURCES, "images")
ERROR_IMAGE = os.path.join(IMAGES, "_err.png")
PLACEHOLDER_IMAGE = os.path.join(IMAGES, "placeholder.png")

PROFILE_COMPONENTS = os.path.join(IMAGES, "profile")
FORM_MARKS = os.path.join(PROFILE_COMPONENTS, "form_marks")
INDICATORS = os.path.join(PROFILE_COMPONENTS, "indicators")
MARKS = os.path.join(PROFILE_COMPONENTS, "marks")
TYPES = os.path.join(PROFILE_COMPONENTS, "types")
SPRITES = os.path.join(PROFILE_COMPONENTS, "sprites")

UI_COMPONENTS = os.path.join(IMAGES, "ui")
DECORATIONS = os.path.join(UI_COMPONENTS, "decorations")
GAMES = os.path.join(UI_COMPONENTS, "games")
WALLPAPERS = os.path.join(UI_COMPONENTS, "wallpapers")
DEFAULT_WALLPAPER = os.path.join(WALLPAPERS, "wallpaper.png")

# Data paths (current)
DATA = os.path.join(RESOURCES, "data")
MODULES = os.path.join(DATA, "modules")
FONTS = os.path.join(DATA, "fonts")
CONFIG = os.path.join(DATA, "config.json")
FORM_SYMBOLS = os.path.join(DATA, "form_symbols.json")
ITEM_DATA = os.path.join(DATA, "items.json")
LOCATION_DATA = os.path.join(DATA, "availability.xlsx")

# Silhouette settings
UNOBTAINED_ALPHA_FRACTION = 0.75
SILHOUETTE_COLORS = [
    (60, 60, 60),    # dark gray (default)
    (255, 0, 0),     # red
    (255, 165, 0),   # orange
    (255, 255, 0),   # yellow
    (0, 255, 0),     # green
    (0, 0, 255),     # blue
    (128, 0, 128)    # purple
]

# Search bar configuration
SEARCH_BAR_HEIGHT = 30
SEARCH_BAR_MARGIN = 50
SEARCH_BAR_Y = 10

SEARCH_BAR_COLOR_ACTIVE = (255, 255, 255)
SEARCH_BAR_COLOR_INACTIVE = (200, 200, 200)
SEARCH_BAR_COLOR_ERROR = (255, 200, 200)
SEARCH_SUGGESTION_HEIGHT = 25
MAX_SUGGESTIONS = 5

# UI Button configuration
BUTTON_WIDTH = 50
BUTTON_HEIGHT = 50

# Brightness adjustment (5% of 255 ~ 13)
BRIGHTNESS_SHIFT = 13

# Default Pokémon Data
DEFAULT_POKEMON_DATA = {
    "caught": False,
    "silhouette_color_index": 0,  # index into SILHOUETTE_COLORS
    "origin_mark": None,
    "form": None,
    "obtainability": None,
    "distribution": None
}

FONT_REGULAR = os.path.join(FONTS, "Comfortaa-Regular.ttf")
FONT_BOLD = os.path.join(FONTS, "Comfortaa-Bold.ttf")
FONT_LIGHT = os.path.join(FONTS, "Comfortaa-Light.ttf")

ALT_REGULAR = os.path.join(FONTS, "Mechanical-g5Y5.otf")
ALT_BOLD = os.path.join(FONTS, "MechanicalBold-oOmA.otf")
ALT_ITALIC = os.path.join(FONTS, "MechanicalOblique-D82m.otf")
ALT_BOLD_ITALIC = os.path.join(FONTS, "MechanicalBoldOblique-aOlo.otf")
