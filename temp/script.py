import json

# --- Configuration ---

# Keywords to use when matching variant forms.
variant_keywords = [
    "small", "average", "large", "super",
    "red flower", "orange flower", "yellow flower", "blue flower", "white flower",
    "spring", "summer", "fall", "winter",
    "sandy", "trash", "plant", "female",
    "alolan", "galarian", "hisuian", "paldean"
]

def special_removals(entry):
    """
    Return True if this entry's form indicates we should remove its evolution chain.
    """
    form = entry.get("form", "").lower()
    name = entry.get("name", "").lower()
    # Remove chain for any entry with "mega" or "gmax"
    if "mega" in form or "gmax" in form:
        return True
    # For Pikachu forms with "cap" or "partner" in their form.
    if "pikachu" in name and ("cap" in form or "partner" in form):
        return True
    # For Eevee forms with "partner" in their form.
    if "eevee" in name and "partner" in form:
        return True
    return False

def base_number(entry):
    """
    Returns the base species number as a string (the integer portion).
    E.g., for an entry with number "27.01", it returns "27".
    """
    try:
        return str(int(float(entry["number"])))
    except Exception:
        return entry["number"]

def convert_number(num):
    """
    Convert a number (that might be a string) into an integer or a float.
    """
    if isinstance(num, (int, float)):
        return num
    s = str(num)
    if '.' in s:
        try:
            return float(s)
        except Exception:
            return s
    else:
        try:
            return int(s)
        except Exception:
            return s

# --- Load Data ---
with open("items.json", "r") as infile:
    data = json.load(infile)

# Build a lookup for all entries by base species.
entries_by_base = {}
for entry in data:
    bnum = base_number(entry)
    entries_by_base.setdefault(bnum, []).append(entry)

# --- Process Each Entry ---
updated_data = []
for entry in data:
    # If special removal conditions apply, clear evolutions.
    if special_removals(entry):
        entry["evolutions"] = []
        updated_data.append(entry)
        continue

    # Otherwise, trust the given evolution chain.
    # Work on a copy of the chain.
    chain = entry.get("evolutions", []).copy()

    new_chain = []
    for stage in chain:
        # Convert stage to string and get its base version (i.e. integer part)
        stage_str = str(stage)
        base_stage = str(int(float(stage_str)))
        # Start with the stage as provided.
        new_stage = stage
        # If the current entry's form contains one of the variant keywords,
        # try to find a matching entry for this stage among those with the same base.
        entry_form = entry.get("form", "").lower()
        for keyword in variant_keywords:
            if keyword in entry_form:
                # Look among all entries with the same base.
                candidates = entries_by_base.get(base_stage, [])
                for cand in candidates:
                    if keyword in cand.get("form", "").lower():
                        new_stage = cand["number"]
                        break
                break  # use the first matching keyword
        new_chain.append(new_stage)

    # Ensure that the current entry's own number appears in the chain.
    current_num = entry["number"]
    current_base = base_number(entry)
    found = False
    for idx, stage in enumerate(new_chain):
        stage_base = str(int(float(str(stage))))
        if stage_base == current_base:
            if str(stage) == current_num:
                found = True
            else:
                new_chain[idx] = current_num
                found = True
    if not found:
        new_chain.append(current_num)

    # Now convert all stages to numeric types (int or float).
    new_chain = [convert_number(n) for n in new_chain]

    entry["evolutions"] = new_chain
    updated_data.append(entry)

# --- Save Updated Data ---
with open("items_updated.json", "w") as outfile:
    json.dump(updated_data, outfile, indent=4)

print("Evolution chains updated and saved as items_updated.json.")
