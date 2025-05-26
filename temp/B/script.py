import json
import pandas as pd

# Mapping for normally obtainable abbreviations (except for D which needs special handling)
obt_map = {
    "C": "Can be caught.",
    "S": "Can be caught at certain times.",
    "R": "Can be Received as a gift.",
    "E": "Evolve a previous stage.",
    "B": "Breed a later evolution.",
    "DA": "Can be caught in Dynamax Adventures.",
    "CC": "Can be caught via communication with another game.",
    "FS": "Can be caught in the Friend Safari."
}

# Define which games get the special "D" meaning
dual_slot_games = {"Diamond", "Pearl", "Platinum"}
max_raids_games = {"Sword", "Shield"}

# Define set of normally obtainable abbreviations (including D)
normally_obtainable = set(obt_map.keys()).union({"D"})

# Read the availability data from the Excel file.
# It is assumed that the Excel file has a header row and contains at least:
#   - A "Name" column (and optionally a "Form" column) to match the JSON Pokémon.
#   - Other columns whose headers are the game names.
df = pd.read_excel("availability.xlsx")

# Load the existing Pokémon data from items.json.
with open("items.json", "r") as f:
    items = json.load(f)

# Loop over each row in the Excel file.
for idx, row in df.iterrows():
    # Get the Pokémon's name and form (if available)
    pokemon_name = str(row["Name"]).strip()
    pokemon_form = ""
    if "Form" in df.columns:
        pokemon_form = str(row["Form"]).strip() if pd.notna(row["Form"]) else ""

    # Find matching Pokémon in the JSON (match on name and form, case-insensitive)
    matching_items = [
        item for item in items
        if item["name"].strip().lower() == pokemon_name.lower() and
           item.get("form", "").strip().lower() == pokemon_form.lower()
    ]

    if not matching_items:
        print(f"Warning: No matching Pokémon found for {pokemon_name} ({pokemon_form})")
        continue

    # Process every game column (skip the Name/Form columns)
    for col in df.columns:
        if col in ["Name", "Form"]:
            continue

        cell_value = row[col]
        if pd.isna(cell_value):
            continue

        cell_value = str(cell_value).strip()
        # Only process if the cell's value is one of the normally obtainable abbreviations.
        if cell_value not in normally_obtainable:
            continue

        # Determine the encounter text for this cell.
        if cell_value == "D":
            if col in dual_slot_games:
                encounter_text = "Can be caught in dual-slot mode."
            elif col in max_raids_games:
                encounter_text = "Available in Max Raids."
            else:
                # If the game column is not recognized for a special D meaning,
                # you might want to skip or log a message. Here we simply ignore it.
                continue
        else:
            encounter_text = obt_map[cell_value]

        # For each matching Pokémon, add this encounter info under the correct game.
        for item in matching_items:
            # Look for an existing entry for this game.
            game_entry = next((entry for entry in item["games"] if entry["game"] == col), None)
            if game_entry:
                # Append the encounter method if not already present.
                if encounter_text not in game_entry["encounter_methods"]:
                    game_entry["encounter_methods"].append(encounter_text)
            else:
                # If no entry exists, create a new one.
                item["games"].append({
                    "game": col,
                    "encounter_methods": [encounter_text]
                })

# Save the updated data to a new JSON file.
with open("items_updated.json", "w") as f:
    json.dump(items, f, indent=4)

print("Availability data has been merged and saved to items_updated.json")
