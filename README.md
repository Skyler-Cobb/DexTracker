
# DexTracker

> **A fully‑offline, highly‑customizable Pokédex progress tracker.**

I developed DexTracker for personal use after finding that most other Pokédex‑tracking utilities were lacking in some minor feature or had some small restriction that caused regular intrusive thoughts wondering if I couldn't just make something really quickly that could handle that problem for me. What started as a basic, bare‑bones project meant to be a quick fix before I got back to shiny‑hunting quickly spiraled in scope, as I ran into those same little annoyances in my own project, identifying and fixing everything that I personally wasn't 100 % satisfied with.  
By no means is this a perfect program, but if you share the same general set of desired tools, I hope you’ll find that it fits all of your needs.

DexTracker is a solo project that receives infrequent updates on no specific schedule. I’ve tried to maximize customization options, so even if development stops the amount of work needed to add new generations or tweak behavior should be minimal for anyone with moderate Python knowledge.

**Thank you for checking out the project, and happy hunting!**

---

## Quick Start

```bash
git clone https://github.com/Skyler-Cobb/DexTracker.git
cd DexTracker
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## Features

### Collection Tracking

| Feature | What it does |
|---------|--------------|
| **6 × 5 box layout** | Mirrors in‑game PC boxes so you can replicate the exact arrangement you plan to use. |
| **One‑click toggle** | Left‑click a sprite to flip between *caught* and *missing*. |
| **Edit mode button** | Click **Edit** (top‑left) to turn editing on, then click any Pokémon to open the detailed entry dialog. |
| **Detailed entry editor** | Inside the dialog you can set shiny status, gender, origin mark, source mark (wild, raid, egg, trade, event…), silhouette color, and variant flags (regional forms, mega/G‑Max, etc.). |
| **Independent variant slots** | Shiny, gender, form, regional and transformation variants are tracked separately so progress bars stay precise. |

### Navigation & Filtering

| Feature | What it does |
|---------|--------------|
| **Search bar** | Click the text box and start typing to jump straight to a Pokémon by name or number, or enter a complex filter string (see *Filter_Terms.md*). |
| **Mode button** | The **Mode** button (to the right of the search bar) cycles through: **Search ➜ Filter ➜ Highlight ➜ Search**. *Filter* hides non‑matches, *Highlight* dims them. |
| **Origin‑mark overlay** | Click the mark icon to cycle through *show all marks / show GO‑marks only / hide marks*. |
| **Module switch button** | The button at the bottom center cycles through loaded modules (NatDex → Shiny NatDex → Form Dex → …). |

### Information Access

| Feature | What it shows |
|---------|---------------|
| **Sidebar completion meters** | Real‑time completion percentages for the current box, region, and module. |
| **Shiny‑lock awareness** | Locked species never count against shiny completion. |
| **Pokémon Data** | In the editor dialog you can view types, evolution chain, base stats, available games, and in‑game encounter methods; upcoming updates will add egg groups, gender ratios, self‑KO warnings, and more. |

### Additional Features

| Feature | Details |
|---------|---------|
| **Autosave** | Progress is written to `resources/data/items.json` whenever you change something. |
| **Extensible modules & assets** | Drop new module JSONs or images into the appropriate folders and they appear automatically. |
| **Cross‑platform** | Pure Python 3 + Pygame: runs on Windows, macOS and Linux. |
| **Offline‑first** | All sprites and data live locally; no network required once installed. |

---


## Known Issues

* No separate data for shiny vs. non‑shiny entries — changing one currently overwrites the other.
* Changing gender in the editor can confuse the sprite loader/information loader, causing the profile to look bugged.
* **Settings** and **Ignore Locked** toggles are placeholders — they aren't implemented yet.
* Encounter‑method data frequently inaccurate or missing.
* Arrow buttons next to the box name are non‑functional — use the mouse‑wheel or arrow keys to change boxes instead.
* Some clicks “fall through” overlay UI and activate items beneath, mainly in the editor dialog.
* Several dialogs have text that overflows or shows huge empty space — UI‑scaling overhaul planned.

---

## Planned Features

* Settings menu
* Extra data in info panel (egg groups, gender ratios, self‑KO warnings, etc.)
* Show source marks directly in box view
* GUI module editor / creator
* Wallpaper picker
* Ability to track specific game something was caught in
* Additional stats (origin‑mark breakdown, favorite shiny‑hunting method, etc.)


---

## Contributing 

Feel free to open an issue or pull request if you'd like to help out.  
I’m new to maintaining public projects, so please be patient if I’m a bit slow to respond.

---

## License

This project is released under the [MIT License](LICENSE).  
Pokémon sprites and marks are © Nintendo / Creatures Inc. / GAME FREAK and are bundled here under fair‑use; remove or replace them if you redistribute the project commercially.