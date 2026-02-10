import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json
import glob
from PIL import ImageDraw
from paths_config import paths_config

class SmoothHighlight:
    def __init__(self, widget, normal_color, hover_color, selected_color):
        self.widget = widget
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.selected_color = selected_color
        self.current_color = normal_color
        self.target_color = normal_color
        self.animation_id = None
        self.is_selected = False
        
    def widget_exists(self):
        """Έλεγχος αν το widget υπάρχει ακόμα"""
        try:
            self.widget.winfo_exists()
            return True
        except tk.TclError:
            return False
        
    def animate_color(self, target_color, duration=150):
        """Smooth color animation"""
        # Έλεγχος αν το widget υπάρχει πριν από animation
        if not self.widget_exists():
            if self.animation_id:
                self.widget.after_cancel(self.animation_id)
                self.animation_id = None
            return
            
        if self.animation_id:
            self.widget.after_cancel(self.animation_id)
            
        start_color = self.current_color
        steps = 10
        step_delay = duration // steps
        
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
            
        start_rgb = hex_to_rgb(start_color)
        target_rgb = hex_to_rgb(target_color)
        
        def update_step(step):
            # Έλεγχος αν το widget υπάρχει σε κάθε βήμα
            if not self.widget_exists():
                if self.animation_id:
                    self.widget.after_cancel(self.animation_id)
                    self.animation_id = None
                return
                
            ratio = step / steps
            current_rgb = tuple(
                int(start_rgb[i] + (target_rgb[i] - start_rgb[i]) * ratio)
                for i in range(3)
            )
            current_color = rgb_to_hex(current_rgb)
            self.current_color = current_color
            
            try:
                # Update widget color
                self.widget.configure(bg=current_color)
                for child in self.widget.winfo_children():
                    if isinstance(child, tk.Label):
                        # Διατηρούμε την εικόνα αν υπάρχει
                        current_image = child.cget('image')
                        current_text = child.cget('text')
                        child.configure(bg=current_color)
                        # Επαναφέρουμε την εικόνα και το κείμενο
                        if current_image:
                            child.configure(image=current_image)
                        if current_text:
                            child.configure(text=current_text)
            except tk.TclError:
                # Widget destroyed during animation
                if self.animation_id:
                    self.widget.after_cancel(self.animation_id)
                    self.animation_id = None
                return
            
            if step < steps:
                self.animation_id = self.widget.after(step_delay, update_step, step + 1)
            else:
                self.animation_id = None
                self.current_color = target_color
                
        update_step(1)
    
    def set_hover(self, hover=True):
        """Set hover state with smooth transition"""
        if not self.widget_exists():
            return
            
        if self.is_selected:
            return
            
        if hover:
            self.animate_color(self.hover_color, 100)
        else:
            self.animate_color(self.normal_color, 100)
    
    def set_selected(self, selected=True):
        """Set selected state with smooth transition"""
        if not self.widget_exists():
            return
            
        self.is_selected = selected
        if selected:
            self.animate_color(self.selected_color, 200)
        else:
            self.animate_color(self.normal_color, 200)

class CustomScrollbar(tk.Canvas):
    def __init__(self, parent, orient='vertical', command=None, **kwargs):
        self.command = command
        self.orient = orient
        
        # Default colors that match the theme
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d', 
            'bg_light': '#3c3c3c',
            'accent': '#007acc',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'border': '#555555',
            'hover': '#4a4a4a',
            'selected': '#007acc'
        }
        
        # Override colors if provided
        for key in self.colors:
            if key in kwargs:
                self.colors[key] = kwargs.pop(key)
        
        super().__init__(parent, **kwargs)
        
        self.configure(
            bg=self.colors['bg_medium'],
            highlightthickness=0,
            relief='flat',
            bd=0,
            width=12
        )
        
        self.slider_color = self.colors['bg_light']
        self.slider_hover_color = self.colors['hover']
        self.slider_active_color = self.colors['accent']
        
        self.slider = None
        self.bind_events()
        self.update_idletasks()
        
    def bind_events(self):
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<B1-Motion>", self.on_drag)
        
    def on_enter(self, event):
        self.slider_hover = True
        self.draw_slider()
        
    def on_leave(self, event):
        self.slider_hover = False
        self.draw_slider()
        
    def on_press(self, event):
        self.slider_active = True
        self.draw_slider()
        self._drag_start = event.y if self.orient == 'vertical' else event.x
        
    def on_release(self, event):
        self.slider_active = False
        self.draw_slider()
        
    def on_drag(self, event):
        if hasattr(self, '_drag_start') and self.command:
            current_pos = event.y if self.orient == 'vertical' else event.x
            delta = current_pos - self._drag_start
            
            # ΔΙΟΡΘΩΣΗ: Μετατροπή delta σε ακέραιο αριθμό μονάδων κύλισης
            # Χρησιμοποιούμε συντελεστή κλιμάκωσης για ευαισθησία
            scroll_units = int(delta / 5)  # Ρυθμίστε αυτόν τον διαιρέτη για ευαισθησία
            
            if scroll_units != 0:  # Κύλιση μόνο αν υπάρχει πραγματική κίνηση
                self.command('scroll', scroll_units, 'units')
                self._drag_start = current_pos
        
    def set(self, lo, hi):
        self.lo = float(lo)
        self.hi = float(hi)
        self.draw_slider()
        
    def draw_slider(self):
        self.delete("slider")
        
        if self.lo == 0.0 and self.hi == 1.0:
            return
            
        if self.orient == 'vertical':
            x1, y1 = 2, self.lo * self.winfo_height()
            x2, y2 = self.winfo_width() - 2, self.hi * self.winfo_height()
        else:
            x1, y1 = self.lo * self.winfo_width(), 2
            x2, y2 = self.hi * self.winfo_width(), self.winfo_height() - 2
            
        # Choose color based on state
        if getattr(self, 'slider_active', False):
            color = self.slider_active_color
        elif getattr(self, 'slider_hover', False):
            color = self.slider_hover_color
        else:
            color = self.slider_color
            
        # Draw rounded rectangle for slider
        radius = 4
        self.slider = self.create_round_rect(x1, y1, x2, y2, radius, fill=color, outline="", tags="slider")
        
    def create_round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, **kwargs, smooth=True)

