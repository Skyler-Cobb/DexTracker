
# DexTracker – Getting Started

## 1. Installation

```bash
git clone https://github.com/Skyler-Cobb/DexTracker.git
cd DexTracker
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

---

## 2. Basic Workflow

| Step | Action |
|------|--------|
| **Open** | Launch the program; the first module (usually *National Dex*) loads automatically. |
| **Toggle caught** | Left‑click a Pokémon’s sprite. A faded silhouette means “missing”; the full sprite means “caught”. |
| **Enable Edit mode** | Click the **Edit** button (top‑left). Its label changes to *ON*. |
| **Open editor dialog** | With Edit mode **ON**, click any Pokémon to open its detailed entry dialog. |
| **Set variants & marks** | Inside the dialog set shiny, gender, origin mark, source mark, custom silhouette color, etc. |
| **Navigate boxes** | Hover anywhere over the grid and scroll the mouse‑wheel up/down. |
| **Switch modules** | Click the **Module** button at the bottom center; each click cycles to the next JSON module. |
| **Search / Filter / Highlight** | Click the search bar, type a term or complex filter, then use the **Mode** button to choose how results are applied. |
| **View progress** | The sidebar shows percentage completion for the current box, region, and whole module. |

---

## 3. Tips & Tricks

| Task | Tip |
|------|-----|
| **Jump straight to a dex number** | Type `#149` (or any number) in the search bar and hit *Enter*. |
| **Create your own module** | Duplicate a file from `resources/data/modules/`, edit the JSON filter_rules, restart DexTracker. |
| **Custom wallpapers** | Drop a PNG into `resources/images/ui/wallpapers/` and point `config.json → wallpaper`. |
| **Silhouette color modification** | Hex strings in `config.json → silhouette_colors`. |