# filter.py – restored advanced filtering logic for DexTracker (v2)
"""
Changelog v2 (2025‑04‑05)
------------------------
• **match_evol_filter** now supports evolution lists that store numeric IDs (int/float/str) as well as names, eliminating the `'int' object has no attribute 'lower'` error when using the `+` evolution filter.
• Parsing is now tolerant of *in‑progress* / incomplete expressions.  If the user is still typing (e.g. the string ends with an operator or an unmatched parenthesis), the parser no longer spams the console with tracebacks; instead, it treats the expression as "no match yet" and returns `False` for all items until the query becomes valid.
"""

from __future__ import annotations

import re
from typing import Callable, List, Tuple, Optional, Any

import dex_adapter  # Legacy wrapper dependency

# ---------------------------------------------------------------------------
#  Lazy helper to fetch a module without creating circular imports
# ---------------------------------------------------------------------------
import importlib

def _load_module(filename: str):
    """
    Try to load a module via module_loader.load_module first.
    Fall back to data.load_module if module_loader isn’t available yet.
    All imports are done inside this function so nothing is imported
    at file‑import time, breaking the circular‑import chain.
    """
    # Attempt module_loader.load_module
    try:
        ml = importlib.import_module("module_loader")
        return ml.load_module(filename)
    except Exception:
        pass

    # Fallback: data.load_module (data.py lazily imports module_loader itself)
    try:
        from data import load_module as _lm   # local import avoids cycle
        return _lm(filename)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def normalize_str(s: str) -> str:
    return s.lower().replace("-", "").replace(" ", "")


def normalize_method(m: str) -> str:
    m_low = m.lower()
    if m_low in ("grass", "tallgrass"):
        return "walk"
    return m_low

# ---------------------------------------------------------------------------
# Primitive matchers
# ---------------------------------------------------------------------------

def match_name_filter(item, value: str) -> bool:
    return value in item.name.lower()


def match_number_filter(item, value: str) -> bool:
    return str(item.number) == str(value)


def match_number_str_filter(item, value: str) -> bool:
    return str(item.number) == str(value)


def match_category_filter(item, value: str) -> bool:
    return any(value in cat.lower() for cat in item.categories)


def match_tag_filter(item, value: str) -> bool:
    return any(value in tag.lower() for tag in item.tags)


def match_form_filter(item, value: Optional[str]):
    if value is None:
        return "." in str(item.number)
    lower_val = value.lower()
    if lower_val == "variant":
        return "." in str(item.number)
    if lower_val == "base":
        return "." not in str(item.number) and getattr(item, "has_alternate", False)
    if lower_val in ("all", "any"):
        return getattr(item, "has_alternate", False)
    if lower_val == "none":
        return not getattr(item, "has_alternate", False)
    if lower_val == "gender":
        return "♂" in item.form or "♀" in item.form
    if lower_val == "male":
        return "♂" in item.form or ("male" in item.form.lower() and "female" not in item.form.lower())
    if lower_val == "female":
        return "♀" in item.form or "female" in item.form.lower()
    return lower_val in item.form.lower()


def match_mark_filter(item, value: Optional[str]):
    if value is None:
        return item.marks.get("flag", False) or item.marks.get("lock", False)
    return any(value in str(v).lower() for v in item.marks.values())


def match_color_filter(item, value: Optional[str]):
    if value is None:
        return item.marks.get("color", "gray").lower() != "gray"
    return item.marks.get("color", "gray").lower() == value


def match_stat_filter(item, criteria: Tuple[str, str, float]):
    stat_name, operator, target_value = criteria
    if stat_name == "total":
        stat_value = sum(float(item.stats.get(k, 0)) for k in ["atk", "def", "spd", "spatk", "spdef", "hp"])
    else:
        stat_value = float(item.stats.get(stat_name, 0))
    if operator == ">":
        return stat_value > target_value
    if operator == ">=":
        return stat_value >= target_value
    if operator == "<":
        return stat_value < target_value
    if operator == "<=":
        return stat_value <= target_value
    if operator == "=":
        return stat_value == target_value
    raise ValueError(f"Unknown operator: {operator}")


def match_in_filter(item, game_method: Tuple[str, Optional[str]]):
    game_filter, method_filter = game_method
    game_norm = normalize_str(game_filter)
    method_norm = normalize_method(method_filter) if method_filter else None
    for g in item.games:
        if normalize_str(g.get("game", "")) == game_norm:
            if not method_norm:
                return True
            for m in g.get("encounter_methods", []):
                if normalize_method(m) == method_norm:
                    return True
    return False


