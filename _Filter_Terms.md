
# DexTracker – Filter String Reference

DexTracker’s search bar doubles as a powerful filter language.  
Each term narrows (or widens) the result set; combine terms with boolean operators for precise selections.

> **Tip:** Switch to **Filter** or **Highlight** mode with the **Mode** button to apply the string.

---

## 1. Name / Number

| Term | Usage | Description |
|------|-------|-------------|
| *(plain text)* | `pikachu` | Substring match on Pokémon name (case‑insensitive). |
| `+` | `+eevee` | Any Pokémon whose **evolution line** contains the substring. |
| `num:` | `num:25`<br>`num:25.01` | Exact number or number + form ID. |
| `#` | `#25`<br>`#25-151`<br>`#25-151f` | `#start‑end` range. Append **f** to include alternate forms within the range. |

---

## 2. Pokémon Data

| Term | Usage / Valid values | Description |
|------|---------------------|-------------|
| `@` | `@fire` | Match any Pokémon whose primary **or** secondary type contains the value. |
| `form:` | `form:variant`, `form:base`, `form:gender`, `form:male`, `form:female`, `form:none` | Form helpers (see table at bottom). |
| `stat:` | `stat:atk>120`, `stat:total<=500` | Six main stats (`hp/atk/def/spatk/spdef/spd`) or `total`. <br> Operators: `> ≥ < ≤ =`. |
| `tag:<tag>` <br> `cat:<tag>` | `cat:starter` <br> `tag:baby`<br> `tag:` | Tags for various specific categories of Pokémon. <br> Valid tags are: starter, baby, legendary, main-legendary, sub-legendary, mythical |

---

## 3. Marks & Silhouettes

| Term | Usage | Description |
|------|-------|-------------|
| `mark` | `mark` | Any entry with **any** mark set (flag or lock). |
| `mark:` | `mark:flag`, `mark:lock` | Match a specific mark keyword. |
| `color` | `color` | Any entry whose silhouette color isn’t the default gray. |
| `color:` | `color:red` | Exact silhouette color. |

---

## 4. Game & Encounter Filters

| Term | Usage | Description |
|------|-------|-------------|
| `in:` | `in:swsh:raid`, `in:scarlet` | Pokémon obtainable in a **game**; optional second part restricts to a specific method. |
| `method:` | `method:egg`, `method:trade` | Match by encounter method across **any** game the entry appears in. |
| `source:` | `source:scarlet`, `source:teraraid` | Loose “find in this game **or** by this method” search. |

---

## 5. Modules & External Filters

| Term | Usage | Description |
|------|-------|-------------|
| `module:` | `module:6_shinyNat.json` | Load a custom JSON filter function from a module file. |

---

### Boolean / Logical Operators

| Symbol / Word | Effect | Example |
|---------------|--------|---------|
| (space), `AND`, `&&` | Logical **AND** (all terms must match) | `@ghost stat:spd>100` |
| `OR`, `||` | Logical **OR** (either side may match) | `@rock OR @ground` |
| `XOR` | Exclusive OR (exactly one side must match) | `@fire XOR @water` |
| `NOT`, `!` | Negation | `@flying NOT mark:lock` |
| `()` | Parentheses control precedence | `(@fire OR @water) stat:hp>100` |

Precedence order (highest → lowest): `()` → `NOT`/`!` → `AND`/space → `XOR` → `OR`.

---

### `form:` Helper Table

| Value | Matches |
|-------|---------|
| *(no value)* | Any entry whose dex number contains a period (`.`) – i.e. **has any form**. |
| `variant` | Same as above (alias). |
| `base` | Only entries with **no** dot but that *have* alternates. |
| `all` / `any` | Pokémon that *possess* alternate forms (base + alternates). |
| `none` | Species with no alternates at all. |
| `gender` | Entries whose form string contains ♂ or ♀. |
| `male` / `female` | Self‑explanatory. |
| any other text | Substring match inside the form string. <br> Example: `form:crowned` |

---

#### Putting It Together

> *Find all Fire‑types obtainable by **egg** in Scarlet that aren’t shiny‑locked and have base‑stat‑total > 450:*

```
@fire in:scarlet:egg NOT mark:lock stat:total>450
```

Remember: switch to **Filter** or **Highlight** mode with the **Mode** button to apply the string.