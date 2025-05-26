import json
import sys
import glob
import os
import config
from PIL import Image

# Global module management variables.
_modules = []
_current_module_index = 0

class Item:
    def __init__(self, name, form, image, categories, number, stats, tags=None, marks=None, cosmetic_gender_diff=False, form_symbols=None, games=None, evolutions=None):
        self.name = name
        self.form = form                # e.g., "Mega", "Gmax", "♀", etc.
        self.image = image              # Base image filename, e.g., "521.png"
        self.categories = categories    # Just a different word for "types", e.g. ["Grass", "Poison"]
        self.number = number            # Dex number- may include a decimal value for alt. forms, like 6 for charizard and 6.01 for Mega Charizard X
        
        self.stats = stats if stats is not None else {}
        self.tags = tags if tags is not None else []
        
        # Default values to init a pokemon with if no mark data exists
        default_marks = {
            "flag": False,          # Flag: Whether or not the pokemon is caught
            "lock": False,          # Shiny lock: Is this pokemon shiny locked? This may get phased out in favor of another tracking method later.
            "source": "none.png",   # Source mark: how the pokemon was obtained
            "origin": "none.png",   # Origin mark: where the pokemon was obtained
            "color": "gray",        # Color: how to recolor a silhouette if the sprite isn't being displayed
            "released": True        # Released: Is this pokemon obtainable at all?
        }
        
        if marks is None:
            self.marks = default_marks.copy()
        else:
            # Normalize keys and merge in defaults for any missing keys.
            normalized = {key.lower(): value for key, value in marks.items()}
            for key, default_value in default_marks.items():
                if key not in normalized:
                    normalized[key] = default_value
            self.marks = normalized

        self.cosmetic_gender_diff = cosmetic_gender_diff
        
        # Initialize form_symbols as an empty list if not provided.
        if form_symbols is None:
            self.form_symbols = []
        else:
            self.form_symbols = form_symbols
            
        self.games = games if games is not None else []
        self.evolutions = evolutions if evolutions is not None else []

def load_module(filename):
    """
    Thin wrapper around module_loader.load_module.
    Importing module_loader here (instead of at file import time)
    prevents a circular dependency between data.py and module_loader.py.
    """
    import module_loader          # local, lazy import
    return module_loader.load_module(filename)


def load_modules():
    """Scan the module directory and load all enabled modules."""
    global _modules, _current_module_index
    _modules = []

    # Look for all JSON files, sorted A‑>Z so index 0 is the first module.
    module_files = sorted(
        glob.glob(os.path.join(config.MODULES, "*.json")),
        key=lambda p: os.path.basename(p).lower()
    )

    for filepath in module_files:
        filename = os.path.basename(filepath)
        mod_data = load_module(filename)
        if mod_data:
            _modules.append(mod_data)
    if not _modules:
        _current_module_index = -1
    else:
        _current_module_index = 0
    return _modules

def get_current_module():
    """Return the currently active module data (or None if no modules loaded)."""
    if not _modules:
        load_modules()
    if _modules and _current_module_index >= 0:
        return _modules[_current_module_index]
    return None

def toggle_module():
    """Cycle to the next module and return it."""
    global _current_module_index
    if not _modules:
        load_modules()
    if _modules:
        _current_module_index = (_current_module_index + 1) % len(_modules)
    return get_current_module()

def get_current_module_name():
    """Return the display name of the current module (or 'None')."""
    mod = get_current_module()
    if not mod:
        return "None"
    # module_loader returns {"module": <raw‑json>, ...}
    return mod["module"].get("name", "Unnamed")

def filter_items_by_module(items, search_query=""):
    """
    Filter the given items based on the active module.
    If a search_query is provided, further filter the module's items by that query.
    Returns a tuple: (filtered_items, filtered_dict)
    """
    mod = get_current_module()
    if mod:
        # Use the compiled module filter function to filter items.
        module_filter_func = mod["filter_function"]
        module_items = [item for item in items if module_filter_func(item)]
    else:
        module_items = items
    if search_query:
        # Delegate to the normal search filter (from filter.py) but only on module_items.
        import filter as search_filter
        filtered = search_filter.filter_items(module_items, search_query)
        filtered_dict = {item.number: item for item in filtered}
        return filtered, filtered_dict
    else:
        filtered_dict = {item.number: item for item in module_items}
        return module_items, filtered_dict