def match_method_filter(item, method_value: str):
    method_norm = normalize_method(method_value)
    for g in item.games:
        for m in g.get("encounter_methods", []):
            if normalize_method(m) == method_norm:
                return True
    return False


def match_source_filter(item, source_value: str):
    source_norm = normalize_str(source_value)
    method_norm = normalize_method(source_value)
    for g in item.games:
        if normalize_str(g.get("game", "")) == source_norm:
            return True
        for m in g.get("encounter_methods", []):
            if normalize_method(m) == method_norm:
                return True
    return False


def match_evol_filter(item, evol_sub):
    evol_sub = evol_sub.lower()
    for evo_ref in item.evolutions:
        # Attempt to interpret each `evo_ref` as a dex number, decimal, or fallback string
        evo_item = None
        if isinstance(evo_ref, (int, float)):
            # direct numeric
            evo_item = dex_adapter.get_pokemon_info(int(evo_ref))  # or round if needed
        else:
            # might be a string "25", "25.01", etc.
            # parse or pass as-is to get_pokemon_info
            try:
                possible_num = float(evo_ref)
                evo_item = dex_adapter.get_pokemon_info(str(evo_ref))
            except:
                # not numeric; might be a leftover string
                pass

        if evo_item:
            # Compare against the evolution’s name
            if evol_sub in evo_item.name.lower():
                return True
        else:
            # fallback check: see if user’s substring is in the raw string
            if evol_sub in str(evo_ref).lower():
                return True
    return False


def match_number_range_filter(item, criteria: Tuple[float, float, bool]):
    start, end, include_forms = criteria
    try:
        num = float(item.number)
    except Exception:
        return False
    if not (start <= num <= end):
        return False
    if not include_forms and "." in str(item.number):
        return False
    return True


def match_module_filter(item, func: Optional[Callable[[Any], bool]]):
    return True if func is None else func(item)

# ---------------------------------------------------------------------------
# Tokenisation & parsing (unchanged apart from helper rename)
# ---------------------------------------------------------------------------

def tokenize(s: str) -> List[str]:
    s = re.sub(r"([()])", r" \1 ", s)
    s = s.replace("!", " ! ")
    s = re.sub(r"\b(OR|NOT|XOR)\b", r" \1 ", s, flags=re.IGNORECASE)
    s = s.replace("||", " || ")
    return s.split()

# -- parse term helper (same as before) --

def _parse_filter_term(term: str):
    low = term.lower().strip()
    if low.startswith("@"):
        return "category", term[1:].strip()
    if term.startswith("#"):
        token = term[1:].strip()
        include_forms = False
        if token.endswith("f"):
            include_forms = True
            token = token[:-1]
        if "-" in token:
            start, end = map(float, token.split("-"))
        else:
            start = end = float(token)
        return "number_range", (start, end, include_forms)
    if low.startswith("in:"):
        game, *method = term[3:].split(":")
        return "in", (game.strip(), method[0].strip() if method else None)
    if low.startswith("method:"):
        return "method", term[7:].strip()
    if low.startswith("source:"):
        return "source", term[7:].strip()
    if term.startswith("+"):
        return "evol", term[1:].strip()
    if low.startswith("module:"):
        filename = term[len("module:"):].strip()
        mod_data = _load_module(filename)
        if mod_data is None:
            return "module", None
        else:
            return "module", mod_data["filter_function"]
    if low.startswith("num:"):
        value = term[4:].strip()
        if re.match(r"^\d+(\.\d+)?$", value):
            return "number", value
        return "number_str", value
    if low.startswith("name:"):
        return "name", low[5:]
    if low.startswith("cat:"):
        return "category", low[4:]
    if low.startswith("tag:"):
        return "tag", low[4:]
    if low.startswith("form:"):
        return "form", term[5:].strip() or None
    if low.startswith("mark:"):
        return "mark", low[5:]
    if low == "mark":
        return "mark", None
    if low.startswith("color:"):
        return "color", low[6:]
    if low == "color":
        return "color", None
    if low.startswith("stat:"):
        stat_expr = low[5:]
        ops = ["<=", ">=", "<", ">", "="]
        op = next((o for o in ops if o in stat_expr), None)
        if not op:
            raise ValueError("stat filter missing operator")
        stat_name, val = (p.strip() for p in stat_expr.split(op, 1))
        mapping = {"sat": "spatk", "sdf": "spdef"}
        stat_name = mapping.get(stat_name, stat_name)
        return "stat", (stat_name, op, float(val))
    return "name", low

