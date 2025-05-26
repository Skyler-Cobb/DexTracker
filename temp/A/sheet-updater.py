import pandas as pd
import re

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

# Final master column order: "#", "Name", "Form", then all game columns
master_columns = ["#", "Name", "Form"] + master_game_columns

def fix_column(col):
    """
    Collapse repeated words in a header (e.g. 'Name Name' -> 'Name').
    """
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
        # Remove the parenthetical portion from the name.
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
    # Also, before counting game columns, drop any extra column known to be spurious.
    # According to instructions, "Game Generation I.1" should be removed.
    drop_list = ["Game Generation I.1", "Generation I.1"]
    current_cols = df.columns.tolist()
    # Keep first two columns (# and Name) then filter out any column in drop_list.
    new_cols = current_cols[:2] + [col for col in current_cols[2:] if col not in drop_list]
    df = df[new_cols]

    # --- Step 5. Determine the game columns present.
    # Assume the first two columns are '#' and 'Name'; the rest are game columns.
    n_game = len(df.columns) - 2
    # Calculate offset: how many columns (from the left of master_game_columns) are missing.
    offset = full_game_count - n_game
    if offset < 0 or offset > full_game_count:
        raise ValueError(f"Unexpected number of game columns: {n_game}")
    
    # Assign new names for the game columns from the master list.
    new_game_names = master_game_columns[offset: offset + n_game]
    # Get the game data and override their column names.
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

    # --- Step 7. Create a new DataFrame with all master columns.
    new_df = pd.DataFrame(columns=master_columns)
    new_df["#"] = df["#"]
    new_df["Name"] = new_names
    new_df["Form"] = forms

    # For game columns, fill in the ones present from the sheet.
    for col in new_game_names:
        new_df[col] = game_data[col]
    # For any master game column not present in this sheet, they remain missing.
    # Fill all missing values with dash.
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

# --- Combine all processed sheets ---
if processed_dfs:
    combined_df = pd.concat(processed_dfs, ignore_index=True)
    # Reorder columns to the master order.
    combined_df = combined_df[master_columns]
    # Write the combined DataFrame to a new Excel file.
    output_file = "pokemon_availability_fixed.xlsx"
    combined_df.to_excel(output_file, index=False)
    print(f"Processing complete. New file saved as '{output_file}'.")
else:
    print("No sheets were processed successfully.")