def load_items():
    try:
        with open(config.ITEM_DATA, "r") as f:
            data_list = json.load(f)
            items = []
            for item_data in data_list:
                item = Item(
                    name=item_data["name"],
                    form=item_data.get("form", ""),
                    image=item_data["image"],
                    categories=item_data["categories"],
                    number=item_data["number"],
                    stats=item_data.get("stats", {}),
                    tags=item_data.get("tags"),
                    marks=item_data.get("marks"),
                    cosmetic_gender_diff=item_data.get("cosmetic_gender_diff", False),
                    form_symbols=item_data.get("form_symbols", []),
                    games=item_data.get("games", []),
                    evolutions=item_data.get("evolutions", [])
                )
                items.append(item)
            # Compute alternate forms.
            base_dict = {}
            for item in items:
                base = item.number.split('.')[0]
                base_dict.setdefault(base, []).append(item)
            for base, forms in base_dict.items():
                has_alternate = len(forms) > 1
                for item in forms:
                    item.has_alternate = has_alternate
            return items
    except FileNotFoundError:
        return []

def save_items(items):
    data_list = []
    for item in items:
        data_list.append({
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
            "evolutions": item.evolutions
        })
    with open(config.ITEM_DATA, "w") as f:
        json.dump(data_list, f, indent=4)

def get_item_by_number(number, items):
    for item in items:
        if item.number == number:
            return item
    return None

def get_item_info(item, keys):
    return {key: getattr(item, key) for key in keys}

def load_image(image_path, form=""):
    """
    Loads an image given its path relative to the "resources/" directory.
    If the provided form contains the female symbol "♀", this function
    inserts "female/" into the path so that the female sprite is loaded,
    but only if it's not already in the path.
    """
    if "♀" in form and not image_path.startswith("female/"):
        parts = image_path.split("/")
        if len(parts) > 1:
            parts.insert(1, "female")
            image_path = "/".join(parts)
        else:
            image_path = "female/" + image_path
    try:
        return Image.open(image_path)
    except Exception:
        print("Image not found:", image_path)
        return Image.open(config.ERROR_IMAGE)

    
def format_number(num_str):
    num_str = str(num_str)
    if "." in num_str:
        base, dec = num_str.split(".")
        return f"[#{int(base):04d}.{dec}]"
    else:
        return f"[#{int(num_str):04d}]"

def load_form_data():
    try:
        with open(config.FORM_SYMBOLS, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def filter_items(items, mode):
    filtered_items = []
    filtered_dict = {}
    if mode == "overview":
        for item in items:
            if '.' not in str(item.number):
                filtered_items.append(item)
                filtered_dict[item.number] = item
    elif mode == "variant":
        variant_whole_numbers = set()
        for item in items:
            num_str = str(item.number)
            if '.' in num_str:
                whole = num_str.split('.')[0]
                variant_whole_numbers.add(whole)
        for item in items:
            num_str = str(item.number)
            if '.' in num_str or ('.' not in num_str and num_str in variant_whole_numbers):
                filtered_items.append(item)
                filtered_dict[item.number] = item
    elif mode == "complete":
        for item in items:
            filtered_items.append(item)
            filtered_dict[item.number] = item
    return filtered_items, filtered_dict

def get_form_items(items, base_number):
    form_items = [i for i in items if i.number.split('.')[0] == base_number]
    form_items.sort(key=lambda i: float(i.number))
    return form_items

if __name__ == "__main__":
    if len(sys.argv) > 1:
        number = sys.argv[1]
        keys = []
        if len(sys.argv) > 2:
            if sys.argv[2].startswith("[") and sys.argv[-1].endswith("]"):
                keys_str = " ".join(sys.argv[2:])
                keys_str = keys_str.strip("[]")
                keys = [k.strip().strip('"').strip("'") for k in keys_str.split(",")]
            else:
                keys = sys.argv[2:]
        items = load_items()
        item = get_item_by_number(number, items)
        if item:
            image = load_image(item.image, form=item.form)
            print(get_item_info(item, keys))
        else:
            print("Item not found")