# -- recursive descent parser (unchanged) --

def _parse_expression(tokens: List[str]):
    expr, idx = _parse_or(tokens, 0)
    if idx != len(tokens):
        raise ValueError("Unexpected token(s)")
    return expr

# (sub‑parsers _parse_or / _parse_xor / _parse_and / _parse_not / _parse_primary remain identical to the first version; omitted here for brevity – they are unchanged.)
# === START of unchanged parser section ===

def _parse_or(toks, i):
    l, i = _parse_xor(toks, i)
    while i < len(toks) and toks[i].upper() in ("OR", "||"):
        i += 1
        r, i = _parse_xor(toks, i)
        l, rcopy = l, r
        l = lambda itm, a=l, b=rcopy: a(itm) or b(itm)
    return l, i

def _parse_xor(toks, i):
    l, i = _parse_and(toks, i)
    while i < len(toks) and toks[i].upper() == "XOR":
        i += 1
        r, i = _parse_and(toks, i)
        l, rcopy = l, r
        l = lambda itm, a=l, b=rcopy: bool(a(itm)) ^ bool(b(itm))
    return l, i

def _parse_and(toks, i):
    l, i = _parse_not(toks, i)
    while i < len(toks) and toks[i] not in (")", "OR", "||", "XOR"):
        if toks[i].upper() in ("AND", "&&"):
            i += 1
            continue
        r, i = _parse_not(toks, i)
        l, rcopy = l, r
        l = lambda itm, a=l, b=rcopy: a(itm) and b(itm)
    return l, i

def _parse_not(toks, i):
    if i < len(toks) and (toks[i] == "!" or toks[i].upper() == "NOT"):
        while i < len(toks) and (toks[i] == "!" or toks[i].upper() == "NOT"):
            i += 1
        op, i = _parse_not(toks, i)
        return lambda itm, f=op: not f(itm), i
    return _parse_primary(toks, i)

def _parse_primary(toks, i):
    if i >= len(toks):
        raise ValueError("Unexpected end of expression")
    tok = toks[i]
    if tok == "(":
        i += 1
        expr, i = _parse_or(toks, i)
        if i >= len(toks) or toks[i] != ")":
            raise ValueError("Expected ')'")
        return expr, i + 1
    i += 1
    term_type, val = _parse_filter_term(tok)
    mapping = {
        "name": match_name_filter,
        "number": match_number_filter,
        "number_str": match_number_str_filter,
        "number_range": match_number_range_filter,
        "category": match_category_filter,
        "tag": match_tag_filter,
        "form": match_form_filter,
        "mark": match_mark_filter,
        "color": match_color_filter,
        "stat": match_stat_filter,
        "in": match_in_filter,
        "method": match_method_filter,
        "source": match_source_filter,
        "evol": match_evol_filter,
        "module": match_module_filter,
    }
    func = mapping[term_type]
    return lambda itm, v=val, f=func: f(itm, v), i
# === END of unchanged parser section ===

# ---------------------------------------------------------------------------
# Evaluation helpers
# ---------------------------------------------------------------------------

def _compile(filter_string: str):
    toks = tokenize(filter_string)
    return _parse_expression(toks)


def _safe_compile(filter_string: str):
    """Return a compiled matcher or None if the expression is incomplete/invalid."""
    try:
        return _compile(filter_string)
    except Exception:
        return None  # Treat as no‑op until user finishes typing


def filter_items(items: List[Any], filter_string: str):
    filter_string = filter_string.strip()
    if not filter_string:
        return items

    if filter_string.lower().startswith("module:"):
        filename = filter_string[len("module:"):].strip()
        mod_data = _load_module(filename)
        if mod_data is None:
            return items            # or [] if you prefer
        compiled_filter = mod_data["filter_function"]
        return [item for item in items if compiled_filter(item)]

    matcher = _safe_compile(filter_string)
    if matcher is None:
        # Incomplete expression – return all items (no filtering) so UI stays populated
        return items

    return [itm for itm in items if matcher(itm)]

# ---------------------------------------------------------------------------
# Legacy dict wrapper
# ---------------------------------------------------------------------------

def filter_item(item_dict: dict, filter_string: str) -> bool:
    key = str(item_dict.get("key", ""))
    item = dex_adapter.get_items_dict().get(key)
    if item is None:
        return False
    matcher = _safe_compile(filter_string)
    if matcher is None:
        return False
    try:
        return matcher(item)
    except Exception:
        return False

__all__ = ["filter_items", "filter_item"]
