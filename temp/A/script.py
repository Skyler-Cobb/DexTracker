import pandas as pd
import re

# --- Define Master Lists ---
# Master list of game columns (39 total)
master_game_columns = [
    "Red", "Blue", "Yellow",        # Generation I (3)
    "Gold", "Silver", "Crystal",     # Generation II (3)
    "Ruby", "Sapphire", "FireRed", "LeafGreen", "Emerald",  # Generation III (5)
    "Colosseum", "XD", "Diamond", "Pearl", "Platinum",       # Generation IV (5)
    "HeartGold", "SoulSilver", "Black", "White", "Black2", "White2",  # Generation V (6)
    "X", "Y", "OmegaRuby", "AlphaSapphire",                  # Generation VI (4)
    "Sun", "Moon", "UltraSun", "UltraMoon",                  # Generation VII (4)
    "LetsGoPikachu", "LetsGoEevee", "Sword", "Shield", "BrilliantDiamond", "ShiningPearl",  # Generation VIII (6)
    "LegendsArceus", "Scarlet", "Violet"                       # Generation IX (3)
]
full_game_count = len(master_game_columns)  # 39

# Our intermediate master columns are simply:
intermediate_master = ["#", "Name", "Form"] + master_game_columns

# New columns to be inserted:
# Insert "SwSh-DLC" after Sword/Shield and "SV-DLC" after Scarlet/Violet.
# Then append: "PokeWalker", "DreamRadar", "DreamWorld", "GO", "Home".
def final_columns_order():
    # Start with the initial three columns.
    cols = ["#", "Name", "Form"]
    # For the game columns, we want to insert new columns at specific positions.
    # Our original master_game_columns indices:
    #  32: "Sword", 33: "Shield", 34: "BrilliantDiamond", 35: "ShiningPearl",
    #  36: "LegendsArceus", 37: "Scarlet", 38: "Violet"
    # We'll take:
    # first part: indices 0 to 33 (i.e. up through "Shield")
    part1 = master_game_columns[0:34]
    # Then insert "SwSh-DLC"
    # Then next part: indices 34 to 39 (i.e. "BrilliantDiamond", "ShiningPearl", "LegendsArceus", "Scarlet", "Violet")
    part2 = master_game_columns[34:39]
    # Then insert "SV-DLC"
    cols += part1 + ["SwSh-DLC"] + part2 + ["SV-DLC", "PokeWalker", "DreamRadar", "DreamWorld", "GO", "Home"]
    return cols

# --- Helper Functions ---
def fix_column(col):
    """Collapse repeated words in a header (e.g. 'Name Name' -> 'Name')."""
    parts = col.split()
    if len(parts) > 1 and all(part == parts[0] for part in parts):
        return parts[0]
    return col

def extract_form(name):
    """
    If a Pokémon name contains a parenthetical (e.g. "Rattata (Alolan Form)"),
    return a tuple (clean_name, form) with whitespace trimmed.
    """
    match = re.search(r'\((.*?)\)', name)
    if match:
        form = match.group(1).strip()
        new_name = re.sub(r'\s*\(.*?\)', '', name).strip()
        return new_name, form
    return name, ""