class DDSViewer:
    def __init__(self, root, sync_callback=None, initial_data=None, update_callback=None):
        self.root = root
        self.root.title("Smart Select")
        self.root.geometry("1070x750")
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ SMART SELECT ΠΑΡΑΘΥΡΟΥ
        self.center_window(self.root)
        
        
        self.root.configure(bg="#1e1e1e")
        
        # Χρώματα theme
        self.colors = {
            'bg_dark': '#1e1e1e',
            'bg_medium': '#2d2d2d', 
            'bg_light': '#3c3c3c',
            'accent': '#007acc',
            'text_primary': '#ffffff',
            'text_secondary': '#cccccc',
            'border': '#555555',
            'hover': '#4a4a4a',
            'selected': '#007acc',
            'hover_border': '#666666',
            'selected_border': '#0099ff'
        }
        
        # Μεταβλητές
        self.champions_data = {}
        self.spells_data = {}
        self.current_images = {}
        self.base_path = paths_config.SMART_SELECT_CHAMPIONS_PATH
        self.spells_path = paths_config.SMART_SELECT_SPELLS_PATH
        self.data_file = paths_config.GAME_DATA_JSON 
        self.selected_champion = None
        self.current_skin_index = 0
        self.selected_spells = [None, None]
        self.spell_grid_visible = False
        
        # Callbacks για συγχρονισμό
        self.sync_callback = sync_callback
        self.update_callback = update_callback  # ΝΕΟ: Callback για ενημερώσεις από lobby
        
        # Two-way sync protection flags
        self._block_filter_sync = False
        self.last_synced_filters = []
        self.syncing_from_lobby = False
        self.syncing_to_lobby = False
        self._block_sync = False  # Additional guard
        
        # Dictionaries για τα highlights
        self.champion_highlights = {}
        self.spell_highlights = {}
        self.spell_slot_highlights = {}
        
        # Αρχικά δεδομένα από το lobby
        self.initial_data = initial_data or {}
        
        # Αρχικοποίηση active filters
        self.active_filters = ["w", "p", "b", "di"]
        
        # Φόρτωση δεδομένων
        self.load_game_data()
        
        # Δημιουργία GUI
        self.create_gui()
        
        # Αρχικός συγχρονισμός με τα δεδομένα από το lobby
        self.sync_from_lobby()
        
        # Φόρτωση εικόνων
        self.load_champions_grid()
    
    def center_window(self, window):
        """Κεντράρισμα παραθύρου στην οθόνη"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def cleanup_highlights(self):
        """Καθαρισμός highlights για widgets που έχουν καταστραφεί"""
        champions_to_remove = []
        
        for champ_name, highlight in self.champion_highlights.items():
            if not hasattr(highlight, 'widget_exists') or not highlight.widget_exists():
                champions_to_remove.append(champ_name)
        
        for champ_name in champions_to_remove:
            del self.champion_highlights[champ_name]
        
        # Το ίδιο για spells
        spells_to_remove = []
        for spell_name, highlight in self.spell_highlights.items():
            if not hasattr(highlight, 'widget_exists') or not highlight.widget_exists():
                spells_to_remove.append(spell_name)
        
        for spell_name in spells_to_remove:
            del self.spell_highlights[spell_name]
    
    def sync_from_lobby(self, lobby_data=None):
        """Συγχρονισμός από το lobby με ενισχυμένη προστασία από loops"""
        if self.syncing_from_lobby or getattr(self, '_block_sync', False):
            return
            
        self.syncing_from_lobby = True
        self._block_sync = True  # Additional guard
        
        print(f"DEBUG: Smart Select receiving sync from lobby: {lobby_data}")
        
        try:
            if lobby_data is None:
                lobby_data = self.initial_data
                
            if not lobby_data:
                return
                
            # Συγχρονισμός filters
            if 'active_filters' in lobby_data:
                self.update_filters_from_external(lobby_data['active_filters'])
            
            # Συγχρονισμός champion
            if 'champion' in lobby_data and lobby_data['champion']:
                champion_name = lobby_data['champion']
                if champion_name in self.champions_data:
                    champion_data = self.champions_data[champion_name]
                    self.select_champion(champion_name, champion_data, from_external=True)
            
            # Συγχρονισμός spells
            if 'spells' in lobby_data:
                spells = lobby_data['spells']
                if len(spells) >= 2:
                    self.selected_spells[0] = (spells[0], self.spells_data.get(spells[0], {}))
                    self.selected_spells[1] = (spells[1], self.spells_data.get(spells[1], {}))
                    self.update_spell_slots()
            
            # Συγχρονισμός skin
            if 'skin' in lobby_data and self.selected_champion:
                skin_name = lobby_data['skin']
                champion_name = self.selected_champion[0]
                champion_data = self.selected_champion[1]
                
                # Έλεγχος αν το skin είναι διαθέσιμο για τον champion
                skins = champion_data.get('skins', {})
                if skin_name in skins:
                    # Βρίσκουμε το index του skin
                    skin_names = list(skins.keys())
                    if skin_name in skin_names:
                        self.current_skin_index = skin_names.index(skin_name)
                        self.update_skin_display()
                        
        finally:
            self.syncing_from_lobby = False
            self.root.after(100, lambda: setattr(self, '_block_sync', False))  # Release after delay

    def select_champion_from_external(self, champion_name):
        """Επιλογή champion από εξωτερική πηγή (lobby)"""
        print(f"DEBUG: Selecting champion from external: {champion_name}")
        if champion_name in self.champions_data:
            champion_data = self.champions_data[champion_name]
            self.select_champion(champion_name, champion_data, from_external=True)

    def update_spells_from_external(self, spells_list):
        """Ενημέρωση spells από εξωτερική πηγή"""
        print(f"DEBUG: Updating spells from external: {spells_list}")
        if len(spells_list) >= 2:
            self.selected_spells[0] = (spells_list[0], self.spells_data.get(spells_list[0], {}))
            self.selected_spells[1] = (spells_list[1], self.spells_data.get(spells_list[1], {}))
            self.update_spell_slots()

    def update_skin_from_external(self, skin_name):
        """Ενημέρωση skin από εξωτερική πηγή"""
        print(f"DEBUG: Updating skin from external: {skin_name}")
        if hasattr(self, 'selected_champion') and self.selected_champion:
            champion_name = self.selected_champion[0]
            champion_data = self.selected_champion[1]
            
            skins = champion_data.get('skins', {})
            if skin_name in skins:
                skin_names = list(skins.keys())
                if skin_name in skin_names:
                    self.current_skin_index = skin_names.index(skin_name)
                    self.update_skin_display()

    def update_filters_from_external(self, active_filters):
        """Ενημέρωση filters από Lobby προς Smart Select"""
        if self.syncing_to_lobby or getattr(self, '_block_filter_sync', False):
            return
            
        print(f"DEBUG: Receiving filters FROM Lobby: {active_filters}")
        
        # Set protection flags
        self.syncing_from_lobby = True
        self._block_filter_sync = True
        
        # Έλεγχος αν πραγματικά άλλαξαν τα filters
        if active_filters == self.active_filters:
            return
        
        self.active_filters = active_filters
        self.last_synced_filters = active_filters.copy()
        
        # Ενημέρωση των checkboxes χωρίς trigger sync
        filter_mapping = {
            "w": "working",
            "p": "playable", 
            "b": "bug_issues",
            "di": "dodge_issues"
        }
        
        for condition, filter_name in filter_mapping.items():
            if hasattr(self, 'filter_vars') and filter_name in self.filter_vars:
                var = self.filter_vars[filter_name]
                # Remove trace temporarily to prevent loops
                trace_info = var.trace_info()
                if trace_info:
                    var.trace_vdelete("w", trace_info[0][1])
                
                var.set(condition in active_filters)
                
                # Restore trace
                var.trace('w', self.on_filter_changed_sync)
        
        # Επανάληψη φόρτωσης champions με τα νέα filters
        self.load_champions_grid()
        
        print(f"DEBUG: Smart Select UI updated with Lobby filters")
        
        # Release protection
        self.root.after(100, lambda: setattr(self, 'syncing_from_lobby', False))
        self.root.after(150, lambda: setattr(self, '_block_filter_sync', False))
    
    def on_filter_changed_sync(self, *args):
        """Συγχρονισμός filters από Smart Select προς Lobby"""
        if self.syncing_from_lobby or getattr(self, '_block_filter_sync', False):
            return
        
        # Set protection flag
        self._block_filter_sync = True
        
        filter_mapping = {
            "working": "w",
            "playable": "p", 
            "bug_issues": "b",
            "dodge_issues": "di"
        }
        
        active_filters = []
        for filter_name, condition in filter_mapping.items():
            if hasattr(self, 'filter_vars') and filter_name in self.filter_vars:
                var = self.filter_vars[filter_name]
                if var.get():
                    active_filters.append(condition)
        
        # Only sync if filters actually changed
        if active_filters != getattr(self, 'last_synced_filters', []):
            print(f"DEBUG: Smart Select filters changed to: {active_filters}")
            self.active_filters = active_filters
            self.last_synced_filters = active_filters.copy()
            
            # Reload champions grid with new filters
            self.load_champions_grid()
            
            # TWO-WAY SYNC: Στέλνουμε τα filters πίσω στο Lobby
            if self.sync_callback and not self.syncing_from_lobby:
                self.syncing_to_lobby = True
                try:
                    self.sync_callback({
                        "type": "filters", 
                        "filters": active_filters
                    })
                    print("DEBUG: Sent filters sync to Lobby")
                finally:
                    self.syncing_to_lobby = False
        
        # Release protection after a short delay
        self.root.after(100, lambda: setattr(self, '_block_filter_sync', False))

    def load_game_data(self):
        """Φόρτωση δεδομένων από το JSON αρχείο"""
        try:
            if not os.path.exists(self.data_file):
                messagebox.showerror("Error", f"Data file not found: {self.data_file}")
                return
                
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.champions_data = data.get('champions', {})
                self.spells_data = data.get('spells', {})
            print(f"Loaded {len(self.champions_data)} champions and {len(self.spells_data)} spells")
        except Exception as e:
            messagebox.showerror("Error", f"Could not load game data: {str(e)}")
    
    def create_gui(self):
        """Δημιουργία γραφικού περιβάλλοντος"""
        # Κύριο frame
        main_frame = tk.Frame(self.root, bg=self.colors['bg_dark'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        title_label = tk.Label(
            header_frame,
            text="SMART SELECT",
            font=('Arial', 20, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg_dark']
        )
        title_label.pack()
        
        # Content frame
        content_frame = tk.Frame(main_frame, bg=self.colors['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left frame για champions και spells
        left_frame = tk.Frame(content_frame, bg=self.colors['bg_medium'], relief="raised", bd=1)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Controls frame
        controls_frame = tk.Frame(left_frame, bg=self.colors['bg_medium'])
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Search και Filters
        search_filter_frame = tk.Frame(controls_frame, bg=self.colors['bg_medium'])
        search_filter_frame.pack(fill=tk.X, pady=5)
        
        # Search
        search_frame = tk.Frame(search_filter_frame, bg=self.colors['bg_medium'])
        search_frame.pack(side=tk.LEFT, padx=(0, 20))
        
        tk.Label(
            search_frame,
            text="🔍 Search:",
            font=('Arial', 9, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_medium']
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            width=20,
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            relief="flat",
            insertbackground=self.colors['text_primary']
        )
        search_entry.pack(side=tk.LEFT)
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # Filters frame με checkboxes
        filter_frame = tk.Frame(search_filter_frame, bg=self.colors['bg_medium'])
        filter_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(
            filter_frame,
            text="Filters:",
            font=('Arial', 9, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_medium']
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        # Μεταβλητές για τα checkboxes
        self.filter_vars = {
            'working': tk.BooleanVar(value=True),
            'playable': tk.BooleanVar(value=True),
            'bug_issues': tk.BooleanVar(value=True),
            'dodge_issues': tk.BooleanVar(value=True)
        }
        
        # Bind trace events για συγχρονισμό
        for var in self.filter_vars.values():
            var.trace('w', self.on_filter_changed_sync)
        
        # Δημιουργία checkboxes
        filters_checkbox_frame = tk.Frame(filter_frame, bg=self.colors['bg_medium'])
        filters_checkbox_frame.pack(side=tk.LEFT)
        
        # Working checkbox
        self.working_cb = tk.Checkbutton(
            filters_checkbox_frame,
            text="Working",
            variable=self.filter_vars['working'],
            command=self.on_filter_changed,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_medium'],
            activeforeground=self.colors['text_primary'],
            cursor="hand2"
        )
        self.working_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # Playable checkbox
        self.playable_cb = tk.Checkbutton(
            filters_checkbox_frame,
            text="Playable",
            variable=self.filter_vars['playable'],
            command=self.on_filter_changed,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_medium'],
            activeforeground=self.colors['text_primary'],
            cursor="hand2"
        )
        self.playable_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # Bug Issues checkbox
        self.bug_cb = tk.Checkbutton(
            filters_checkbox_frame,
            text="Bug",
            variable=self.filter_vars['bug_issues'],
            command=self.on_filter_changed,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_medium'],
            activeforeground=self.colors['text_primary'],
            cursor="hand2"
        )
        self.bug_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # Dodge Issues checkbox
        self.dodge_cb = tk.Checkbutton(
            filters_checkbox_frame,
            text="Dodge Issues",
            variable=self.filter_vars['dodge_issues'],
            command=self.on_filter_changed,
            bg=self.colors['bg_medium'],
            fg=self.colors['text_primary'],
            selectcolor=self.colors['bg_dark'],
            activebackground=self.colors['bg_medium'],
            activeforeground=self.colors['text_primary'],
            cursor="hand2"
        )
        self.dodge_cb.pack(side=tk.LEFT, padx=(0, 10))
        
        # Canvas με scrollbar για champions
        self.canvas_frame = tk.Frame(left_frame, bg=self.colors['bg_medium'])
        self.canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            bg=self.colors['bg_medium'],
            highlightthickness=0
        )
        
        # Custom scrollbar για champions
        self.v_scrollbar = CustomScrollbar(
            self.canvas_frame,
            orient=tk.VERTICAL,
            command=self.canvas.yview,
            bg_dark=self.colors['bg_dark'],
            bg_medium=self.colors['bg_medium'],
            bg_light=self.colors['bg_light'],
            accent=self.colors['accent'],
            hover=self.colors['hover']
        )
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame για το πλέγμα champions
        self.grid_frame = tk.Frame(self.canvas, bg=self.colors['bg_medium'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        
        # ΑΠΛΑ SPELL SLOTS - ΣΤΑΘΕΡΟ ΜΕΓΕΘΟΣ
        spells_frame = tk.Frame(left_frame, bg=self.colors['bg_medium'])
        spells_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            spells_frame,
            text="⚡ SUMMONER SPELLS",
            font=('Arial', 11, 'bold'),
            fg=self.colors['accent'],
            bg=self.colors['bg_medium']
        ).pack(anchor=tk.W, pady=(0, 10))
        
        slots_frame = tk.Frame(spells_frame, bg=self.colors['bg_medium'])
        slots_frame.pack(fill=tk.X)
        
        # Spell Slot 1 - ΣΤΑΘΕΡΟ ΜΕΓΕΘΟΣ
        self.slot1_frame = tk.Frame(slots_frame, bg=self.colors['bg_light'], relief="raised", bd=1, width=50, height=50)
        self.slot1_frame.pack(side=tk.LEFT, padx=(0, 10))
        self.slot1_frame.pack_propagate(False)
        
        self.slot1_label = tk.Label(
            self.slot1_frame,
            text="➕\nSlot 1",
            font=('Arial', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_light'],
            cursor="hand2",
            justify=tk.CENTER
        )
        self.slot1_label.pack(expand=True, fill=tk.BOTH)
        self.slot1_label.bind("<Button-1>", lambda e: self.toggle_spell_grid(0))
        
        # Spell Slot 2 - ΣΤΑΘΕΡΟ ΜΕΓΕΘΟΣ
        self.slot2_frame = tk.Frame(slots_frame, bg=self.colors['bg_light'], relief="raised", bd=1, width=50, height=50)
        self.slot2_frame.pack(side=tk.LEFT)
        self.slot2_frame.pack_propagate(False)
        
        self.slot2_label = tk.Label(
            self.slot2_frame,
            text="➕\nSlot 2", 
            font=('Arial', 9),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_light'],
            cursor="hand2",
            justify=tk.CENTER
        )
        self.slot2_label.pack(expand=True, fill=tk.BOTH)
        self.slot2_label.bind("<Button-1>", lambda e: self.toggle_spell_grid(1))
        
        # SPELL GRID FRAME (αρχικά κρυφό)
        self.spell_grid_frame = tk.Frame(left_frame, bg=self.colors['bg_medium'], relief="raised", bd=1)
        
        # Spell grid controls
        spell_controls_frame = tk.Frame(self.spell_grid_frame, bg=self.colors['bg_medium'])
        spell_controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.current_slot_var = tk.StringVar(value="Selecting for: Slot 1")
        slot_label = tk.Label(
            spell_controls_frame,
            textvariable=self.current_slot_var,
            font=('Arial', 10, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_medium']
        )
        slot_label.pack(side=tk.LEFT)
        
        close_btn = tk.Button(
            spell_controls_frame,
            text="Close",
            command=self.hide_spell_grid,
            bg=self.colors['bg_light'],
            fg=self.colors['text_primary'],
            cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT)
        
        # Canvas για spell grid
        self.spell_canvas_frame = tk.Frame(self.spell_grid_frame, bg=self.colors['bg_medium'])
        self.spell_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.spell_canvas = tk.Canvas(
            self.spell_canvas_frame,
            bg=self.colors['bg_medium'],
            highlightthickness=0
        )
        
        # Custom scrollbar για spells
        self.spell_v_scrollbar = CustomScrollbar(
            self.spell_canvas_frame,
            orient=tk.VERTICAL,
            command=self.spell_canvas.yview,
            bg_dark=self.colors['bg_dark'],
            bg_medium=self.colors['bg_medium'],
            bg_light=self.colors['bg_light'],
            accent=self.colors['accent'],
            hover=self.colors['hover']
        )
        
        self.spell_canvas.configure(yscrollcommand=self.spell_v_scrollbar.set)
        
        self.spell_v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.spell_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame για το πλέγμα spells
        self.spells_grid_frame = tk.Frame(self.spell_canvas, bg=self.colors['bg_medium'])
        self.spell_canvas_window = self.spell_canvas.create_window((0, 0), window=self.spells_grid_frame, anchor="nw")
        
        # Right frame για skins
        self.right_frame = tk.Frame(content_frame, bg=self.colors['bg_medium'], relief="raised", bd=1)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH)
        self.right_frame.configure(width=400)
        
        # Skin controls frame (βελάκια καρουζέλ)
        skin_controls_frame = tk.Frame(self.right_frame, bg=self.colors['bg_medium'])
        skin_controls_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        
        # Previous button
        self.prev_btn = tk.Button(
            skin_controls_frame,
            text="◀",
            command=self.previous_skin,
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            font=('Arial', 14, 'bold'),
            width=3,
            relief="flat",
            cursor="hand2"
        )
        self.prev_btn.pack(side=tk.LEFT)
        
        # Skin name
        self.skin_name_label = tk.Label(
            skin_controls_frame,
            text="No champion selected",
            font=('Arial', 14, 'bold'),
            fg=self.colors['text_primary'],
            bg=self.colors['bg_medium']
        )
        self.skin_name_label.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=10)
        
        # Next button
        self.next_btn = tk.Button(
            skin_controls_frame,
            text="▶",
            command=self.next_skin,
            bg=self.colors['accent'],
            fg=self.colors['text_primary'],
            font=('Arial', 14, 'bold'),
            width=3,
            relief="flat",
            cursor="hand2"
        )
        self.next_btn.pack(side=tk.RIGHT)
        
        # Canvas για skin image
        self.skin_canvas = tk.Canvas(
            self.right_frame,
            bg=self.colors['bg_light'],
            highlightthickness=0
        )
        self.skin_canvas.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Skin counter label
        self.skin_counter_label = tk.Label(
            self.right_frame,
            text="",
            font=('Arial', 10),
            fg=self.colors['text_secondary'],
            bg=self.colors['bg_medium']
        )
        self.skin_counter_label.pack(pady=(0, 10))
        
        # Bind events
        self.skin_canvas.bind("<Configure>", self.on_skin_canvas_configure)
        self.grid_frame.bind("<Configure>", self.on_frame_configure)
        self.spells_grid_frame.bind("<Configure>", self.on_spells_frame_configure)
        
        # Bind scroll wheel events
        self.bind_scroll_events()
        
        # Bind hover events για spell slots
        self.bind_spell_slots_hover()
        
        # Initialize spell slot highlights
        self.spell_slot_highlights = {}
        self.spell_slot_highlights['slot1'] = SmoothHighlight(
            self.slot1_frame, 
            self.colors['bg_light'], 
            self.colors['hover'], 
            self.colors['selected']
        )
        self.spell_slot_highlights['slot2'] = SmoothHighlight(
            self.slot2_frame, 
            self.colors['bg_light'], 
            self.colors['hover'], 
            self.colors['selected']
        )
    
    def on_filter_changed(self, event=None):
        """Χειρισμός αλλαγής στα filter checkboxes"""
        self.load_champions_grid()
    
    def bind_spell_slots_hover(self):
        """Bind hover events για τα spell slots"""
        self.slot1_frame.bind("<Enter>", lambda e: self.spell_slot_highlights['slot1'].set_hover(True))
        self.slot1_frame.bind("<Leave>", lambda e: self.spell_slot_highlights['slot1'].set_hover(False))
        self.slot1_label.bind("<Enter>", lambda e: self.spell_slot_highlights['slot1'].set_hover(True))
        self.slot1_label.bind("<Leave>", lambda e: self.spell_slot_highlights['slot1'].set_hover(False))
        
        self.slot2_frame.bind("<Enter>", lambda e: self.spell_slot_highlights['slot2'].set_hover(True))
        self.slot2_frame.bind("<Leave>", lambda e: self.spell_slot_highlights['slot2'].set_hover(False))
        self.slot2_label.bind("<Enter>", lambda e: self.spell_slot_highlights['slot2'].set_hover(True))
        self.slot2_label.bind("<Leave>", lambda e: self.spell_slot_highlights['slot2'].set_hover(False))
    
    def bind_scroll_events(self):
        """Bind scroll wheel events για όλα τα scrollable elements"""
        # Για champions canvas
        self.canvas_frame.bind("<MouseWheel>", self.on_mousewheel_champions)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel_champions)
        self.grid_frame.bind("<MouseWheel>", self.on_mousewheel_champions)
        
        # Για spells canvas
        self.spell_canvas_frame.bind("<MouseWheel>", self.on_mousewheel_spells)
        self.spell_canvas.bind("<MouseWheel>", self.on_mousewheel_spells)
        self.spells_grid_frame.bind("<MouseWheel>", self.on_mousewheel_spells)
        
        # Για skin navigation με scroll wheel
        self.skin_canvas.bind("<MouseWheel>", self.on_mousewheel_skin)
        
        # Bind στο main frame για να πιάνει παντού
        self.root.bind("<MouseWheel>", self.on_mousewheel_global)
    
    def on_mousewheel_global(self, event):
        """Global scroll που ελέγχει πού βρίσκεται το mouse"""
        x, y = event.x, event.y
        
        try:
            champions_bbox = self.canvas_frame.bbox()
            if champions_bbox and self.is_point_in_widget(x, y, self.canvas_frame):
                self.on_mousewheel_champions(event)
                return
        except:
            pass
            
        if self.spell_grid_visible:
            try:
                spells_bbox = self.spell_canvas_frame.bbox()
                if spells_bbox and self.is_point_in_widget(x, y, self.spell_canvas_frame):
                    self.on_mousewheel_spells(event)
                    return
            except:
                pass
        
        try:
            skin_bbox = self.skin_canvas.bbox()
            if skin_bbox and self.is_point_in_widget(x, y, self.skin_canvas):
                self.on_mousewheel_skin(event)
                return
        except:
            pass
    
    def is_point_in_widget(self, x, y, widget):
        """Ελέγχει αν το σημείο (x,y) βρίσκεται μέσα στο widget"""
        try:
            wx = widget.winfo_rootx()
            wy = widget.winfo_rooty()
            wwidth = widget.winfo_width()
            wheight = widget.winfo_height()
            
            return (wx <= x <= wx + wwidth and wy <= y <= wy + wheight)
        except:
            return False
    
    def on_mousewheel_champions(self, event):
        """Scroll champions grid με mouse wheel"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_mousewheel_spells(self, event):
        """Scroll spells grid με mouse wheel"""
        self.spell_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
    
    def on_mousewheel_skin(self, event):
        """Αλλαγή skins με mouse wheel"""
        if hasattr(self, 'skins_list') and self.skins_list:
            if event.delta > 0:
                self.previous_skin()
            else:
                self.next_skin()
    
    def find_champion_icon_path(self, champion_id):
        """Βρίσκει Square DDS αρχείο για champion"""
        champion_folder = os.path.join(self.base_path, champion_id, "Info")
        
        if not os.path.exists(champion_folder):
            return None
        
        patterns = [
            f"{champion_id}_Square.dds",
            f"XenZhao_Square.dds",
            f"*_Square.dds",
            f"*__Square.dds", 
            f"*Square*.dds"
        ]
        
        for pattern in patterns:
            search_pattern = os.path.join(champion_folder, pattern)
            files = glob.glob(search_pattern)
            if files:
                return files[0]
        
        return None
    
    def find_spell_icon_path(self, spell_id, display_name):
        """Βρίσκει DDS αρχείο για spell"""
        # ΕΙΔΙΚΗ ΠΕΡΙΠΤΩΣΗ ΓΙΑ GHOST - χρησιμοποιεί το Summoner_haste.dds
        if spell_id == "SummonerHaste" or display_name.lower() == "ghost":
            haste_path = os.path.join(self.spells_path, "Summoner_haste.dds")
            if os.path.exists(haste_path):
                return haste_path
        
        possible_names = [
            f"{spell_id}.dds",
            f"Summoner{display_name}.dds",
            f"Summoner_{display_name}.dds",
            f"{spell_id.lower()}.dds"
        ]
        
        for filename in possible_names:
            spell_path = os.path.join(self.spells_path, filename)
            if os.path.exists(spell_path):
                return spell_path
        
        return None
    
    def find_skin_loadscreen_path(self, champion_id, skin_id):
        """Βρίσκει LoadScreen DDS αρχείο για skin"""
        if skin_id == 0:
            filename = f"{champion_id}LoadScreen.dds"
        else:
            filename = f"{champion_id}LoadScreen_{skin_id}.dds"
        
        skin_path = os.path.join(self.base_path, champion_id, filename)
        
        if os.path.exists(skin_path):
            return skin_path
        
        return None
    
    def load_dds_image(self, file_path, size=(70, 70)):
        """Φόρτωση και resize DDS εικόνας"""
        try:
            if file_path and os.path.exists(file_path):
                image = Image.open(file_path)
                image = image.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
            else:
                img = Image.new('RGB', size, color='#2d2d2d')
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading image {file_path}: {str(e)}")
            img = Image.new('RGB', size, color='#2d2d2d')
            return ImageTk.PhotoImage(img)
    
    def load_spell_image(self, file_path):
        """Φόρτωση spell εικόνας - ΜΙΚΡΗ ΕΙΚΟΝΑ ΓΙΑ ΣΤΑΘΕΡΟ ΜΕΓΕΘΟΣ"""
        try:
            if file_path and os.path.exists(file_path):
                image = Image.open(file_path)
                image = image.resize((50, 50), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image)
            else:
                img = Image.new('RGB', (50, 50), color='#2d2d2d')
                return ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading spell image {file_path}: {str(e)}")
            img = Image.new('RGB', (50, 50), color='#2d2d2d')
            return ImageTk.PhotoImage(img)
    
    def load_skin_image_with_aspect_ratio(self, file_path, max_width, max_height):
        """Φόρτωση skin εικόνας διατηρώντας τις αναλογίες"""
        try:
            if file_path and os.path.exists(file_path):
                image = Image.open(file_path)
                original_width, original_height = image.size
                
                ratio = min(max_width / original_width, max_height / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(image), new_width, new_height
            else:
                img = Image.new('RGB', (max_width, max_height), color='#2d2d2d')
                return ImageTk.PhotoImage(img), max_width, max_height
        except Exception as e:
            print(f"Error loading skin image {file_path}: {str(e)}")
            img = Image.new('RGB', (max_width, max_height), color='#2d2d2d')
            return ImageTk.PhotoImage(img), max_width, max_height
    
    def on_skin_canvas_configure(self, event):
        self.update_skin_display()
    
    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        # Update the custom scrollbar
        self.v_scrollbar.set(*self.canvas.yview())
    
    def on_spells_frame_configure(self, event):
        self.spell_canvas.configure(scrollregion=self.spell_canvas.bbox("all"))
        # Update the custom scrollbar
        self.spell_v_scrollbar.set(*self.spell_canvas.yview())
    
    def on_search_changed(self, event=None):
        self.load_champions_grid()
    
    def toggle_spell_grid(self, slot_index):
        if self.spell_grid_visible:
            self.hide_spell_grid()
        else:
            self.show_spell_grid(slot_index)
    
    def show_spell_grid(self, slot_index):
        self.current_slot = slot_index
        self.current_slot_var.set(f"Selecting for: Slot {slot_index + 1}")
        self.spell_grid_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.spell_grid_visible = True
        self.load_spells_grid()
    
    def hide_spell_grid(self):
        self.spell_grid_frame.pack_forget()
        self.spell_grid_visible = False
    
    def previous_skin(self):
        """Προηγούμενο skin"""
        if hasattr(self, 'skins_list') and self.skins_list:
            self.current_skin_index = (self.current_skin_index - 1) % len(self.skins_list)
            self.update_skin_display()
            
            # Συγχρονισμός skin με lobby
            if self.selected_champion and self.sync_callback and not self.syncing_from_lobby:
                self.syncing_to_lobby = True
                try:
                    skin_name = self.skins_names[self.current_skin_index]
                    sync_data = {
                        "type": "skin", 
                        "champion": self.selected_champion[0],
                        "skin": skin_name
                    }
                    self.sync_callback(sync_data)
                finally:
                    self.syncing_to_lobby = False
    
    def next_skin(self):
        """Επόμενο skin"""
        if hasattr(self, 'skins_list') and self.skins_list:
            self.current_skin_index = (self.current_skin_index + 1) % len(self.skins_list)
            self.update_skin_display()
            
            # Συγχρονισμός skin με lobby
            if self.selected_champion and self.sync_callback and not self.syncing_from_lobby:
                self.syncing_to_lobby = True
                try:
                    skin_name = self.skins_names[self.current_skin_index]
                    sync_data = {
                        "type": "skin", 
                        "champion": self.selected_champion[0],
                        "skin": skin_name
                    }
                    self.sync_callback(sync_data)
                finally:
                    self.syncing_to_lobby = False
    
    def load_champions_grid(self):
        # Καθαρισμός highlights πριν από νέα φόρτωση
        self.cleanup_highlights()
        
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        search_text = self.search_var.get().lower()
        
        filtered_champions = []
        
        for champ_name, champ_data in self.champions_data.items():
            if search_text and search_text not in champ_name.lower():
                continue
            
            condition = champ_data.get('condition', '')
            
            # ΕΛΕΓΧΟΣ: Αν είναι άδεια όλα τα checkboxes, ΝΑ ΜΗΝ ΕΜΦΑΝΙΖΕΙ ΚΑΝΕΝΑ CHAMPION
            any_filter_selected = (self.filter_vars['working'].get() or 
                                 self.filter_vars['playable'].get() or 
                                 self.filter_vars['bug_issues'].get() or 
                                 self.filter_vars['dodge_issues'].get())
            
            # Αν δεν έχει επιλεγεί κανένα φίλτρο, ΜΗΝ εμφανίζεις κανένα champion
            if not any_filter_selected:
                continue
            
            # Εφαρμογή φίλτρων βάσει των checkboxes
            show_champion = False
            
            if self.filter_vars['working'].get() and condition == 'w':
                show_champion = True
            if self.filter_vars['playable'].get() and condition == 'p':
                show_champion = True
            if self.filter_vars['bug_issues'].get() and condition == 'b':
                show_champion = True
            if self.filter_vars['dodge_issues'].get() and condition == 'di':
                show_champion = True
            
            if show_champion:
                filtered_champions.append((champ_name, champ_data))
        
        filtered_champions.sort()
        
        max_cols = 6
        row, col = 0, 0
        
        for champ_name, champ_data in filtered_champions:
            champion_id = champ_data['champion_id']
            icon_path = self.find_champion_icon_path(champion_id)
            
            # Δημιουργία card frame
            card_frame = tk.Frame(self.grid_frame, bg=self.colors['bg_light'], relief="raised", bd=1)
            card_frame.grid(row=row, column=col, padx=3, pady=3)
            
            # Δημιουργία highlight manager για αυτό το card
            highlight = SmoothHighlight(
                card_frame,
                self.colors['bg_light'],
                self.colors['hover'],
                self.colors['selected']
            )
            self.champion_highlights[champ_name] = highlight
            
            # Ελέγχει αν αυτό το champion είναι επιλεγμένο
            is_selected = self.selected_champion and self.selected_champion[0] == champ_name
            if is_selected:
                highlight.set_selected(True)
            
            photo = self.load_dds_image(icon_path, size=(70, 70))
            self.current_images[f"{champion_id}_icon"] = photo
            
            img_label = tk.Label(
                card_frame,
                image=photo,
                bg=highlight.current_color,
                cursor="hand2"
            )
            img_label.pack(padx=5, pady=5)
            
            name_label = tk.Label(
                card_frame,
                text=champ_name,
                font=('Arial', 8, 'bold'),
                fg=self.colors['text_primary'],
                bg=highlight.current_color,
                cursor="hand2"
            )
            name_label.pack(padx=5, pady=(0, 5))
            
            # Bind events
            img_label.bind("<MouseWheel>", self.on_mousewheel_champions)
            name_label.bind("<MouseWheel>", self.on_mousewheel_champions)
            card_frame.bind("<MouseWheel>", self.on_mousewheel_champions)
            
            # Smooth hover events
            img_label.bind("<Enter>", lambda e, h=highlight: h.set_hover(True))
            img_label.bind("<Leave>", lambda e, h=highlight: h.set_hover(False))
            name_label.bind("<Enter>", lambda e, h=highlight: h.set_hover(True))
            name_label.bind("<Leave>", lambda e, h=highlight: h.set_hover(False))
            card_frame.bind("<Enter>", lambda e, h=highlight: h.set_hover(True))
            card_frame.bind("<Leave>", lambda e, h=highlight: h.set_hover(False))
            
            img_label.bind("<Button-1>", lambda e, name=champ_name, data=champ_data: self.select_champion(name, data))
            name_label.bind("<Button-1>", lambda e, name=champ_name, data=champ_data: self.select_champion(name, data))
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        for i in range(max_cols):
            self.grid_frame.columnconfigure(i, weight=1)
        
        # Update scrollbar after loading content
        self.canvas.update_idletasks()
        self.v_scrollbar.set(*self.canvas.yview())
    
    def load_spells_grid(self):
        # Καθαρισμός highlights πριν από νέα φόρτωση
        self.cleanup_highlights()
        
        for widget in self.spells_grid_frame.winfo_children():
            widget.destroy()
        
        self.spell_highlights.clear()
        
        max_cols = 7
        row, col = 0, 0
        
        for spell_name, spell_data in self.spells_data.items():
            spell_id = spell_data['spell_id']
            display_name = spell_name.replace(' ', '')
            
            spell_path = self.find_spell_icon_path(spell_id, display_name)
            
            # Δημιουργία card frame
            card_frame = tk.Frame(self.spells_grid_frame, bg=self.colors['bg_light'], relief="raised", bd=1)
            card_frame.grid(row=row, column=col, padx=3, pady=3)
            
            # Δημιουργία highlight manager
            highlight = SmoothHighlight(
                card_frame,
                self.colors['bg_light'],
                self.colors['hover'],
                self.colors['selected']
            )
            self.spell_highlights[spell_name] = highlight
            
            # Έλεγχος αν το spell είναι επιλεγμένο
            is_selected = any(spell and spell[0] == spell_name for spell in self.selected_spells)
            if is_selected:
                highlight.set_selected(True)
            
            photo = self.load_spell_image(spell_path)
            self.current_images[f"{spell_id}_icon"] = photo
            
            img_label = tk.Label(
                card_frame,
                image=photo,
                bg=highlight.current_color,
                cursor="hand2"
            )
            img_label.pack(padx=5, pady=5)
            
            name_label = tk.Label(
                card_frame,
                text=spell_name,
                font=('Arial', 7),
                fg=self.colors['text_primary'],
                bg=highlight.current_color,
                cursor="hand2"
            )
            name_label.pack(padx=5, pady=(0, 5))
            
            # Bind events
            img_label.bind("<MouseWheel>", self.on_mousewheel_spells)
            name_label.bind("<MouseWheel>", self.on_mousewheel_spells)
            card_frame.bind("<MouseWheel>", self.on_mousewheel_spells)
            
            # Smooth hover events
            img_label.bind("<Enter>", lambda e, h=highlight: h.set_hover(True))
            img_label.bind("<Leave>", lambda e, h=highlight: h.set_hover(False))
            name_label.bind("<Enter>", lambda e, h=highlight: h.set_hover(True))
            name_label.bind("<Leave>", lambda e, h=highlight: h.set_hover(False))
            card_frame.bind("<Enter>", lambda e, h=highlight: h.set_hover(True))
            card_frame.bind("<Leave>", lambda e, h=highlight: h.set_hover(False))
            
            img_label.bind("<Button-1>", lambda e, name=spell_name, data=spell_data: self.select_spell(name, data))
            name_label.bind("<Button-1>", lambda e, name=spell_name, data=spell_data: self.select_spell(name, data))
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        for i in range(max_cols):
            self.spells_grid_frame.columnconfigure(i, weight=1)
        
        # Update scrollbar after loading content
        self.spell_canvas.update_idletasks()
        self.spell_v_scrollbar.set(*self.spell_canvas.yview())
    
    def select_spell(self, spell_name, spell_data):
        if hasattr(self, 'current_slot'):
            self.selected_spells[self.current_slot] = (spell_name, spell_data)
            self.update_spell_slots()
            self.hide_spell_grid()
            
            # Συγχρονισμός με lobby
            if self.sync_callback and not self.syncing_from_lobby:
                self.syncing_to_lobby = True
                try:
                    sync_data = {
                        "type": "spell",
                        "slot": self.current_slot,
                        "spell": spell_name
                    }
                    self.sync_callback(sync_data)
                finally:
                    self.syncing_to_lobby = False
    
    def update_spell_slots(self):
        # Ενημέρωση spell slots με εικόνες
        if self.selected_spells[0]:
            spell_name, spell_data = self.selected_spells[0]
            spell_id = spell_data['spell_id']
            display_name = spell_name.replace(' ', '')
            spell_path = self.find_spell_icon_path(spell_id, display_name)
            
            photo = self.load_spell_image(spell_path)
            self.slot1_label.config(
                image=photo,
                text="",  # ΜΟΝΟ ΕΙΚΟΝΑ, ΟΧΙ ΚΕΙΜΕΝΟ
                compound=tk.CENTER
            )
            self.slot1_label.image = photo  # Keep reference
            self.spell_slot_highlights['slot1'].set_selected(True)
        
        if self.selected_spells[1]:
            spell_name, spell_data = self.selected_spells[1]
            spell_id = spell_data['spell_id']
            display_name = spell_name.replace(' ', '')
            spell_path = self.find_spell_icon_path(spell_id, display_name)
            
            photo = self.load_spell_image(spell_path)
            self.slot2_label.config(
                image=photo,
                text="",  # ΜΟΝΟ ΕΙΚΟΝΑ, ΟΧΙ ΚΕΙΜΕΝΟ
                compound=tk.CENTER
            )
            self.slot2_label.image = photo  # Keep reference
            self.spell_slot_highlights['slot2'].set_selected(True)
    
    def select_champion(self, champion_name, champion_data, from_external=False):
        """Επιλογή champion με προστασία από destroyed widgets"""
        # Απενεργοποίηση του προηγούμενου selected champion - με προστασία
        if (self.selected_champion and 
            self.selected_champion[0] in self.champion_highlights):
            
            highlight = self.champion_highlights[self.selected_champion[0]]
            # Έλεγχος αν το highlight ακόμα υπάρχει και είναι valid
            if hasattr(highlight, 'widget_exists') and highlight.widget_exists():
                highlight.set_selected(False)
            else:
                # Αν το widget έχει καταστραφεί, αφαίρεσέ το από το dictionary
                del self.champion_highlights[self.selected_champion[0]]
        
        self.selected_champion = (champion_name, champion_data)
        self.skin_name_label.config(text=champion_name)
        self.load_champion_skins(champion_data)
        
        # Ενεργοποίηση του νέου selected champion - με προστασία
        if champion_name in self.champion_highlights:
            highlight = self.champion_highlights[champion_name]
            if hasattr(highlight, 'widget_exists') and highlight.widget_exists():
                highlight.set_selected(True)
            else:
                # Αν το widget έχει καταστραφεί, δημιούργησε νέο highlight
                del self.champion_highlights[champion_name]
                
        # Συγχρονισμός με lobby ΜΟΝΟ αν δεν προέρχεται από external source
        if not from_external and self.sync_callback and not self.syncing_from_lobby:
            self.syncing_to_lobby = True
            try:
                sync_data = {
                    "type": "champion",
                    "champion": champion_name,
                    "skin": self.skins_names[0] if hasattr(self, 'skins_names') and self.skins_names else "Classic"
                }
                self.sync_callback(sync_data)
            finally:
                self.syncing_to_lobby = False
    
    def load_champion_skins(self, champion_data):
        champion_id = champion_data['champion_id']
        skins = champion_data.get('skins', {})
        
        self.skins_list = []
        self.skins_names = []
        
        for skin_name, skin_id in sorted(skins.items(), key=lambda x: x[1]):
            self.skins_list.append(skin_id)
            self.skins_names.append(skin_name)
        
        self.current_skin_index = 0
        self.update_skin_display()
    
    def update_skin_display(self):
        if not hasattr(self, 'skins_list') or not self.skins_list:
            self.skin_canvas.delete("all")
            self.skin_counter_label.config(text="")
            return
        
        champion_id = self.selected_champion[1]['champion_id']
        skin_id = self.skins_list[self.current_skin_index]
        skin_name = self.skins_names[self.current_skin_index]
        
        canvas_width = self.skin_canvas.winfo_width()
        canvas_height = self.skin_canvas.winfo_height()
        
        if canvas_width > 10 and canvas_height > 10:
            skin_path = self.find_skin_loadscreen_path(champion_id, skin_id)
            skin_photo, img_width, img_height = self.load_skin_image_with_aspect_ratio(
                skin_path, canvas_width - 20, canvas_height - 20
            )
            
            self.skin_canvas.delete("all")
            x = (canvas_width - img_width) // 2
            y = (canvas_height - img_height) // 2
            self.skin_canvas.create_image(x, y, anchor=tk.NW, image=skin_photo)
            self.skin_canvas.current_photo = skin_photo
        
        if not skin_name or skin_name.lower() == "default":
            champion_name = self.selected_champion[0]
            self.skin_name_label.config(text=champion_name)
        else:
            self.skin_name_label.config(text=skin_name)
        
        self.skin_counter_label.config(text=f"{self.current_skin_index + 1}/{len(self.skins_list)}")

def main():
    root = tk.Tk()
    app = DDSViewer(root)
    root.mainloop()

if __name__ == "__main__":
    main()