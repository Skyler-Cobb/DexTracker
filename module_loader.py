# module_loader.py

import os
import json
import re
import importlib

from config import MODULES  # path to your modules directory
import data  # your data.py, for Item & load_items()


# ----------------------------------------------------------------------------- 
# Region ranges for exclusion filters 
# -----------------------------------------------------------------------------
REGION_RANGES = {
    "Kanto":   (1,   151),
    "Johto":   (152, 251),
    "Hoenn":   (252, 386),
    "Sinnoh":  (387, 493),
    "Unova":   (494, 649),
    "Kalos":   (650, 721),
    "Alola":   (722, 807),
    "Unknown": (808, 809),
    "Galar":   (810, 898),
    "Hisui":   (899, 905),
    "Paldea":  (906, 1025),
}

# ----------------------------------------------------------------------------- 
# Build the logical filter string from the module JSON 
# -----------------------------------------------------------------------------
def build_module_filter_string(mod: dict) -> str:
    tokens = []
    # 1) explicit filter_constraints
    fc = mod.get("filter_constraints", "").strip()
    if fc:
        tokens.append(f"({fc})")

    # 2) region exclusions
    for region, enabled in mod.get("regions", {}).items():
        if not enabled and region in REGION_RANGES:
            start, end = REGION_RANGES[region]
            tokens.append(f"#{start}-{end}f")

    # 3) home_compatible_variants → by_form_name
    hcv = mod.get("home_compatible_variants", {})
    for form, inc in hcv.get("by_form_name", {}).items():
        if not inc:
            tokens.append(f"form:{form.lower()}")

    # 4) home_compatible_variants → by_species_name
    species = [s.lower() for s, inc in hcv.get("by_species_name", {}).items() if not inc]
    if species:
        tokens.append(f"(({ ' OR '.join(species) }) AND form:variant)")

    # 5) hcv special_handling
    for key, inc in hcv.get("special_handling", {}).items():
        if not inc:
            kl = key.lower()
            if kl == "gender_cosmetic":
                tokens.append("form:♀")
            elif kl == "gender_forms":
                tokens.append("form:female")
            elif kl == "alcremie_sweets":
                tokens.append("#869.01-869.06f")
            elif kl == "alcremie_full":
                tokens.append("#869.07-869.62f")
            elif kl == "zygarde":
                tokens.append("(zygarde AND form:variant)")
            elif kl == "zygarde_power_construct":
                tokens.append("(zygarde AND form:construct)")
            elif kl == "minior_core":
                tokens.append("(minior AND NOT form:meteor AND form:variant)")
            elif kl == "pikachu_hat":
                tokens.append("(pikachu AND form:cap)")
            else:
                tokens.append(kl)

    # 6) home_incompatible_variants (similar breakdown)
    hiv = mod.get("home_incompatible_variants", {})
    # 6a) battle_forms.by_species_name
    bs = [s.lower() for s, inc in hiv.get("battle_forms", {}).get("by_species_name", {}).items() if not inc]
    if bs:
        tokens.append(f"(({ ' OR '.join(bs) }) AND form:variant)")
    # 6b) battle_forms.by_form_name
    for form, inc in hiv.get("battle_forms", {}).get("by_form_name", {}).items():
        if not inc:
            tokens.append(f"form:{form.lower()}")
    # 6c) item_forms.by_species_name
    ispec = [s.lower() for s, inc in hiv.get("item_forms", {}).get("by_species_name", {}).items() if not inc]
    if ispec:
        tokens.append(f"(({ ' OR '.join(ispec) }) AND form:variant)")
    # 6d) item_forms.by_form_name
    for form, inc in hiv.get("item_forms", {}).get("by_form_name", {}).items():
        if not inc:
            tokens.append(f"form:{form.lower()}")
    # 6e) hiv special_handling
    for key, inc in hiv.get("special_handling", {}).items():
        if not inc:
            kl = key.lower()
            if kl == "fusion":
                tokens += ["#646.01f", "#646.02f", "#800.01f", "#800.02f", "#898.01f", "#898.02f"]
            elif kl == "pikachu_cosplay":
                tokens.append("#25.01-25.06f")
            elif kl == "lgpe_partner":
                tokens += ["#25.15", "#133.01"]
            elif kl == "floette_eternal":
                tokens.append("#670.05f")
            elif kl == "minior_meteor":
                tokens.append("(form:meteor AND form:variant)")
            elif kl == "therian":
                tokens.append("form:therian")
            else:
                tokens.append(kl)

    if tokens:
        return "NOT (" + " OR ".join(tokens) + ")"
    return ""

# ----------------------------------------------------------------------------- 
# Recursive‑descent compiler to turn filter string into a Python boolean expr 
# -----------------------------------------------------------------------------
def tokenize_code(s: str):
    s = re.sub(r'([\(\)])', r' \1 ', s)
    s = s.replace("!", " ! ")
    s = re.sub(r'\b(OR|NOT|XOR)\b', r' \1 ', s, flags=re.IGNORECASE)
    s = s.replace("||", " || ")
    return s.split()

# We’ll import your existing match_* functions from the legacy filter.py:
from filter import (
    match_name_filter, match_number_filter, match_number_str_filter,
    match_number_range_filter, match_category_filter, match_tag_filter,
    match_form_filter, match_mark_filter, match_color_filter, match_stat_filter,
    match_in_filter, match_method_filter, match_source_filter, match_evol_filter
)