def process_sheet(df):
    # --- Step 1. Drop the unnecessary "Icon Icon" column if present.
    for col in df.columns:
        if col.strip().lower() == "icon icon":
            df = df.drop(columns=[col])
            break

    # --- Step 2. Fix duplicate column names.
    df.columns = [fix_column(str(col)) for col in df.columns]

    # Rename "Number" or "# #" to "#"
    if "Number" in df.columns:
        df = df.rename(columns={"Number": "#"})
    if "# #" in df.columns:
        df = df.rename(columns={"# #": "#"})

    # --- Step 3. Ensure we have "#" and "Name" columns.
    if "#" not in df.columns or "Name" not in df.columns:
        raise ValueError("Sheet is missing '#' or 'Name' columns.")

    # --- Step 4. Reorder columns so that '#' and 'Name' are first.
    # Before counting game columns, drop any extra column known to be spurious.
    drop_list = ["Game Generation I.1", "Generation I.1"]
    current_cols = df.columns.tolist()
    new_cols = current_cols[:2] + [col for col in current_cols[2:] if col not in drop_list]
    df = df[new_cols]

    # --- Step 5. Determine the game columns present.
    # Assume the first two columns are '#' and 'Name'; the rest are game columns.
    n_game = len(df.columns) - 2
    offset = full_game_count - n_game
    if offset < 0 or offset > full_game_count:
        raise ValueError(f"Unexpected number of game columns: {n_game}")
    
    new_game_names = master_game_columns[offset: offset + n_game]
    game_data = df.iloc[:, 2:].copy()
    game_data.columns = new_game_names

    # --- Step 6. Process the "Name" column to extract "Form".
    new_names = []
    forms = []
    for name in df["Name"]:
        name_str = str(name) if pd.notnull(name) else ""
        clean_name, form = extract_form(name_str)
        new_names.append(clean_name)
        forms.append(form)

    # --- Step 7. Build a new DataFrame with the intermediate master columns.
    new_df = pd.DataFrame(columns=intermediate_master)
    new_df["#"] = df["#"]
    new_df["Name"] = new_names
    new_df["Form"] = forms
    for col in new_game_names:
        new_df[col] = game_data[col]
    new_df = new_df.fillna("—")
    return new_df

# --- Process each sheet from the original Excel file ---
all_sheets = pd.read_excel("pokemon_availability.xlsx", sheet_name=None)
processed_dfs = []
for sheet_name, df in all_sheets.items():
    try:
        processed_df = process_sheet(df)
        processed_dfs.append(processed_df)
    except Exception as e:
        print(f"Error processing sheet '{sheet_name}': {e}")

if not processed_dfs:
    raise ValueError("No sheets were processed successfully.")

# --- Combine processed sheets ---
combined_df = pd.concat(processed_dfs, ignore_index=True)
# At this point, combined_df has columns per intermediate_master

# --- Add New Columns and Adjust Values ---
# Initialize new columns with "—"
combined_df["SwSh-DLC"] = "—"
combined_df["SV-DLC"] = "—"
combined_df["PokeWalker"] = "—"
combined_df["DreamRadar"] = "—"
combined_df["DreamWorld"] = "—"
combined_df["GO"] = "—"
combined_df["Home"] = "—"

# Process each row for CD in Sword/Shield and Scarlet/Violet, and for DR/DW.
def update_row(row):
    # For Sword/Shield: if either equals "CD", then change them to "—" and set SwSh-DLC to "C".
    if row.get("Sword", "—") == "CD" or row.get("Shield", "—") == "CD":
        row["Sword"] = "—"
        row["Shield"] = "—"
        row["SwSh-DLC"] = "C"
    # For Scarlet/Violet: if either equals "CD", then change them to "—" and set SV-DLC to "C".
    if row.get("Scarlet", "—") == "CD" or row.get("Violet", "—") == "CD":
        row["Scarlet"] = "—"
        row["Violet"] = "—"
        row["SV-DLC"] = "C"
    # For DreamRadar: if any game column (from the intermediate master game columns) is "DR", mark it.
    for col in master_game_columns:
        if row.get(col, "—") == "DR":
            row["DreamRadar"] = "C"
            break
    # For DreamWorld: if any game column is "DW", mark it.
    for col in master_game_columns:
        if row.get(col, "—") == "DW":
            row["DreamWorld"] = "C"
            break
    return row

combined_df = combined_df.apply(update_row, axis=1)

# --- Reorder Columns to Final Order ---
final_cols = final_columns_order()
combined_df = combined_df[final_cols]

# --- Write to New Excel File ---
output_file = "pokemon_availability_fixed.xlsx"
combined_df.to_excel(output_file, index=False)
print(f"Processing complete. New file saved as '{output_file}'.")
