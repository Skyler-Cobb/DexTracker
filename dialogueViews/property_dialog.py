# dialogueViews/property_dialog.py
import os
import json
import pygame
import data
import dex_adapter  # For data-related calls
from config import (
    ALT_BOLD, ALT_REGULAR, ALT_ITALIC, UI_COMPONENTS, MARKS, TYPES,
    FORM_SYMBOLS, FORM_MARKS, SILHOUETTE_COLORS
)
from dialogueViews.popups import PopupManager
from dialogueViews.editor_view import EditorView
from dialogueViews.info_view import InfoView
from dialogueViews.availability_view import AvailabilityView
from dialogueViews.relationships_view import RelationshipsView

POPUP_BG_COLOR = (240, 240, 240)
POPUP_BORDER_COLOR = (0, 0, 0)

class PropertyDialog:
    def __init__(self, screen_width, screen_height):
        # Setup dialog dimensions.
        dialog_width = 600
        dialog_height = 550
        self.dialog_rect = pygame.Rect(
            (screen_width - dialog_width) // 2,
            (screen_height - dialog_height) // 2,
            dialog_width,
            dialog_height
        )

        # Shared state.
        self.selected_pokemon_id = None
        self.pokemon_info = None
        self.shiny_state = False
        self.female_state = False
        self.caught_state = False
        self.locked_state = False

        # Load common resources.
        self._load_resources()

        # Setup popup manager.
        self.popup_manager = PopupManager(self.dialog_rect, self)

        # Create view instances.
        self.views = {
            "Editor": EditorView(self),
            "Info": InfoView(self),
            "Availability": AvailabilityView(self),
            "Relationships": RelationshipsView(self)
        }
        self.pages = list(self.views.keys())
        self.current_page = "Editor"
        self.tab_rects = {}

    def _load_resources(self):
        # Load close button image.
        close_img_path = os.path.join(UI_COMPONENTS, "clear.png")
        try:
            self.close_img = pygame.image.load(close_img_path).convert_alpha()
        except Exception:
            self.close_img = None

        # Load origin mark images.
        try:
            origin_folder = os.path.join(MARKS, "origin")
            if os.path.isdir(origin_folder):
                self.origin_mark_images = dex_adapter.load_mark_images(origin_folder)
            else:
                self.origin_mark_images = {}
        except Exception:
            self.origin_mark_images = {}

        # Load source mark images.
        try:
            source_folder = os.path.join(MARKS, "source")
            if os.path.isdir(source_folder):
                self.source_mark_images = dex_adapter.load_mark_images(source_folder)
            else:
                self.source_mark_images = {}
        except Exception:
            self.source_mark_images = {}

        # Load lock and flag icons.
        self.lock_image = {}
        try:
            lock_img = pygame.image.load(os.path.join(MARKS, "lock.png")).convert_alpha()
            unlock_img = pygame.image.load(os.path.join(MARKS, "unlock.png")).convert_alpha()
            self.lock_image[True] = lock_img
            self.lock_image[False] = unlock_img
        except Exception:
            pass
        try:
            self.flag_image = pygame.image.load(os.path.join(MARKS, "flag.png")).convert_alpha()
        except Exception:
            self.flag_image = None

        # Load shiny icons.
        self.shiny_icons = {}
        try:
            shiny_on = pygame.image.load(os.path.join(MARKS, "shiny-on.png")).convert_alpha()
            shiny_off = pygame.image.load(os.path.join(MARKS, "shiny-off.png")).convert_alpha()
            self.shiny_icons[True] = shiny_on
            self.shiny_icons[False] = shiny_off
        except Exception:
            pass

        # Load gender icons.
        self.gender_icons = {}
        try:
            male_img = pygame.image.load(os.path.join(MARKS, "gender-male.png")).convert_alpha()
            female_img = pygame.image.load(os.path.join(MARKS, "gender-female.png")).convert_alpha()
            self.gender_icons[False] = male_img
            self.gender_icons[True] = female_img
        except Exception:
            pass

        # Load type images.
        self.type_images = {}
        if os.path.isdir(TYPES):
            for fname in os.listdir(TYPES):
                if fname.lower().endswith(".png"):
                    key = os.path.splitext(fname)[0].lower()
                    try:
                        self.type_images[key] = pygame.image.load(os.path.join(TYPES, fname)).convert_alpha()
                    except Exception:
                        pass

        # Load form symbols.
        try:
            with open(FORM_SYMBOLS, "r") as f:
                self.form_symbols = json.load(f)
        except Exception:
            self.form_symbols = {}

        # Fonts.
        self.header_font = pygame.font.Font(ALT_BOLD, 28)
        self.main_font = pygame.font.Font(ALT_REGULAR, 20)
        self.small_font = pygame.font.Font(ALT_REGULAR, 14)

        # Geometry caches.
        self.toggle_rects = {}  # For shiny/gender toggles.
        self.editor_buttons = {}  # For Editor page controls.
        self.evolution_icon_rects = []  # For relationships.
        self.form_icon_rects = {}  # For forms.
        self.shiny_rect = None
        self.gender_rect = None

        # --- New: Load tab icons --- 
        self.tab_icons = {}
        try:
            tab_icon_files = {
                "Editor": "edit_tab.png",
                "Info": "info_view.png",
                "Availability": "availability_view.png",
                "Relationships": "relationships_view.png"
            }
            for tab, filename in tab_icon_files.items():
                path = os.path.join(MARKS, filename)
                if os.path.exists(path):
                    self.tab_icons[tab] = pygame.image.load(path).convert_alpha()
                else:
                    self.tab_icons[tab] = None
        except Exception:
            self.tab_icons = {tab: None for tab in ["Editor", "Info", "Availability", "Relationships"]}

    def open(self, pokemon_id, keep_tab=False, new_gender=None):
        """
        Opens the details for a given Pokémon.
        
        Parameters:
        - pokemon_id: The ID of the Pokémon to load.
        - keep_tab (bool): If True, the current tab is preserved; otherwise, it defaults to the Editor tab.
        - new_gender (optional bool): If provided, forces the dialog to load with this gender.
        """
        self.selected_pokemon_id = pokemon_id
        self.pokemon_info = dex_adapter.get_pokemon_info(pokemon_id)
        if self.pokemon_info:
            if not keep_tab:
                self.shiny_state = getattr(self.pokemon_info, "shiny", False)
                self.female_state = getattr(self.pokemon_info, "female", False)
            else:
                # Force the gender if new_gender is provided.
                if new_gender is not None:
                    self.female_state = new_gender
                else:
                    self.female_state = getattr(self.pokemon_info, "female", False)
            self.caught_state = dex_adapter.is_pokemon_caught(pokemon_id)
            self.locked_state = getattr(self.pokemon_info, "locked", False)
        if not keep_tab:
            self.current_page = "Editor"
        # If keep_tab is True, leave self.current_page unchanged.
        self.popup_manager.hide_all()
        for view in self.views.values():
            view.refresh()

    def close(self):
        self.selected_pokemon_id = None
        self.pokemon_info = None
        self.popup_manager.hide_all()

    def is_open(self):
        return self.selected_pokemon_id is not None

    def handle_event(self, event, search_input=None, suggestions=None):
        if not self.is_open():
            return False

        # Handle search input first.
        if search_input:
            ret = search_input.handle_event(event)
            if ret == "enter":
                search_input.text = ""
                if suggestions:
                    suggestions.clear()
                search_input.active = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if self.popup_manager.is_active():
                    self.popup_manager.hide_all()
                else:
                    self.close()
                return True
        
        if event.type == pygame.MOUSEWHEEL:
            if self.current_page in self.views:
                handled = self.views[self.current_page].handle_event(event)
                if handled:
                    return True

        # Delegate popup events.
        if self.popup_manager.is_active():
            self.popup_manager.handle_event(event)
            return True

        # <<-- NEW: Always section toggle handling for shiny and gender -->> 
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.shiny_rect is not None and self.shiny_rect.collidepoint(event.pos):
                self.shiny_state = not self.shiny_state
                return True
            if self.gender_rect is not None and self.gender_rect.collidepoint(event.pos):
                # Determine desired new gender: if currently female, then we want male; otherwise, female.
                new_gender = not self.female_state  # True means female is desired.
                base_number = str(self.pokemon_info.number).split('.')[0]
                all_forms = data.get_form_items(dex_adapter.get_items(), base_number)
                target_variant_id = None
                for item in all_forms:
                    # When wanting a female variant, look for a form that has "♀" in its form string or "female" in its image.
                    if new_gender:
                        if (("♀" in item.form) or ("female" in item.image.lower())) and (str(item.number) != str(self.selected_pokemon_id)):
                            target_variant_id = item.number
                            break
                    else:
                        # When wanting a male variant, assume the male form is the default:
                        # typically with an empty form string or explicitly containing "male".
                        if (item.form == "" or ("male" in item.form.lower())) and (str(item.number) != str(self.selected_pokemon_id)):
                            target_variant_id = item.number
                            break
                if target_variant_id is not None:
                    self.open(target_variant_id, keep_tab=True, new_gender=new_gender)
                return True
        # <<-- End of toggle handling -->> 

        # Delegate event handling to the current view.
        if self.current_page in self.views:
            handled = self.views[self.current_page].handle_event(event)
            if handled:
                return True

        # Global mouse events for tab switching and close button.
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for page, rect in self.tab_rects.items():
                if rect.collidepoint(event.pos):
                    self.current_page = page
                    return True

            if self.close_img:
                close_rect = pygame.Rect(self.dialog_rect.right - 35, self.dialog_rect.top + 5, 30, 30)
                if close_rect.collidepoint(event.pos):
                    self.close()
                    return True

        return True

    # Updated draw method: now accepts an extra mark_mode parameter.
    def draw(self, screen, mark_mode=0):
        if not self.is_open():
            return

        # Draw dialog background.
        pygame.draw.rect(screen, (220,220,220), self.dialog_rect)
        pygame.draw.rect(screen, (0,0,0), self.dialog_rect, 2)

        # Draw common (always-present) section.
        bottom_always = self._draw_always_section(screen)

        # Let the current view draw its content.
        if self.current_page in self.views:
            self.views[self.current_page].draw(screen, bottom_always + 10)

        # Draw tab bar.
        self._draw_tab_bar(screen)

        # Draw close button.
        if self.close_img:
            close_rect = pygame.Rect(self.dialog_rect.right - 35, self.dialog_rect.top + 5, 30, 30)
            screen.blit(pygame.transform.smoothscale(self.close_img, (30,30)), close_rect)

        # Draw active popup if any.
        self.popup_manager.draw(screen)

    def _draw_always_section(self, screen):
        cur_y = self.dialog_rect.y + 20

        # Header: number and name.
        id_str = str(self.selected_pokemon_id)
        try:
            id_int = int(id_str.split('.')[0])
            id_display = f"{id_int:04d}"
        except Exception:
            id_display = id_str
        name_val = getattr(self.pokemon_info, "name", "Unknown")
        head_txt = f"#{id_display}: {name_val}"
        head_surf = self.header_font.render(head_txt, True, (0, 0, 0))
        head_rect = head_surf.get_rect(centerx=self.dialog_rect.centerx, top=cur_y)
        screen.blit(head_surf, head_rect)
        cur_y += head_rect.height + 5

        # Form name.
        form_name = getattr(self.pokemon_info, "form", "")
        if form_name:
            # Using main_font here; you might swap to a Unicode‐friendly ALT font as needed.
            f_font = self.main_font  
            f_surf = f_font.render(form_name, True, (0, 0, 0))
            f_rect = f_surf.get_rect(centerx=self.dialog_rect.centerx, top=cur_y)
            screen.blit(f_surf, f_rect)
            cur_y += f_rect.height + 5

        # Use different sizes depending on the active tab.
        if self.current_page == "Editor":
            sprite_w = 200
            type_w, type_h = 105, 23
            toggle_icon_size = 30
            toggle_gap = 20
        else:
            sprite_w = 120
            type_w, type_h = 70, 20
            toggle_icon_size = 20
            toggle_gap = 10

        # Sprite.
        try:
            spr = dex_adapter.load_sprite(self.selected_pokemon_id, shiny=self.shiny_state, female=self.female_state, caught=True)
        except Exception:
            spr = pygame.Surface((80, 80))
        ratio = spr.get_width() / spr.get_height() if spr.get_height() != 0 else 1
        sprite_h = int(sprite_w / ratio)
        scaled_spr = pygame.transform.smoothscale(spr, (sprite_w, sprite_h))
        spr_rect = scaled_spr.get_rect(centerx=self.dialog_rect.centerx, top=cur_y)
        screen.blit(scaled_spr, spr_rect)
        cur_y += spr_rect.height + 10

        # Types.
        cats = getattr(self.pokemon_info, "categories", [])
        if cats:
            gap = 10
            total_w = len(cats) * type_w + (len(cats) - 1) * gap
            start_x = self.dialog_rect.centerx - total_w // 2
            for c in cats:
                c_lower = c.lower()
                if c_lower in self.type_images:
                    scaled = pygame.transform.smoothscale(self.type_images[c_lower], (type_w, type_h))
                    screen.blit(scaled, (start_x, cur_y))
                start_x += type_w + gap
            cur_y += type_h + 5

        # Shiny/Gender toggles.
        toggles = []
        toggles.append(("Shiny", self.shiny_state, self.shiny_icons))
        if getattr(self.pokemon_info, "cosmetic_gender_diff", False):
            toggles.append(("Gender", self.female_state, self.gender_icons))
        if toggles:
            total_toggle_w = len(toggles) * toggle_icon_size + (len(toggles) - 1) * toggle_gap
            start_x = self.dialog_rect.centerx - total_toggle_w // 2
            for lbl, state, icon_dict in toggles:
                r = pygame.Rect(start_x, cur_y, toggle_icon_size, toggle_icon_size)
                pygame.draw.rect(screen, (200, 200, 200), r)
                pygame.draw.rect(screen, (0, 0, 0), r, 2)
                icon = icon_dict.get(state)
                if icon:
                    padded_rect = pygame.Rect(r.x + 4, r.y + 4, r.width - 8, r.height - 8)
                    scaled = pygame.transform.smoothscale(icon, (padded_rect.width, padded_rect.height))
                    screen.blit(scaled, padded_rect)
                if lbl == "Shiny":
                    self.shiny_rect = r
                elif lbl == "Gender":
                    self.gender_rect = r
                start_x += toggle_icon_size + toggle_gap
            cur_y += toggle_icon_size + 10

        return cur_y

    def _draw_tab_bar(self, screen):
        tab_height = 45
        tab_width = self.dialog_rect.width // len(self.pages)
        self.tab_rects = {}
        for idx, page in enumerate(self.pages):
            x = self.dialog_rect.x + idx * tab_width
            rect = pygame.Rect(x, self.dialog_rect.bottom - tab_height, tab_width, tab_height)
            fill_color = (180,180,250) if page == self.current_page else (200,200,200)
            pygame.draw.rect(screen, fill_color, rect)
            pygame.draw.rect(screen, (0,0,0), rect, 2)
            # --- Modified Tab Drawing ---
            icon = self.tab_icons.get(page)
            if icon:
                # Scale the icon to roughly 80% of the tab height.
                icon_height = int(rect.height * 0.8)
                factor = icon_height / icon.get_height()
                icon_width = int(icon.get_width() * factor)
                scaled_icon = pygame.transform.smoothscale(icon, (icon_width, icon_height))
                icon_rect = scaled_icon.get_rect(center=rect.center)
                screen.blit(scaled_icon, icon_rect)
            else:
                # Fallback text: for "Availability" and "Relationships", use shorter labels.
                label = page
                if page == "Availability":
                    label = "Locations"
                elif page == "Relationships":
                    label = "Related"
                txt = self.main_font.render(label, True, (0,0,0))
                txt_rect = txt.get_rect(center=rect.center)
                screen.blit(txt, txt_rect)
            self.tab_rects[page] = rect