def code_for_term(term_type, value):
    M = {
        "name":         "match_name_filter",
        "number":       "match_number_filter",
        "number_str":   "match_number_str_filter",
        "number_range": "match_number_range_filter",
        "category":     "match_category_filter",
        "tag":          "match_tag_filter",
        "form":         "match_form_filter",
        "mark":         "match_mark_filter",
        "color":        "match_color_filter",
        "stat":         "match_stat_filter",
        "in":           "match_in_filter",
        "method":       "match_method_filter",
        "source":       "match_source_filter",
        "evol":         "match_evol_filter",
    }
    if term_type not in M:
        raise ValueError(f"Unknown term type: {term_type}")
    return f"{M[term_type]}(item, {repr(value)})"

def compile_filter_string(s: str) -> str:
    expr, idx = code_parse_or(tokenize_code(s), 0)
    if idx != len(tokenize_code(s)):
        raise ValueError("Trailing tokens")
    return expr

def code_parse_primary(tokens, i):
    if tokens[i] == "(":
        i += 1
        expr, i = code_parse_or(tokens, i)
        if tokens[i] != ")":
            raise ValueError("Expected ')'")
        return expr, i+1
    tok = tokens[i]; i+=1
    from filter import _parse_filter_term
    tt, val = _parse_filter_term(tok)
    return code_for_term(tt, val), i

def code_parse_not(tokens, i):
    if tokens[i] in ("!",) or tokens[i].upper()=="NOT":
        cnt=0
        while tokens[i] in ("!",) or tokens[i].upper()=="NOT":
            cnt+=1; i+=1
        operand, i = code_parse_not(tokens, i)
        return (f"(not {operand})", i) if cnt%2 else (operand, i)
    return code_parse_primary(tokens, i)

def code_parse_and(tokens, i):
    left, i = code_parse_not(tokens, i)
    while i<len(tokens) and tokens[i] not in (")","OR","||","XOR"):
        if tokens[i].upper() in ("AND","&&"):
            i+=1; continue
        right, i = code_parse_not(tokens, i)
        left = f"({left} and {right})"
    return left, i

def code_parse_xor(tokens, i):
    left, i = code_parse_and(tokens, i)
    while i<len(tokens) and tokens[i].upper()=="XOR":
        i+=1
        right, i = code_parse_and(tokens, i)
        left = f"(bool({left}) ^ bool({right}))"
    return left, i

def code_parse_or(tokens, i):
    left, i = code_parse_xor(tokens, i)
    while i<len(tokens) and tokens[i].upper() in ("OR","||"):
        i+=1
        right, i = code_parse_xor(tokens, i)
        left = f"({left} or {right})"
    return left, i

def compile_module_filter(filter_string: str):
    """Return a function f(item)->bool from the filter string."""
    if not filter_string.strip():
        return lambda item: True
    expr = compile_filter_string(filter_string)
    code = f"def _f(item):\n    return {expr}"
    env = {fn.__name__: fn for fn in (
        match_name_filter, match_number_filter, match_number_str_filter,
        match_number_range_filter, match_category_filter, match_tag_filter,
        match_form_filter, match_mark_filter, match_color_filter, match_stat_filter,
        match_in_filter, match_method_filter, match_source_filter, match_evol_filter
    )}
    exec(code, env)
    return env["_f"]

# ----------------------------------------------------------------------------- 
# Public API 
# -----------------------------------------------------------------------------
def load_module(module_filename: str):
    """
    Load and compile one module JSON.  
    Returns None if missing/disabled, else:
      {
        "module":        <raw JSON>,
        "filter_function": <callable item->bool>,
        "other_flags":   {...},
        "filter_string": "NOT (...)",
        "name":          <module name>,
        "default_shiny": <boolean>
      }
    """
    path = os.path.join(MODULES, module_filename)
    if not os.path.isfile(path):
        return None

    with open(path, "r", encoding="utf-8") as f:
        mod = json.load(f)
    if not mod.get("enabled", False):
        return None

    fs = build_module_filter_string(mod)
    func = compile_module_filter(fs)
    cache = {}
    def cached(item):
        key = str(item.number)
        if key in cache:
            return cache[key]
        res = func(item)
        cache[key] = res
        return res

    flags = {
        "hide_impossible_pokemon": mod.get("hide_impossible_pokemon", False),
        "hide_locked_shinies":     mod.get("hide_locked_shinies", False),
        "hide_go_exclusives":      mod.get("hide_go_exclusives", False),
        "decorations":             mod.get("decorations", {}),
    }
    return {
        "module":          mod,
        "filter_function": cached,
        "other_flags":     flags,
        "filter_string":   fs,
        "name":            mod.get("name", os.path.splitext(module_filename)[0]),
        "default_shiny":   mod.get("default_shiny", False)
    }

def get_module_pokemon_numbers(module_filename: str):
    """
    Return a sorted list of all `item.number` strings matching that module.
    """
    mod = load_module(module_filename)
    if not mod:
        return []
    items = data.load_items()
    nums = [itm.number for itm in items if mod["filter_function"](itm)]
    try:
        return sorted(nums, key=lambda x: float(x))
    except ValueError:
        return sorted(nums)
