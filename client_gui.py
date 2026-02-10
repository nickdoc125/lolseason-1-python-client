import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import websockets
import asyncio
import threading
import json
import random
import string
import subprocess
import os
from history_manager import load_history, add_username_to_history, add_ip_to_history
from config import CHAMPIONS, TEAMS, SUMMONER_SPELLS, SKINS, DEFAULT_SKIN, AI_DIFFICULTY_OPTIONS, DEFAULT_AI_DIFFICULTY, PORT, GAME_MODES, MAPS, DEFAULT_GAME_MODE, DEFAULT_MAP, GAMEINFO_PATH, SERVER_PATH, LEAGUE_PATH, GAME_PORT, BAT_OUTPUT_PATH, RUNES_EDITOR_EXE, RUNES_JSON, GAME_DATA, PLAYER_COUNT_OPTIONS, DEFAULT_PLAYER_COUNT, PLAYER_COUNT_LIMITS
from config import get_champion_id, get_skin_id, get_spell_id, get_game_mode_id, get_map_id
from player_frame import PlayerChampionFrame
try:
    from smart_select import DDSViewer
except ImportError as e:
    print(f"Warning: Could not import DDSViewer: {e}")
    DDSViewer = None

# Χρώματα dark theme
DARK_THEME = {
    'bg_dark': '#1e1e1e',
    'bg_medium': '#2d2d2d', 
    'bg_light': '#3c3c3c',
    'accent': '#007acc',
    'text_primary': '#ffffff',
    'text_secondary': '#cccccc',
    'border': '#555555',
    'hover': '#4a4a4a',
    'selected': '#007acc',
    'success': '#4CAF50',
    'warning': '#FF9800',
    'error': '#f44336'
}

class DarkTheme:
    @staticmethod
    def configure_styles():
        style = ttk.Style()
        
        # Configure theme
        style.theme_use('clam')
        
        # Configure colors
        style.configure('.', 
                       background=DARK_THEME['bg_dark'],
                       foreground=DARK_THEME['text_primary'],
                       fieldbackground=DARK_THEME['bg_light'],
                       selectbackground=DARK_THEME['selected'],
                       selectforeground=DARK_THEME['text_primary'],
                       troughcolor=DARK_THEME['bg_medium'],
                       insertcolor=DARK_THEME['text_primary'])
        
        # Configure specific widgets
        style.configure('TFrame', background=DARK_THEME['bg_dark'])
        style.configure('TLabel', background=DARK_THEME['bg_dark'], foreground=DARK_THEME['text_primary'])
        style.configure('TButton', background=DARK_THEME['bg_medium'], foreground=DARK_THEME['text_primary'])
        
        # Σημαντικό: Combobox styling - ΚΥΡΙΑ ΡΥΘΜΙΣΗ
        style.configure('TCombobox', 
                       fieldbackground=DARK_THEME['bg_light'],
                       background=DARK_THEME['bg_light'],
                       foreground=DARK_THEME['text_primary'],
                       selectbackground=DARK_THEME['selected'],
                       selectforeground=DARK_THEME['text_primary'],
                       arrowcolor=DARK_THEME['text_primary'],
                       bordercolor=DARK_THEME['border'],
                       lightcolor=DARK_THEME['bg_light'],
                       darkcolor=DARK_THEME['bg_light'])
        
        # ΠΟΛΥ ΣΗΜΑΝΤΙΚΟ: Ρύθμιση για το popdown listbox
        style.configure('TCombobox.Listbox',
                       background=DARK_THEME['bg_light'],
                       foreground=DARK_THEME['text_primary'],
                       selectbackground=DARK_THEME['selected'],
                       selectforeground=DARK_THEME['text_primary'],
                       relief='flat',
                       borderwidth=1)
        
        style.configure('TEntry', 
                       fieldbackground=DARK_THEME['bg_light'], 
                       foreground=DARK_THEME['text_primary'],
                       insertcolor=DARK_THEME['text_primary'])
        
        style.configure('TCheckbutton', 
                       background=DARK_THEME['bg_dark'], 
                       foreground=DARK_THEME['text_primary'])
        
        style.configure('TScrollbar', 
                       background=DARK_THEME['bg_medium'], 
                       troughcolor=DARK_THEME['bg_dark'])
        
        # Map states
        style.map('TCombobox',
                 fieldbackground=[('readonly', DARK_THEME['bg_light']),
                                 ('active', DARK_THEME['hover'])],
                 background=[('readonly', DARK_THEME['bg_light']),
                           ('active', DARK_THEME['hover'])],
                 selectbackground=[('readonly', DARK_THEME['selected']),
                                  ('active', DARK_THEME['selected'])])
        
        style.map('TButton',
                 background=[('active', DARK_THEME['hover']),
                           ('pressed', DARK_THEME['selected'])])
class FilterFrame(tk.Frame):
    def __init__(self, parent, callback):
        super().__init__(parent, relief="solid", bd=1, padx=3, pady=3, bg=DARK_THEME['bg_medium'])
        self.callback = callback
        self.parent = parent
        
        # Title
        tk.Label(self, text="Filters", font=("Arial", 9, "bold"), 
                bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 3))
        
        # Condition filters
        self.condition_vars = {
            "w": tk.BooleanVar(value=True),
            "p": tk.BooleanVar(value=True),
            "b": tk.BooleanVar(value=True),
            "di": tk.BooleanVar(value=True)
        }
        
        condition_labels = {
            "w": "Working",
            "p": "Playable", 
            "b": "Bug",
            "di": "Dodge issue"
        }
        
        # Create compact checkboxes with dark theme
        for i, (condition, var) in enumerate(self.condition_vars.items()):
            cb = tk.Checkbutton(self, text=condition_labels[condition], variable=var,
                              command=self.on_filter_change, font=("Arial", 8),
                              bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'],
                              selectcolor=DARK_THEME['bg_dark'],
                              activebackground=DARK_THEME['bg_medium'],
                              activeforeground=DARK_THEME['text_primary'])
            cb.grid(row=1, column=i, sticky="w", padx=1)
    
    def on_filter_change(self):
        if self.callback:
            self.callback()
    
    def get_active_filters(self):
        return [condition for condition, var in self.condition_vars.items() if var.get()]
    
    def set_active_filters(self, active_filters):
        for condition, var in self.condition_vars.items():
            var.set(condition in active_filters)

class GameSettingsFrame(tk.Frame):
    def __init__(self, parent, is_host=False, initial_settings=None, autofill_callback=None):
        super().__init__(parent, relief="solid", bd=1, padx=10, pady=10, bg=DARK_THEME['bg_medium'])
        self.is_host = is_host
        self.autofill_callback = autofill_callback
        self.autobalance_callback = None
        
        if initial_settings is None:
            initial_settings = {
                "game_mode": DEFAULT_GAME_MODE,
                "map": DEFAULT_MAP,
                "player_count": DEFAULT_PLAYER_COUNT,
                "manacosts": True,
                "cooldowns": True,
                "cheats": False,
                "minion_spawns": True
            }
        
        self.settings = initial_settings
        
        # Title
        title_label = tk.Label(self, text="Game Settings", font=("Arial", 10, "bold"),
                              bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'])
        title_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 5))
        
        # Πρώτη γραμμή - Mode, Map και Player Count
        self.mode_frame = tk.Frame(self, bg=DARK_THEME['bg_medium'])
        self.mode_frame.grid(row=1, column=0, sticky="w", padx=(0, 10), pady=2)
        
        tk.Label(self.mode_frame, text="Mode:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).pack(side="left", padx=(0, 5))
        self.game_mode_var = tk.StringVar(value=initial_settings["game_mode"])
        
        if self.is_host and GAME_MODES:
            self.game_mode_combo = ttk.Combobox(self.mode_frame, textvariable=self.game_mode_var, 
                                              values=GAME_MODES, state="readonly", width=14)
            self.game_mode_combo.pack(side="left")
            self.game_mode_combo.bind('<<ComboboxSelected>>', self.on_change)
        else:
            self.game_mode_label = tk.Label(self.mode_frame, text=initial_settings["game_mode"], 
                                          width=14, bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
            self.game_mode_label.pack(side="left")
        
        # Map frame
        self.map_frame = tk.Frame(self, bg=DARK_THEME['bg_medium'])
        self.map_frame.grid(row=1, column=1, sticky="w", padx=(0, 10), pady=2)
        
        tk.Label(self.map_frame, text="Map:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).pack(side="left", padx=(0, 5))
        self.map_var = tk.StringVar(value=initial_settings["map"])
        
        if self.is_host and MAPS:
            self.map_combo = ttk.Combobox(self.map_frame, textvariable=self.map_var, 
                                        values=MAPS, state="readonly", width=14)
            self.map_combo.pack(side="left")
            self.map_combo.bind('<<ComboboxSelected>>', self.on_change)
        else:
            self.map_label = tk.Label(self.map_frame, text=initial_settings["map"], 
                                    width=14, bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
            self.map_label.pack(side="left")
        
        # Player Count frame
        self.player_count_frame = tk.Frame(self, bg=DARK_THEME['bg_medium'])
        self.player_count_frame.grid(row=1, column=2, sticky="w", pady=2)
        
        tk.Label(self.player_count_frame, text="Players:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).pack(side="left", padx=(0, 5))
        self.player_count_var = tk.StringVar(value=initial_settings.get("player_count", DEFAULT_PLAYER_COUNT))
        
        if self.is_host and PLAYER_COUNT_OPTIONS:
            self.player_count_combo = ttk.Combobox(self.player_count_frame, textvariable=self.player_count_var, 
                                                 values=PLAYER_COUNT_OPTIONS, state="readonly", width=10)
            self.player_count_combo.pack(side="left")
            self.player_count_combo.bind('<<ComboboxSelected>>', self.on_change)
        else:
            self.player_count_label = tk.Label(self.player_count_frame, 
                                             text=initial_settings.get("player_count", DEFAULT_PLAYER_COUNT), 
                                             width=10, bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
            self.player_count_label.pack(side="left")
        
        # Δεύτερη γραμμή - Checkbuttons και Buttons μαζί
        self.bottom_frame = tk.Frame(self, bg=DARK_THEME['bg_medium'])
        self.bottom_frame.grid(row=2, column=0, columnspan=4, sticky="ew", pady=1)
        
        # Αριστερά - Checkbuttons
        self.checks_frame = tk.Frame(self.bottom_frame, bg=DARK_THEME['bg_medium'])
        self.checks_frame.pack(side="left", fill="x", expand=True)
        
        self.manacosts_var = tk.BooleanVar(value=initial_settings.get("manacosts", True))
        self.cooldowns_var = tk.BooleanVar(value=initial_settings.get("cooldowns", True))
        self.cheats_var = tk.BooleanVar(value=initial_settings.get("cheats", False))
        self.minion_spawns_var = tk.BooleanVar(value=initial_settings.get("minion_spawns", True))
        
        # Manacosts checkbox
        self.manacosts_cb = tk.Checkbutton(self.checks_frame, text="Manacosts", variable=self.manacosts_var,
                                          command=self.on_change, state="normal" if self.is_host else "disabled",
                                          bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'],
                                          selectcolor=DARK_THEME['bg_dark'])
        self.manacosts_cb.pack(side="left", padx=(0, 10))
        
        # Cooldowns checkbox
        self.cooldowns_cb = tk.Checkbutton(self.checks_frame, text="Cooldowns", variable=self.cooldowns_var,
                                          command=self.on_change, state="normal" if self.is_host else "disabled",
                                          bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'],
                                          selectcolor=DARK_THEME['bg_dark'])
        self.cooldowns_cb.pack(side="left", padx=(0, 10))
        
        # Cheats checkbox
        self.cheats_cb = tk.Checkbutton(self.checks_frame, text="Cheats", variable=self.cheats_var,
                                       command=self.on_change, state="normal" if self.is_host else "disabled",
                                       bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'],
                                       selectcolor=DARK_THEME['bg_dark'])
        self.cheats_cb.pack(side="left", padx=(0, 10))
        
        # Minion Spawns checkbox
        self.minion_spawns_cb = tk.Checkbutton(self.checks_frame, text="Minions", variable=self.minion_spawns_var,
                                              command=self.on_change, state="normal" if self.is_host else "disabled",
                                              bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'],
                                              selectcolor=DARK_THEME['bg_dark'])
        self.minion_spawns_cb.pack(side="left")
        
        # Δεξιά - Buttons
        self.buttons_frame = tk.Frame(self.bottom_frame, bg=DARK_THEME['bg_medium'])
        self.buttons_frame.pack(side="right", padx=(10, 0))
        
        # Autofill Button
        self.autofill_button = tk.Button(self.buttons_frame, text="🤖 AUTOFILL", 
                                       command=self.autofill_bots,
                                       font=("Arial", 8, "bold"),
                                       bg=DARK_THEME['accent'], fg="white",
                                       state="disabled" if not is_host else "normal",
                                       cursor="hand2")
        self.autofill_button.pack(side="left", padx=(0, 5))
        
        # Auto Balance Button
        self.autobalance_button = tk.Button(self.buttons_frame, text="⚖️ AUTO BALANCE", 
                                          command=self.autobalance_teams,
                                          font=("Arial", 8, "bold"),
                                          bg=DARK_THEME['warning'], fg="white",
                                          state="disabled" if not is_host else "normal",
                                          cursor="hand2")
        self.autobalance_button.pack(side="left")
    
    def autofill_bots(self):
        if self.autofill_callback and self.is_host:
            self.autofill_callback()
    
    def autobalance_teams(self):
        if self.autobalance_callback and self.is_host:
            self.autobalance_callback()
    
    def on_change(self, event=None):
        if hasattr(self, 'callback'):
            self.callback()
    
    def set_callback(self, callback):
        self.callback = callback
    
    def set_autobalance_callback(self, callback):
        self.autobalance_callback = callback
    
    def get_settings(self):
        return {
            "game_mode": self.game_mode_var.get(),
            "map": self.map_var.get(),
            "player_count": self.player_count_var.get(),
            "manacosts": self.manacosts_var.get(),
            "cooldowns": self.cooldowns_var.get(),
            "cheats": self.cheats_var.get(),
            "minion_spawns": self.minion_spawns_var.get()
        }
    
    def update_settings(self, new_settings, is_host=False):
        self.is_host = is_host
        self.settings = new_settings
        
        # Ενημέρωση τιμών
        self.game_mode_var.set(new_settings["game_mode"])
        self.map_var.set(new_settings["map"])
        self.player_count_var.set(new_settings.get("player_count", DEFAULT_PLAYER_COUNT))
        self.manacosts_var.set(new_settings.get("manacosts", True))
        self.cooldowns_var.set(new_settings.get("cooldowns", True))
        self.cheats_var.set(new_settings.get("cheats", False))
        self.minion_spawns_var.set(new_settings.get("minion_spawns", True))
        
        # Ενημέρωση UI βάσει host status
        if self.is_host:
            # Mode - μετατροπή από label σε combobox αν χρειάζεται
            if hasattr(self, 'game_mode_label'):
                self.game_mode_label.destroy()
                if hasattr(self, 'game_mode_combo'):
                    self.game_mode_combo.destroy()
                self.game_mode_combo = ttk.Combobox(self.mode_frame, textvariable=self.game_mode_var, 
                                                  values=GAME_MODES, state="readonly", width=14)
                self.game_mode_combo.pack(side="left")
                self.game_mode_combo.bind('<<ComboboxSelected>>', self.on_change)
            
            # Map - μετατροπή από label σε combobox αν χρειάζεται
            if hasattr(self, 'map_label'):
                self.map_label.destroy()
                if hasattr(self, 'map_combo'):
                    self.map_combo.destroy()
                self.map_combo = ttk.Combobox(self.map_frame, textvariable=self.map_var, 
                                            values=MAPS, state="readonly", width=14)
                self.map_combo.pack(side="left")
                self.map_combo.bind('<<ComboboxSelected>>', self.on_change)
            
            # Player Count - μετατροπή από label σε combobox αν χρειάζεται
            if hasattr(self, 'player_count_label'):
                self.player_count_label.destroy()
                if hasattr(self, 'player_count_combo'):
                    self.player_count_combo.destroy()
                self.player_count_combo = ttk.Combobox(self.player_count_frame, textvariable=self.player_count_var, 
                                                     values=PLAYER_COUNT_OPTIONS, state="readonly", width=10)
                self.player_count_combo.pack(side="left")
                self.player_count_combo.bind('<<ComboboxSelected>>', self.on_change)
            
            # Ενεργοποίηση checkboxes
            self.manacosts_cb.config(state="normal")
            self.cooldowns_cb.config(state="normal")
            self.cheats_cb.config(state="normal")
            self.minion_spawns_cb.config(state="normal")
            
            # Ενημέρωση autofill button
            player_count = new_settings.get("player_count", DEFAULT_PLAYER_COUNT)
            if player_count in ["1v1", "2v2", "3v3", "4v4", "5v5", "6v6"]:
                self.autofill_button.config(state="normal", bg=DARK_THEME['accent'])
            else:
                self.autofill_button.config(state="disabled", bg=DARK_THEME['bg_light'])
            
            # Ενημέρωση autobalance button
            self.autobalance_button.config(state="normal", bg=DARK_THEME['warning'])
        else:
            # Mode - μετατροπή από combobox σε label αν χρειάζεται
            if hasattr(self, 'game_mode_combo'):
                self.game_mode_combo.destroy()
                if hasattr(self, 'game_mode_label'):
                    self.game_mode_label.destroy()
                current_mode = self.game_mode_var.get()
                self.game_mode_label = tk.Label(self.mode_frame, text=current_mode, 
                                              width=14, bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
                self.game_mode_label.pack(side="left")
            
            # Map - μετατροπή από combobox σε label αν χρειάζεται
            if hasattr(self, 'map_combo'):
                self.map_combo.destroy()
                if hasattr(self, 'map_label'):
                    self.map_label.destroy()
                current_map = self.map_var.get()
                self.map_label = tk.Label(self.map_frame, text=current_map, 
                                        width=14, bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
                self.map_label.pack(side="left")
            
            # Player Count - μετατροπή από combobox σε label αν χρειάζεται
            if hasattr(self, 'player_count_combo'):
                self.player_count_combo.destroy()
                if hasattr(self, 'player_count_label'):
                    self.player_count_label.destroy()
                current_count = self.player_count_var.get()
                self.player_count_label = tk.Label(self.player_count_frame, text=current_count, 
                                                 width=10, bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
                self.player_count_label.pack(side="left")
            
            # Απενεργοποίηση checkboxes
            self.manacosts_cb.config(state="disabled")
            self.cooldowns_cb.config(state="disabled")
            self.cheats_cb.config(state="disabled")
            self.minion_spawns_cb.config(state="disabled")
            
            # Απενεργοποίηση autofill button
            self.autofill_button.config(state="disabled", bg=DARK_THEME['bg_light'])
            
            # Απενεργοποίηση autobalance button
            self.autobalance_button.config(state="disabled", bg=DARK_THEME['bg_light'])

class LobbyClient:
    def __init__(self, root, host_ip):
        self.root = root
        self.root.title("Game Lobby - Champion Select")
        self.root.geometry("1100x680")
        self.root.configure(bg=DARK_THEME['bg_dark'])
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ ΤΟΥ LOBBY ΠΑΡΑΘΥΡΟΥ
        self.center_window(self.root)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure dark theme
        DarkTheme.configure_styles()
        
        self.websocket = None
        self.player_frames = {}
        self.is_host = False
        self.game_settings = {
            "game_mode": DEFAULT_GAME_MODE,
            "map": DEFAULT_MAP,
            "player_count": DEFAULT_PLAYER_COUNT,
            "manacosts": True,
            "cooldowns": True,
            "cheats": False,
            "minion_spawns": True
        }
        self.host_ip = host_ip
        self.loop = asyncio.new_event_loop()
        
        # Νέα μεταβλητή για expanded state
        self.is_expanded = False
        
        # Φίλτρα
        self.active_filters = ["w", "p", "b", "di"]
        self.filtered_champions = self.get_filtered_champions()
        self.filtered_spells = self.get_filtered_spells()

        # Two-way sync protection flags
        self._syncing_to_smart_select = False
        self._syncing_from_smart_select = False

        # Προσθήκη IP στο history
        add_ip_to_history(host_ip)

        # Φόρτωση history usernames
        history = load_history()
        
        # Δημιουργία παραθύρου για username με history
        self.name = self.ask_username_with_history(history["usernames"])
        if not self.name:
            self.root.destroy()
            return

        # Προσθήκη του νέου username στο history
        add_username_to_history(self.name)

        # Φόρτωση των runes και talents του παίκτη
        self.player_runes, self.player_talents = self.load_player_runes_and_talents()

        # Main frame
        main_frame = tk.Frame(root, bg=DARK_THEME['bg_dark'])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top frame for player champion selects and game settings
        top_frame = tk.Frame(main_frame, bg=DARK_THEME['bg_dark'])
        top_frame.pack(fill="x", pady=(0, 10))
        
        title_text = "Champion Select - All Players"
        self.title_label = tk.Label(top_frame, text=title_text, 
                                   font=("Arial", 14, "bold"),
                                   bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary'])
        self.title_label.pack(pady=(0, 10))
        
        # Main settings and filters container
        settings_filters_frame = tk.Frame(top_frame, bg=DARK_THEME['bg_dark'])
        settings_filters_frame.pack(fill="x", pady=5)
        
        # Left side - Game Settings
        self.game_settings_frame = GameSettingsFrame(settings_filters_frame, 
                                                   is_host=False, 
                                                   initial_settings=self.game_settings,
                                                   autofill_callback=self.autofill_bots)
        self.game_settings_frame.pack(side="left", padx=(0, 10))
        self.game_settings_frame.set_callback(self.send_game_settings_update)
        self.game_settings_frame.set_autobalance_callback(self.autobalance_teams)
        
        # Right side - Filters (μικρότερο)
        filters_container = tk.Frame(settings_filters_frame, bg=DARK_THEME['bg_dark'])
        filters_container.pack(side="right", fill="y")
        
        # Filters Frame (μικρότερο)
        self.filter_frame = FilterFrame(filters_container, self.on_filter_change)
        self.filter_frame.pack(fill="x", pady=0)
        
        # Buttons frame για Smart Select, Add Bot και Expand/Collapse
        buttons_frame = tk.Frame(filters_container, bg=DARK_THEME['bg_dark'])
        buttons_frame.pack(fill="x", pady=(5, 0))
        
        # Smart Select button (νέο κουμπί)
        self.smart_select_button = tk.Button(buttons_frame, text="🎯 Smart Select", 
                                           command=self.open_smart_select,
                                           bg=DARK_THEME['accent'], fg="white", font=("Arial", 9, "bold"),
                                           height=1, width=12, cursor="hand2")
        self.smart_select_button.pack(side="left", padx=(0, 2), fill="x", expand=True)
        
        # Add Bot button (μισό πλάτος) - ΑΡΧΙΚΗ ΚΑΤΑΣΤΑΣΗ
        self.add_bot_button = tk.Button(buttons_frame, text="➕ Add Bot", 
                                      command=self.show_add_bot_dialog,
                                      bg=DARK_THEME['success'], fg="white", font=("Arial", 9, "bold"),
                                      height=1, width=12, cursor="hand2")
        self.add_bot_button.pack(side="left", padx=(0, 2), fill="x", expand=True)
        
        # Expand/Collapse button (μισό πλάτος)
        self.expand_button = tk.Button(buttons_frame, text="⬇ Expand", 
                                     command=self.toggle_expand,
                                     bg=DARK_THEME['accent'], fg="white", font=("Arial", 9, "bold"),
                                     height=1, width=8, cursor="hand2")
        self.expand_button.pack(side="right", padx=(2, 0), fill="x", expand=True)
        
        # Container for player frames with horizontal scroll
        players_frame_container = tk.Frame(top_frame, bg=DARK_THEME['bg_dark'])
        players_frame_container.pack(fill="x", expand=True)
        
        # Create horizontal scrollbar - ΛΕΠΤΟ scrollbar
        self.h_scrollbar = tk.Scrollbar(players_frame_container, orient="horizontal", width=8,
                                       bg=DARK_THEME['bg_medium'], troughcolor=DARK_THEME['bg_dark'])
        self.h_scrollbar.pack(side="bottom", fill="x")
        
        # Create canvas for scrolling
        self.canvas = tk.Canvas(players_frame_container, 
                               xscrollcommand=self.h_scrollbar.set,
                               height=185, highlightthickness=0,
                               bg=DARK_THEME['bg_medium'])
        self.canvas.pack(side="top", fill="x", expand=True)
        
        # Configure scrollbar
        self.h_scrollbar.config(command=self.canvas.xview)
        
        # Create frame inside canvas for player frames
        self.players_container = tk.Frame(self.canvas, bg=DARK_THEME['bg_medium'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.players_container, anchor="nw")
        
        # Bind events for scrolling and resize
        self.players_container.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Αρχικά κρύβουμε το scrollbar
        self.h_scrollbar.pack_forget()
        
        # Bottom frame for chat and ready button
        bottom_frame = tk.Frame(main_frame, bg=DARK_THEME['bg_dark'])
        bottom_frame.pack(fill="both", expand=True)
        
        # Left side - Chat
        chat_frame = tk.Frame(bottom_frame, bg=DARK_THEME['bg_dark'])
        chat_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        tk.Label(chat_frame, text="Chat:", font=("Arial", 10, "bold"),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w")
        
        self.chat_text = tk.Text(chat_frame, state="disabled", width=50, height=10,
                               bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'],
                               insertbackground=DARK_THEME['text_primary'])
        self.chat_text.pack(fill="both", expand=True, pady=5)
        
        # Chat input
        chat_input_frame = tk.Frame(chat_frame, bg=DARK_THEME['bg_dark'])
        chat_input_frame.pack(fill="x", pady=5)
        
        self.chat_entry = tk.Entry(chat_input_frame, width=40,
                                 bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'],
                                 insertbackground=DARK_THEME['text_primary'])
        self.chat_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.chat_entry.bind("<Return>", lambda e: self.send_chat())
        
        self.chat_button = tk.Button(chat_input_frame, text="Send", command=self.send_chat,
                                   bg=DARK_THEME['accent'], fg="white", cursor="hand2")
        self.chat_button.pack(side="left")
        
        # Right side - Ready button and info
        right_frame = tk.Frame(bottom_frame, bg=DARK_THEME['bg_dark'])
        right_frame.pack(side="right", fill="y")
        
        # Runes Editor button
        self.runes_button = tk.Button(right_frame, text="🧿 RUNES EDITOR", 
                                    command=self.open_runes_editor,
                                    font=("Arial", 10, "bold"),
                                    bg=DARK_THEME['bg_medium'], fg="white",
                                    width=15, height=2, cursor="hand2")
        self.runes_button.pack(pady=5)
        
        # Ready button
        self.ready_var = tk.BooleanVar()
        self.ready_button = tk.Checkbutton(right_frame, text="READY", 
                                         variable=self.ready_var, 
                                         command=self.send_ready, 
                                         font=("Arial", 12, "bold"),
                                         indicatoron=True,
                                         width=15,
                                         height=3,
                                         bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary'],
                                         selectcolor=DARK_THEME['accent'],
                                         activebackground=DARK_THEME['bg_dark'],
                                         activeforeground=DARK_THEME['text_primary'])
        self.ready_button.pack(pady=10)
        
        # Start Game button (μόνο για host)
        self.start_game_button = tk.Button(right_frame, text="START GAME", 
                                         command=self.start_game,
                                         font=("Arial", 12, "bold"),
                                         bg=DARK_THEME['bg_light'], fg="white",
                                         width=15, height=3,
                                         state="disabled", cursor="hand2")
        self.start_game_button.pack(pady=10)
        
        # Reconnect button (για όλους)
        self.reconnect_button = tk.Button(right_frame, text="🔄 RECONNECT", 
                                        command=self.reconnect_game,
                                        font=("Arial", 10, "bold"),
                                        bg=DARK_THEME['accent'], fg="white",
                                        width=15, height=2, cursor="hand2")
        self.reconnect_button.pack(pady=5)

        # Σύνδεση με WebSocket server
        threading.Thread(target=self.connect_websocket, daemon=True).start()

    def center_window(self, window):
        """Κεντράρισμα παραθύρου στην οθόνη"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def on_filter_change(self):
        """Χειρισμός αλλαγής filters από το Lobby UI"""
        new_filters = self.filter_frame.get_active_filters()
        
        # Έλεγχος αν πραγματικά άλλαξαν τα filters
        if new_filters == self.active_filters:
            return
        
        self.active_filters = new_filters
        self.filtered_champions = self.get_filtered_champions()
        self.filtered_spells = self.get_filtered_spells()
        
        print(f"DEBUG: Lobby filters changed to: {self.active_filters}")
        
        # Ενημέρωση player frames
        for player_name, frame in self.player_frames.items():
            if (frame.is_own_player and not frame.player_data["ready"]) or (self.is_host and frame.is_bot):
                if hasattr(frame, 'champion_combo'):
                    frame.champion_combo['values'] = self.filtered_champions
                    current_champ = frame.champion_var.get()
                    if current_champ not in self.filtered_champions and self.filtered_spells:
                        frame.champion_var.set(self.filtered_champions[0])
                        frame.on_champion_change()
                
                if hasattr(frame, 'spell1_combo'):
                    frame.spell1_combo['values'] = self.filtered_spells
                    current_spell1 = frame.spell1_var.get()
                    if current_spell1 not in self.filtered_spells and self.filtered_spells:
                        frame.spell1_var.set(self.filtered_spells[0])
                
                if hasattr(frame, 'spell2_combo'):
                    frame.spell2_combo['values'] = self.filtered_spells
                    current_spell2 = frame.spell2_var.get()
                    if current_spell2 not in self.filtered_spells and self.filtered_spells:
                        frame.spell2_var.set(self.filtered_spells[0])
        
        # ΣΥΓΧΡΟΝΙΣΜΟΣ ΠΡΟΣ Smart Select - two way sync
        self.sync_filters_to_smart_select()

    def sync_filters_to_smart_select(self):
        """Συγχρονισμός filters από Lobby προς Smart Select"""
        if not hasattr(self, 'smart_select_app') or not self.smart_select_app:
            return
        
        # Protection από loops
        if getattr(self, '_syncing_to_smart_select', False):
            return
        
        self._syncing_to_smart_select = True
        
        try:
            if hasattr(self.smart_select_app, 'update_filters_from_external'):
                print(f"DEBUG: Syncing filters TO Smart Select: {self.active_filters}")
                self.smart_select_app.update_filters_from_external(self.active_filters)
        except Exception as e:
            print(f"Error syncing filters to Smart Select: {e}")
        finally:
            self.root.after(100, lambda: setattr(self, '_syncing_to_smart_select', False))

    def sync_filters_from_smart_select(self, new_filters):
        """Συγχρονισμός filters από Smart Select προς Lobby"""
        # Protection από loops
        if getattr(self, '_syncing_from_smart_select', False):
            return
        
        self._syncing_from_smart_select = True
        
        try:
            # Έλεγχος αν πραγματικά άλλαξαν τα filters
            if new_filters == self.active_filters:
                return
            
            print(f"DEBUG: Syncing filters FROM Smart Select: {new_filters}")
            
            self.active_filters = new_filters
            self.filtered_champions = self.get_filtered_champions()
            self.filtered_spells = self.get_filtered_spells()
            
            # Ενημέρωση Filter Frame UI
            for condition, var in self.filter_frame.condition_vars.items():
                # Προσωρινά απενεργοποιούμε το callback για να μην προκληθεί loop
                var.set(condition in new_filters)
            
            # Ενημέρωση player frames
            for player_name, frame in self.player_frames.items():
                if (frame.is_own_player and not frame.player_data["ready"]) or (self.is_host and frame.is_bot):
                    if hasattr(frame, 'champion_combo'):
                        frame.champion_combo['values'] = self.filtered_champions
                        current_champ = frame.champion_var.get()
                        if current_champ not in self.filtered_champions and self.filtered_champions:
                            frame.champion_var.set(self.filtered_champions[0])
                            frame.on_champion_change()
                    
                    if hasattr(frame, 'spell1_combo'):
                        frame.spell1_combo['values'] = self.filtered_spells
                        current_spell1 = frame.spell1_var.get()
                        if current_spell1 not in self.filtered_spells and self.filtered_spells:
                            frame.spell1_var.set(self.filtered_spells[0])
                    
                    if hasattr(frame, 'spell2_combo'):
                        frame.spell2_combo['values'] = self.filtered_spells
                        current_spell2 = frame.spell2_var.get()
                        if current_spell2 not in self.filtered_spells and self.filtered_spells:
                            frame.spell2_var.set(self.filtered_spells[0])
                            
        except Exception as e:
            print(f"Error syncing filters from Smart Select: {e}")
        finally:
            self.root.after(100, lambda: setattr(self, '_syncing_from_smart_select', False))

    def open_smart_select(self):
        """Ανοίγει το Smart Select με βελτιωμένο συγχρονισμό"""
        try:
            # Close existing instance if any
            if hasattr(self, 'smart_select_app') and self.smart_select_app:
                try:
                    self.smart_select_app.root.destroy()
                except:
                    pass
                del self.smart_select_app
            
            # Create window with slight delay to ensure proper initialization
            self.root.after(100, self._create_smart_select_window)
            
        except Exception as e:
            error_msg = f"Failed to open Smart Select: {str(e)}"
            messagebox.showerror("Smart Select Error", error_msg, parent=self.root)

    def _create_smart_select_window(self):
        """Δημιουργία παραθύρου Smart Select με καθυστέρηση για σταθεροποίηση"""
        smart_win = tk.Toplevel(self.root)
        smart_win.title("Smart Select")
        smart_win.geometry("1050x720")
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ SMART SELECT ΠΑΡΑΘΥΡΟΥ
        self.center_window(smart_win)
        
        # ΠΡΟΣΘΗΚΗ: Ορισμός ως transient του κύριου παραθύρου
        smart_win.transient(self.root)
        
        # Prepare initial data with current player state
        initial_data = self._get_current_player_state()
        
        # Create Smart Select with delayed callback binding
        self.smart_select_app = DDSViewer(
            smart_win, 
            sync_callback=self.handle_smart_select_sync,
            initial_data=initial_data,
            update_callback=self.update_smart_select_from_lobby
        )
        
        # Bind close event
        smart_win.protocol("WM_DELETE_WINDOW", lambda: self.on_smart_select_close(smart_win))
        
        # Final sync after window is fully initialized
        self.root.after(200, lambda: self.smart_select_app.sync_from_lobby(initial_data))
        
        self.add_chat(f"SYSTEM: 🎯 Smart Select opened - fully synchronized with lobby")

    def _get_current_player_state(self):
        """Βρίσκει τα τρέχοντα δεδομένα του παίκτη"""
        initial_data = {
            'active_filters': self.active_filters,
            'champion': '',
            'spells': ['', ''],
            'skin': 'Classic'
        }
        
        if self.name in self.player_frames:
            player_frame = self.player_frames[self.name]
            selection = player_frame.get_selection()
            initial_data.update({
                'champion': selection["champion"],
                'spells': [selection["spell1"], selection["spell2"]],
                'skin': selection["skin"]
            })
        
        return initial_data

    def update_smart_select_from_lobby(self, data_type=None):
        """Ενημερώνει το Smart Select με προστασία από loops"""
        if not hasattr(self, 'smart_select_app') or not self.smart_select_app:
            return
        
        # Additional protection
        if getattr(self, '_updating_smart_select', False):
            return
            
        self._updating_smart_select = True
        
        try:
            # Βρίσκουμε τα τρέχοντα δεδομένα του παίκτη
            if self.name in self.player_frames:
                player_frame = self.player_frames[self.name]
                selection = player_frame.get_selection()
                
                # Ενημέρωση μόνο για τον συγκεκριμένο τύπο δεδομένων ή για όλα
                if data_type is None or data_type == "all":
                    # Στέλνουμε όλα τα δεδομένα
                    update_data = {
                        'champion': selection["champion"],
                        'spells': [selection["spell1"], selection["spell2"]],
                        'skin': selection["skin"],
                        'active_filters': self.active_filters
                    }
                    if hasattr(self.smart_select_app, 'sync_from_lobby'):
                        self.smart_select_app.sync_from_lobby(update_data)
                
                elif data_type == "champion":
                    if hasattr(self.smart_select_app, 'select_champion_from_external'):
                        self.smart_select_app.select_champion_from_external(selection["champion"])
                
                elif data_type == "spells":
                    if hasattr(self.smart_select_app, 'update_spells_from_external'):
                        self.smart_select_app.update_spells_from_external([
                            selection["spell1"], 
                            selection["spell2"]
                        ])
                
                elif data_type == "skin":
                    if hasattr(self.smart_select_app, 'update_skin_from_external'):
                        self.smart_select_app.update_skin_from_external(selection["skin"])
                
                elif data_type == "filters":
                    if hasattr(self.smart_select_app, 'update_filters_from_external'):
                        self.smart_select_app.update_filters_from_external(self.active_filters)
                    
        except Exception as e:
            print(f"Error updating Smart Select from lobby: {e}")
        finally:
            self.root.after(50, lambda: setattr(self, '_updating_smart_select', False))

    def on_smart_select_close(self, window):
        """Χειρίζεται το κλείσιμο του Smart Select παραθύρου"""
        print("DEBUG: Closing Smart Select window")
        if hasattr(self, 'smart_select_app'):
            del self.smart_select_app
        window.destroy()

    def handle_smart_select_sync(self, sync_data):
        """Χειρίζεται συγχρονισμό δεδομένων από το Smart Select"""
        print(f"DEBUG: Smart Select sync received - Type: {sync_data.get('type')}")
        
        if sync_data["type"] == "filters":
            # Συγχρονισμός filters από Smart Select προς Lobby
            self.sync_filters_from_smart_select(sync_data["filters"])
            
        elif sync_data["type"] == "champion":
            # Συγχρονισμός champion
            if self.name in self.player_frames and not self.player_frames[self.name].player_data["ready"]:
                frame = self.player_frames[self.name]
                frame.champion_var.set(sync_data["champion"])
                frame.on_champion_change()
                self.send_player_update()
                
        elif sync_data["type"] == "spell":
            # Συγχρονισμός spell
            if self.name in self.player_frames and not self.player_frames[self.name].player_data["ready"]:
                frame = self.player_frames[self.name]
                if sync_data["slot"] == 0:
                    frame.spell1_var.set(sync_data["spell"])
                else:
                    frame.spell2_var.set(sync_data["spell"])
                frame.on_change()
                self.send_player_update()
                
        elif sync_data["type"] == "skin":
            # Συγχρονισμός skin
            if (self.name in self.player_frames and not self.player_frames[self.name].player_data["ready"] and
                self.player_frames[self.name].champion_var.get() == sync_data["champion"]):
                frame = self.player_frames[self.name]
                frame.skin_var.set(sync_data["skin"])
                frame.on_change()
                self.send_player_update()

    def get_current_player_limit(self):
        player_count_setting = self.game_settings.get("player_count", "5v5")
        return PLAYER_COUNT_LIMITS.get(player_count_setting, 10)

    def get_current_player_count(self):
        if hasattr(self, 'last_players_list'):
            return len(self.last_players_list)
        return 0

    def can_add_more_players(self):
        current_limit = self.get_current_player_limit()
        if current_limit == 0:
            return True
        
        current_count = self.get_current_player_count()
        return current_count < current_limit

    def update_add_bot_button(self):
        current_limit = self.get_current_player_limit()
        current_count = self.get_current_player_count()
        
        if not self.is_host:
            self.add_bot_button.config(
                state="disabled",
                text="➕ Add Bot",
                bg="gray"
            )
        elif current_limit == 0:
            self.add_bot_button.config(
                state="normal",
                text="➕ Add Bot",
                bg=DARK_THEME['success']
            )
        elif current_count < current_limit:
            remaining = current_limit - current_count
            self.add_bot_button.config(
                state="normal",
                text=f"➕ Add Bot ({remaining})",
                bg=DARK_THEME['success']
            )
        else:
            self.add_bot_button.config(
                state="disabled",
                text=f"❌ Limit: {current_limit}",
                bg="gray"
            )

    def update_player_limit_display(self):
        current_limit = self.get_current_player_limit()
        current_count = self.get_current_player_count()
        
        if current_limit > 0:
            if current_count >= current_limit:
                self.add_chat(f"SYSTEM: ⚠️ Player limit reached: {current_count}/{current_limit}")
            elif current_count == current_limit - 1:
                self.add_chat(f"SYSTEM: ℹ️ Only 1 slot remaining ({current_count}/{current_limit})")
            else:
                remaining = current_limit - current_count
                if remaining <= 3:
                    self.add_chat(f"SYSTEM: ℹ️ {remaining} slots remaining ({current_count}/{current_limit})")

    def send_bot_update(self, bot_name):
        if self.is_host and bot_name in self.player_frames:
            frame = self.player_frames[bot_name]
            if frame.is_bot:
                selection = frame.get_selection()
                self.send({
                    "type": "update_bot",
                    "bot_name": bot_name,
                    "bot_data": selection
                })

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.expand_button.config(text="⬆ Collapse", bg=DARK_THEME['warning'])
            self.canvas.config(height=370)
        else:
            self.expand_button.config(text="⬇ Expand", bg=DARK_THEME['accent'])
            self.canvas.config(height=185)
        
        if hasattr(self, 'last_players_list'):
            self.update_lobby_display(self.last_players_list)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.canvas.itemconfig(self.canvas_window, width=self.players_container.winfo_reqwidth())
        self._check_scrollbar_needed()

    def _on_canvas_configure(self, event=None):
        if self.players_container.winfo_reqwidth() > event.width:
            self.canvas.itemconfig(self.canvas_window, width=self.players_container.winfo_reqwidth())
        else:
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self._check_scrollbar_needed()

    def _check_scrollbar_needed(self):
        try:
            if self.players_container.winfo_reqwidth() > self.canvas.winfo_width():
                if not self.h_scrollbar.winfo_ismapped():
                    self.h_scrollbar.pack(side="bottom", fill="x")
            else:
                if self.h_scrollbar.winfo_ismapped():
                    self.h_scrollbar.pack_forget()
        except:
            pass

    def _update_scroll_region(self):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._check_scrollbar_needed()

    def get_filtered_champions(self):
        filtered = []
        champions_data = GAME_DATA.get("champions", {})
        
        for champ_name, champ_data in champions_data.items():
            condition = champ_data.get("condition", "w")
            if condition in self.active_filters:
                filtered.append(champ_name)
        
        return sorted(filtered)

    def get_filtered_spells(self):
        filtered = []
        spells_data = GAME_DATA.get("spells", {})
        
        for spell_name, spell_data in spells_data.items():
            condition = spell_data.get("condition", "w")
            if condition in self.active_filters:
                filtered.append(spell_name)
        
        return sorted(filtered)

    def load_player_runes_and_talents(self):
        try:
            if os.path.exists(RUNES_JSON):
                with open(RUNES_JSON, 'r', encoding='utf-8') as f:
                    runes_data = json.load(f)
            
                if isinstance(runes_data, dict):
                    runes = runes_data.get("runes", {})
                    talents = runes_data.get("talents", {})
                    
                    if not runes:
                        runes = self.generate_default_runes()
                    if not talents:
                        talents = self.generate_default_talents()
                        
                    return runes, talents
                    
        except Exception as e:
            print(f"Error loading player runes and talents: {e}")
        
        return self.generate_default_runes(), self.generate_default_talents()

    def generate_default_runes(self):
        runes = {}
        for i in range(1, 31):
            runes[str(i)] = 5260
        return runes

    def generate_default_talents(self):
        talents = {}
        talent_ids = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 
                      114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 
                      129, 130, 131, 132, 133, 134, 135, 136, 137, 140, 143, 144, 145, 146, 147]
        
        for talent_id in talent_ids:
            talents[str(talent_id)] = 0
        
        talents["102"] = 4
        talents["116"] = 4
        talents["118"] = 3
        talents["119"] = 3
        talents["120"] = 1
        talents["121"] = 4
        talents["122"] = 1
        talents["126"] = 1
        talents["132"] = 1
        talents["134"] = 3
        talents["136"] = 2
        talents["140"] = 1
        
        return talents

    def send_runes_update(self):
        self.player_runes, self.player_talents = self.load_player_runes_and_talents()
        self.send({
            "type": "update_runes",
            "runes": self.player_runes,
            "talents": self.player_talents
        })

    def autobalance_teams(self):
        """Αυτόματη εξισορρόπηση με ίδιο αριθμό μελών και ίδια αναλογία παικτών/bots"""
        if not self.is_host:
            return
        
        if not hasattr(self, 'last_players_list') or not self.last_players_list:
            messagebox.showinfo("Auto Balance", "No players in the lobby to balance.", parent=self.root)
            return
        
        # Κατηγοριοποίηση παικτών
        blue_players = []
        blue_bots = []
        purple_players = []
        purple_bots = []
        
        for player in self.last_players_list:
            if player["team"] == "BLUE":
                if player.get("is_bot", False):
                    blue_bots.append(player)
                else:
                    blue_players.append(player)
            else:
                if player.get("is_bot", False):
                    purple_bots.append(player)
                else:
                    purple_players.append(player)
        
        # Στατιστικά πριν από εξισορρόπηση
        total_blue = len(blue_players) + len(blue_bots)
        total_purple = len(purple_players) + len(purple_bots)
        
        print(f"DEBUG - Before balance:")
        print(f"  BLUE: {len(blue_players)} players, {len(blue_bots)} bots (total: {total_blue})")
        print(f"  PURPLE: {len(purple_players)} players, {len(purple_bots)} bots (total: {total_purple})")
        
        # Έλεγχος αν χρειάζεται εξισορρόπηση
        needs_balance = self._needs_balance(blue_players, blue_bots, purple_players, purple_bots)
        
        if not needs_balance:
            messagebox.showinfo("Auto Balance", "Teams are already perfectly balanced!", parent=self.root)
            return
        
        # Εφαρμογή εξισορρόπησης
        changes_made = self._apply_smart_balance(blue_players, blue_bots, purple_players, purple_bots)
        
        if changes_made > 0:
            self.add_chat(f"SYSTEM: ⚖️ Teams perfectly balanced - {changes_made} changes made")
            
            # Εμφάνιση νέων στατιστικών
            new_blue_players = len([p for p in self.last_players_list if p["team"] == "BLUE" and not p.get("is_bot", False)])
            new_blue_bots = len([p for p in self.last_players_list if p["team"] == "BLUE" and p.get("is_bot", False)])
            new_purple_players = len([p for p in self.last_players_list if p["team"] == "PURPLE" and not p.get("is_bot", False)])
            new_purple_bots = len([p for p in self.last_players_list if p["team"] == "PURPLE" and p.get("is_bot", False)])
            
            messagebox.showinfo("Auto Balance", 
                              f"Teams perfectly balanced!\n\n"
                              f"BLUE: {new_blue_players} players + {new_blue_bots} bots\n"
                              f"PURPLE: {new_purple_players} players + {new_purple_bots} bots\n\n"
                              f"{changes_made} changes applied", parent=self.root)
        else:
            messagebox.showinfo("Auto Balance", "No changes needed - teams are perfectly balanced!", parent=self.root)

    def _needs_balance(self, blue_players, blue_bots, purple_players, purple_bots):
        total_blue = len(blue_players) + len(blue_bots)
        total_purple = len(purple_players) + len(purple_bots)
        
        # Έλεγχος 1: Ίσος αριθμό μελών (ή διαφορά 1 για περιττό σύνολο)
        if abs(total_blue - total_purple) > 1:
            return True
        
        # Έλεγχος 2: Ίδια αναλογία παικτών/bots (όσο το δυνατόν πιο κοντά)
        player_diff = abs(len(blue_players) - len(purple_players))
        bot_diff = abs(len(blue_bots) - len(purple_bots))
        
        if player_diff > 1 or bot_diff > 1:
            return True
        
        return False

    def _apply_smart_balance(self, blue_players, blue_bots, purple_players, purple_bots):
        changes_made = 0
        
        total_players = len(blue_players) + len(purple_players)
        total_bots = len(blue_bots) + len(purple_bots)
        
        # Βρίσκουμε την καλύτερη δυνατή κατανομή
        best_config = self._find_best_balance(total_players, total_bots)
        
        target_blue_players = best_config["blue_players"]
        target_blue_bots = best_config["blue_bots"] 
        target_purple_players = best_config["purple_players"]
        target_purple_bots = best_config["purple_bots"]
        
        print(f"DEBUG - Best balance configuration:")
        print(f"  BLUE: {target_blue_players} players + {target_blue_bots} bots")
        print(f"  PURPLE: {target_purple_players} players + {target_purple_bots} bots")
        
        # Εφαρμογή εξισορρόπησης
        player_changes = self._balance_to_target(blue_players, purple_players, 
                                               target_blue_players, "player")
        changes_made += player_changes
        
        bot_changes = self._balance_to_target(blue_bots, purple_bots,
                                            target_blue_bots, "bot")
        changes_made += bot_changes
        
        return changes_made

    def _find_best_balance(self, total_players, total_bots):
        total_members = total_players + total_bots
        target_total = total_members // 2
        
        possible_configs = []
        
        for blue_players in range(max(0, total_players - target_total), min(total_players, target_total) + 1):
            blue_bots_needed = target_total - blue_players
            
            if 0 <= blue_bots_needed <= total_bots:
                purple_players = total_players - blue_players
                purple_bots = total_bots - blue_bots_needed
                
                player_diff = abs(blue_players - purple_players)
                bot_diff = abs(blue_bots_needed - purple_bots)
                total_diff = abs((blue_players + blue_bots_needed) - (purple_players + purple_bots))
                
                score = total_diff * 100 + player_diff * 10 + bot_diff
                
                possible_configs.append({
                    "blue_players": blue_players,
                    "blue_bots": blue_bots_needed, 
                    "purple_players": purple_players,
                    "purple_bots": purple_bots,
                    "score": score
                })
        
        if possible_configs:
            best_config = min(possible_configs, key=lambda x: x["score"])
        else:
            best_config = {
                "blue_players": total_players // 2,
                "blue_bots": total_bots // 2,
                "purple_players": total_players - (total_players // 2),
                "purple_bots": total_bots - (total_bots // 2),
                "score": 0
            }
        
        return best_config

    def _balance_to_target(self, blue_list, purple_list, target_blue, entity_type):
        changes_made = 0
        current_blue = len(blue_list)
        current_purple = len(purple_list)
        
        print(f"DEBUG - Balancing {entity_type}:")
        print(f"  Current: Blue={current_blue}, Purple={current_purple}")
        print(f"  Target: Blue={target_blue}")
        
        blue_diff = target_blue - current_blue
        
        if blue_diff > 0:
            entities_to_move = min(blue_diff, current_purple)
            entities_from_purple = purple_list[:entities_to_move]
            
            for entity in entities_from_purple:
                self.send({
                    "type": "move_player",
                    "player_name": entity["name"],
                    "new_team": "BLUE"
                })
            changes_made += entities_to_move
            print(f"  Moving {entities_to_move} {entity_type}(s) from PURPLE to BLUE")
        
        elif blue_diff < 0:
            entities_to_move = min(abs(blue_diff), current_blue)
            entities_from_blue = blue_list[:entities_to_move]
            
            for entity in entities_from_blue:
                self.send({
                    "type": "move_player", 
                    "player_name": entity["name"],
                    "new_team": "PURPLE"
                })
            changes_made += entities_to_move
            print(f"  Moving {entities_to_move} {entity_type}(s) from BLUE to PURPLE")
        
        return changes_made

    def autofill_bots(self):
        if not self.is_host:
            return
        
        player_count_setting = self.game_settings.get("player_count", "5v5")
        
        if player_count_setting not in ["1v1", "2v2", "3v3", "4v4", "5v5", "6v6"]:
            messagebox.showinfo("Autofill", "Autofill is only available for 1v1 to 6v6 game modes.", parent=self.root)
            return
        
        players_per_team = int(player_count_setting[0])
        total_required_players = players_per_team * 2
        
        current_players = self.get_current_player_count()
        
        if current_players >= total_required_players:
            messagebox.showinfo("Autofill", f"Lobby is already full! ({current_players}/{total_required_players} players)", parent=self.root)
            return
        
        blue_players = 0
        purple_players = 0
        
        if hasattr(self, 'last_players_list'):
            for player in self.last_players_list:
                if player["team"] == "BLUE":
                    blue_players += 1
                else:
                    purple_players += 1
        
        bots_added = 0
        for team in ["BLUE", "PURPLE"]:
            current_team_players = blue_players if team == "BLUE" else purple_players
            bots_needed = players_per_team - current_team_players
            
            for i in range(bots_needed):
                if current_players >= total_required_players:
                    break
                
                while True:
                    bot_name = f"Bot_{random.randint(1000, 9999)}"
                    if not any(p["name"] == bot_name for p in self.last_players_list):
                        break
                
                champion = random.choice(self.filtered_champions) if self.filtered_champions else ""
                skin = random.choice(SKINS) if SKINS else DEFAULT_SKIN
                difficulty = random.choice(AI_DIFFICULTY_OPTIONS) if AI_DIFFICULTY_OPTIONS else DEFAULT_AI_DIFFICULTY
                
                available_spells = self.filtered_spells.copy()
                spell1 = random.choice(available_spells) if available_spells else ""
                if spell1 in available_spells:
                    available_spells.remove(spell1)
                spell2 = random.choice(available_spells) if available_spells else ""
                
                bot_data = {
                    "name": bot_name,
                    "ready": True,
                    "champion": champion,
                    "team": team,
                    "skin": skin,
                    "spell1": spell1,
                    "spell2": spell2,
                    "AIDifficulty": difficulty,
                    "is_bot": True
                }
                
                self.send({
                    "type": "add_bot",
                    "bot_data": bot_data
                })
                
                bots_added += 1
                current_players += 1
        
        if bots_added > 0:
            self.add_chat(f"SYSTEM: 🤖 Added {bots_added} bots to fill the lobby ({current_players}/{total_required_players})")
            messagebox.showinfo("Autofill", f"Added {bots_added} bots!\n\nTotal players: {current_players}/{total_required_players}", parent=self.root)
        else:
            messagebox.showinfo("Autofill", "No bots were needed - lobby is already full!", parent=self.root)
        
        self.root.after(100, self.update_add_bot_button())

    async def connect_websocket_async(self):
        try:
            self.websocket = await websockets.connect(f"ws://{self.host_ip}:{PORT}")
            
            default_champion = self.filtered_champions[0] if self.filtered_champions else ""
            default_team = TEAMS[0] if TEAMS else ""
            default_spell1 = self.filtered_spells[0] if self.filtered_spells else ""
            default_spell2 = self.filtered_spells[1] if len(self.filtered_spells) > 1 else ""
            
            await self.send_async({
                "type": "join", 
                "name": self.name,
                "champion": default_champion,
                "team": default_team,
                "skin": DEFAULT_SKIN,
                "spell1": default_spell1,
                "spell2": default_spell2,
                "runes": self.player_runes,
                "talents": self.player_talents
            })
            
            await self.receive_loop_async()
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Cannot connect to server: {e}", parent=self.root))
            self.root.after(0, self.root.destroy)

    def connect_websocket(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.connect_websocket_async())
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Cannot connect to server: {e}", parent=self.root))
            self.root.after(0, self.root.destroy)

    async def send_async(self, data):
        if self.websocket:
            await self.websocket.send(json.dumps(data))

    def send(self, data):
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.send_async(data), self.loop)

    async def receive_loop_async(self):
        try:
            async for message in self.websocket:
                data = json.loads(message)
                self.root.after(0, self.handle_message, data)
                
        except websockets.exceptions.ConnectionClosed:
            self.root.after(0, lambda: messagebox.showinfo("Disconnected", "Disconnected from server", parent=self.root))
            self.root.after(0, self.root.destroy)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showinfo("Error", f"Connection error: {e}", parent=self.root))
            self.root.after(0, self.root.destroy)

    def handle_message(self, data):
        if data["type"] == "lobby_update":
            self.update_lobby(data["players"], data.get("is_host", False), data.get("game_settings"))
            self.root.after(100, self.update_add_bot_button)

        elif data["type"] == "chat":
            self.add_chat(f"{data['sender']}: {data['message']}")
            
        elif data["type"] == "kicked":
            messagebox.showinfo("Kicked", "You were kicked from the lobby by the host", parent=self.root)
            self.root.destroy()

        elif data["type"] == "all_players_ready":
            if data["all_ready"] and self.is_host:
                self.root.after(0, lambda: self.start_game_button.config(state="normal", bg=DARK_THEME['warning']))
        
        elif data["type"] == "launch_game":
            self.create_and_launch_connect_bat(data)
        
        elif data["type"] == "gameinfo_data":
            self.create_gameinfo_file(data)
        
        elif data["type"] == "error":
            messagebox.showerror("Error", data["message"], parent=self.root)
            self.add_chat(f"SYSTEM: ERROR - {data['message']}")
            self.root.after(100, self.update_add_bot_button)

    def on_close(self):
        """Χειρίζεται το κλείσιμο του παραθύρου"""
        self.disconnect()

    def disconnect(self):
        """Αποσυνδέεται από τον server"""
        if self.websocket:
            asyncio.run_coroutine_threadsafe(self.websocket.close(), self.loop)
        if self.loop and self.loop.is_running():
            self.loop.stop()
        self.root.destroy()

    def open_runes_editor(self):
        try:
            if os.path.exists(RUNES_EDITOR_EXE):
                process = subprocess.Popen([RUNES_EDITOR_EXE])
                self.add_chat(f"SYSTEM: 🧿 Launching Runes Editor...")
                
                def wait_and_reload():
                    process.wait()
                    self.root.after(100, self.send_runes_update)
                    self.add_chat(f"SYSTEM: 🔄 Runes and Talents updated from Runes Editor")
                
                threading.Thread(target=wait_and_reload, daemon=True).start()
                
            else:
                messagebox.showwarning("Runes Editor Not Found", 
                    f"Runes Editor executable not found!\n\n"
                    f"Expected at: {RUNES_EDITOR_EXE}\n\n"
                    f"Please make sure RunesEditor.exe is in the correct location.", parent=self.root)
                self.add_chat(f"SYSTEM: ❌ Runes Editor not found at {RUNES_EDITOR_EXE}")
                
        except Exception as e:
            error_msg = f"Failed to launch Runes Editor: {str(e)}"
            messagebox.showerror("Runes Editor Error", error_msg, parent=self.root)
            self.add_chat(f"SYSTEM: ❌ Runes Editor error - {error_msg}")
	
    def reconnect_game(self):
        try:
            if os.path.exists(BAT_OUTPUT_PATH):
                os.startfile(BAT_OUTPUT_PATH)
                self.add_chat(f"SYSTEM: 🔄 Reconnecting to game...")
                messagebox.showinfo("Reconnect", "Launching League of Legends with saved connection settings!", parent=self.root)
            else:
                messagebox.showwarning("Reconnect", 
                    f"Connect file not found!\n\n"
                    f"Expected at: {BAT_OUTPUT_PATH}\n\n"
                    f"Please start the game normally first to generate the connect file.", parent=self.root)
                self.add_chat(f"SYSTEM: ❌ Reconnect failed - connect.bat not found")
                
        except Exception as e:
            error_msg = f"Failed to reconnect: {str(e)}"
            messagebox.showerror("Reconnect Error", error_msg, parent=self.root)
            self.add_chat(f"SYSTEM: ❌ Reconnect error - {error_msg}")

    def send_game_settings_update(self):
        if self.is_host:
            settings = self.game_settings_frame.get_settings()
            
            new_limit = PLAYER_COUNT_LIMITS.get(settings["player_count"], 10)
            current_count = self.get_current_player_count()
            
            if new_limit > 0 and current_count > new_limit:
                messagebox.showwarning("Player Limit Conflict",
                                    f"Cannot change to {settings['player_count']}.\n"
                                    f"Current player count ({current_count}) exceeds the new limit ({new_limit}).\n"
                                    f"Please remove some players or bots first.", parent=self.root)
                return
            
            self.send({
                "type": "update_game_settings",
                "game_mode": settings["game_mode"],
                "map": settings["map"],
                "player_count": settings["player_count"],
                "manacosts": settings["manacosts"],
                "cooldowns": settings["cooldowns"],
                "cheats": settings["cheats"],
                "minion_spawns": settings["minion_spawns"]
            })
            
            self.root.after(100, self.update_add_bot_button)

    def show_add_bot_dialog(self):
        if not self.is_host:
            messagebox.showinfo("Info", "Only the host can add bots.", parent=self.root)
            return
        
        if not self.can_add_more_players():
            current_limit = self.get_current_player_limit()
            messagebox.showwarning("Player Limit Reached", 
                                f"Cannot add more players/bots.\n"
                                f"Current limit for {self.game_settings.get('player_count', '5v5')} is {current_limit} players.", parent=self.root)
            return
            
        bot_win = tk.Toplevel(self.root)
        bot_win.title("Add Bot")
        bot_win.geometry("300x465")
        bot_win.configure(bg=DARK_THEME['bg_dark'])
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ BOT DIALOG
        self.center_window(bot_win)
        
        # ΠΡΟΣΘΗΚΗ: Ορισμός ως transient του κύριου παραθύρου
        bot_win.transient(self.root)
        bot_win.grab_set()
        
        tk.Label(bot_win, text="Add Bot Player", font=("Arial", 12, "bold"),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(pady=10)
        
        # Bot name
        tk.Label(bot_win, text="Bot Name:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        bot_name_var = tk.StringVar(value=f"Bot_{random.randint(1000, 9999)}")
        bot_name_entry = tk.Entry(bot_win, textvariable=bot_name_var, width=20,
                                bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'])
        bot_name_entry.pack(pady=5, padx=20, fill="x")
        
        # Champion selection
        tk.Label(bot_win, text="Champion:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        champion_var = tk.StringVar(value=random.choice(self.filtered_champions) if self.filtered_champions else "")
        champion_combo = ttk.Combobox(bot_win, textvariable=champion_var, values=self.filtered_champions, state="readonly")
        champion_combo.pack(pady=5, padx=20, fill="x")
        
        # Team selection
        tk.Label(bot_win, text="Team:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        team_var = tk.StringVar(value=random.choice(TEAMS) if TEAMS else "")
        team_combo = ttk.Combobox(bot_win, textvariable=team_var, values=TEAMS, state="readonly")
        team_combo.pack(pady=5, padx=20, fill="x")
        
        # Skin selection
        tk.Label(bot_win, text="Skin:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        skin_var = tk.StringVar(value=random.choice(SKINS) if SKINS else DEFAULT_SKIN)
        skin_combo = ttk.Combobox(bot_win, textvariable=skin_var, values=SKINS, state="readonly")
        skin_combo.pack(pady=5, padx=20, fill="x")
        
        # AI Difficulty selection
        tk.Label(bot_win, text="AI Difficulty:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        difficulty_var = tk.StringVar(value=DEFAULT_AI_DIFFICULTY)
        difficulty_combo = ttk.Combobox(bot_win, textvariable=difficulty_var, 
                                      values=AI_DIFFICULTY_OPTIONS, state="readonly")
        difficulty_combo.pack(pady=5, padx=20, fill="x")
        
        # Spell 1 selection
        tk.Label(bot_win, text="Spell 1:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        spell1_var = tk.StringVar(value=random.choice(self.filtered_spells) if self.filtered_spells else "")
        spell1_combo = ttk.Combobox(bot_win, textvariable=spell1_var, values=self.filtered_spells, state="readonly")
        spell1_combo.pack(pady=5, padx=20, fill="x")
        
        # Spell 2 selection
        tk.Label(bot_win, text="Spell 2:", bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=20)
        available_spells = [s for s in self.filtered_spells if s != spell1_var.get()]
        spell2_var = tk.StringVar(value=random.choice(available_spells) if available_spells else "")
        spell2_combo = ttk.Combobox(bot_win, textvariable=spell2_var, values=self.filtered_spells, state="readonly")
        spell2_combo.pack(pady=5, padx=20, fill="x")
        
        def add_bot():
            bot_name = bot_name_var.get().strip()
            if not bot_name:
                messagebox.showwarning("Warning", "Please enter a bot name", parent=bot_win)
                return
                
            bot_data = {
                "name": bot_name,
                "ready": True,
                "champion": champion_var.get(),
                "team": team_var.get(),
                "skin": skin_var.get(),
                "spell1": spell1_var.get(),
                "spell2": spell2_var.get(),
                "AIDifficulty": difficulty_var.get(),
                "is_bot": True
            }
            
            self.send({
                "type": "add_bot",
                "bot_data": bot_data
            })
            bot_win.destroy()
            
            self.root.after(100, self.update_add_bot_button)
        
        def randomize_bot():
            bot_name_var.set(f"Bot_{random.randint(1000, 9999)}")
            if self.filtered_champions:
                champion_var.set(random.choice(self.filtered_champions))
            if TEAMS:
                team_var.set(random.choice(TEAMS))
            if SKINS:
                skin_var.set(random.choice(SKINS))
            if AI_DIFFICULTY_OPTIONS:
                difficulty_var.set(random.choice(AI_DIFFICULTY_OPTIONS))
            if self.filtered_spells:
                spell1_var.set(random.choice(self.filtered_spells))
                available_spells = [s for s in self.filtered_spells if s != spell1_var.get()]
                if available_spells:
                    spell2_var.set(random.choice(available_spells))
        
        button_frame = tk.Frame(bot_win, bg=DARK_THEME['bg_dark'])
        button_frame.pack(pady=15)
        
        tk.Button(button_frame, text="🎲 Randomize", command=randomize_bot, width=12, 
                 bg=DARK_THEME['accent'], fg="white", cursor="hand2").pack(side="left", padx=5)
        tk.Button(button_frame, text="➕ Add Bot", command=add_bot, width=12, 
                 bg=DARK_THEME['success'], fg="white", cursor="hand2").pack(side="left", padx=5)
        tk.Button(button_frame, text="❌ Cancel", command=bot_win.destroy, width=12,
                 bg=DARK_THEME['error'], fg="white", cursor="hand2").pack(side="left", padx=5)
        
        bot_win.mainloop()

    def ask_username_with_history(self, usernames_history):
        win = tk.Toplevel(self.root)
        win.title("Enter Username")
        win.geometry("300x150")
        win.configure(bg=DARK_THEME['bg_dark'])
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ USERNAME DIALOG
        self.center_window(win)
        
        # ΠΡΟΣΘΗΚΗ: Ορισμός ως transient του κύριου παραθύρου
        win.transient(self.root)
        win.grab_set()
        
        tk.Label(win, text="Enter your username:", font=("Arial", 10),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(pady=10)
        
        username_var = tk.StringVar()
        username_combo = ttk.Combobox(win, textvariable=username_var, values=usernames_history)
        username_combo.pack(pady=5, padx=20, fill="x")
        username_combo.focus()
        
        result = [None]
        
        def on_ok():
            username = username_var.get().strip()
            if username:
                result[0] = username
                win.destroy()
            else:
                messagebox.showwarning("Warning", "Please enter a username", parent=win)
        
        def on_cancel():
            win.destroy()
        
        win.bind('<Return>', lambda e: on_ok())
        
        button_frame = tk.Frame(win, bg=DARK_THEME['bg_dark'])
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="OK", command=on_ok, width=10,
                 bg=DARK_THEME['success'], fg="white", cursor="hand2").pack(side="left", padx=5)
        tk.Button(button_frame, text="Cancel", command=on_cancel, width=10,
                 bg=DARK_THEME['error'], fg="white", cursor="hand2").pack(side="left", padx=5)
        
        win.wait_window()
        return result[0]

    def send_ready(self):
        self.send({"type": "ready", "ready": self.ready_var.get()})
        
    def send_player_update(self):
        """Αποστολή ενημέρωσης παίκτη και ενημέρωση Smart Select"""
        if self.name in self.player_frames and not self.player_frames[self.name].player_data["ready"]:
            frame = self.player_frames[self.name]
            selection = frame.get_selection()
            self.send({
                "type": "player_update",
                "champion": selection["champion"],
                "team": selection["team"],
                "skin": selection["skin"],
                "spell1": selection["spell1"],
                "spell2": selection["spell2"],
                "runes": self.player_runes,
                "talents": self.player_talents
            })
            
            # ΕΝΗΜΕΡΩΣΗ SMART SELECT
            self.update_smart_select_from_lobby("all")

    def send_chat(self):
        msg = self.chat_entry.get().strip()
        if msg:
            self.send({"type": "chat", "sender": self.name, "message": msg})
            self.chat_entry.delete(0, tk.END)

    def create_and_launch_connect_bat(self, data):
        player_data = data["player_data"]
        host_ip = data["host_ip"]
        game_port = data["game_port"]
        
        if player_data["name"] == self.name:
            try:
                bat_content = f"""@echo off
echo Connecting to game as player: {player_data['name']}
echo IP: {host_ip}
echo Port: {game_port}
echo Player ID: {player_data['playerId']}
echo.
echo Starting League of Legends...
cd {LEAGUE_PATH}
"League of Legends.exe" "" "" "" "{host_ip} {game_port} {player_data['blowfishKey']} {player_data['playerId']}"
exit
"""
                
                bat_path = BAT_OUTPUT_PATH
                
                os.makedirs(os.path.dirname(bat_path), exist_ok=True)
                
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                
                bat_dir = os.path.dirname(bat_path)
                os.startfile(bat_path)
                
                self.add_chat(f"SYSTEM: Launching League of Legends for {player_data['name']}")
                self.add_chat(f"SYSTEM: Batch file created at: {bat_path}")
                
            except Exception as e:
                self.add_chat(f"SYSTEM: ERROR - Failed to create connect.bat: {e}")
                messagebox.showerror("Error", f"Failed to create connect.bat: {e}", parent=self.root)

    def create_gameinfo_file(self, data):
        try:
            players_data = data["players_data"]
            game_settings = data["game_settings"]
            
            game_info = {
                "gameId": 1,
                "game": {
                    "map": get_map_id(game_settings["map"]),
                    "gameMode": get_game_mode_id(game_settings["game_mode"]),
                    "mutators": ["", "", "", "", "", "", "", ""],
                    "dataPackage": "AvCsharp-Scripts"
                },
                "gameInfo": {
                    "TICK_RATE": 30,
                    "CLIENT_VERSION": "1.0.0.126",
                    "FORCE_START_TIMER": 60,
                    "MANACOSTS_ENABLED": game_settings.get("manacosts", True),
                    "COOLDOWNS_ENABLED": game_settings.get("cooldowns", True),
                    "CHEATS_ENABLED": game_settings.get("cheats", False),
                    "MINION_SPAWNS_ENABLED": game_settings.get("minion_spawns", True),
                    "CONTENT_PATH": "../../../../../Content",
                    "IS_DAMAGE_TEXT_GLOBAL": False,
                    "ENDGAME_HTTP_POST_ADDRESS": "",
                    "APIKEYDROPBOX": "",
                    "USERNAMEOFREPLAYMAN": "",
                    "PASSWORDOFREPLAYMAN": "",
                    "ENABLE_LAUNCHER": False,
                    "LAUNCHER_ADRESS_AND_PORT": "127.0.0.1:25565",
                    "SUPRESS_SCRIPT_NOT_FOUND_LOGS": True,
                    "AB_CLIENT": False,
                    "ENABLE_LOG_AND_CONSOLEWRITELINE": False,
                    "ENABLE_LOG_BehaviourTree": True,
                    "ENABLE_LOG_PKT": False,
                    "ENABLE_REPLAY": False,
                    "ENABLE_ALLOCATION_TRACKER": False,
                    "SCRIPT_ASSEMBLIES": [
                        "AvLua-Converted",
                        "AvCsharp-Scripts"
                    ]
                },
                "players": players_data
            }
            
            with open(GAMEINFO_PATH, 'w', encoding='utf-8') as f:
                json.dump(game_info, f, indent=4, ensure_ascii=False)
            
            self.add_chat(f"SYSTEM: Game configuration saved to {GAMEINFO_PATH}")
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save gameinfo.json: {e}", parent=self.root)
            self.add_chat(f"SYSTEM: ERROR - Failed to save game configuration: {e}")
            return False

    def update_lobby(self, players, is_host=False, game_settings=None):
        self.is_host = is_host
        
        if game_settings:
            self.game_settings = game_settings
            self.game_settings_frame.update_settings(game_settings, is_host)
        
        self.update_add_bot_button()
        
        current_limit = self.get_current_player_limit()
        current_count = len(players)
        
        if current_limit > 0:
            if current_count >= current_limit:
                self.add_chat(f"SYSTEM: ⚠️ Player limit reached: {current_count}/{current_limit}")
            elif current_count == current_limit - 1:
                self.add_chat(f"SYSTEM: ℹ️ Only 1 slot remaining ({current_count}/{current_limit})")
        
        title_text = "Champion Select - All Players"
        if self.is_host:
            title_text += " (HOST)"
            self.start_game_button.pack(pady=10)
        else:
            self.start_game_button.pack_forget()
        
        self.title_label.config(text=title_text)
        
        if self.is_host:
            all_ready = self.check_all_players_ready(players)
            if all_ready and len(players) > 0:
                self.start_game_button.config(state="normal", bg=DARK_THEME['warning'])
            else:
                self.start_game_button.config(state="disabled", bg=DARK_THEME['bg_light'])
        
        self.last_players_list = players
        self.update_lobby_display(players)

    def check_all_players_ready(self, players):
        if not players:
            return False
        
        for player in players:
            if not player.get("ready", False):
                return False
        return True

    def start_game(self):
        if not self.is_host:
            return
        
        self.send({
            "type": "launch_game", 
            "host_ip": self.host_ip,
            "game_port": GAME_PORT
        })
        
        self.launch_game_server()

    def launch_game_server(self):
        if not self.is_host:
            return False
            
        if not SERVER_PATH or not os.path.exists(SERVER_PATH):
            messagebox.showerror("Error", 
                f"Cannot find server executable.\n\n"
                f"Please check paths.json configuration.\n"
                f"Current path: {SERVER_PATH}", parent=self.root)
            return False
        
        try:
            subprocess.Popen([SERVER_PATH], cwd=os.path.dirname(SERVER_PATH))
            self.add_chat("SYSTEM: Game server launched successfully!")
            return True
                
        except Exception as e:
            error_msg = f"Failed to launch server: {str(e)}"
            messagebox.showerror("Error", f"{error_msg}", parent=self.root)
            self.add_chat(f"SYSTEM: ERROR - {error_msg}")
            return False

    def update_lobby_display(self, players_list):
        current_players = {p["name"] for p in players_list}
        
        for player_name in list(self.player_frames.keys()):
            if player_name not in current_players:
                if player_name in self.player_frames:
                    self.player_frames[player_name].destroy()
                    del self.player_frames[player_name]
        
        sorted_players = self.sort_players_by_category(players_list)
        
        for widget in self.players_container.winfo_children():
            widget.destroy()
        
        if self.is_expanded:
            self._create_expanded_layout(sorted_players)
        else:
            self._create_collapsed_layout(sorted_players)
        
        self._force_canvas_refresh()

    def _create_collapsed_layout(self, sorted_players):
        for i, player_data in enumerate(sorted_players):
            player_name = player_data["name"]
            is_own_player = (player_name == self.name)
            is_bot = player_data.get("is_bot", False)
            
            frame = PlayerChampionFrame(self.players_container, player_data, is_own_player, self.is_host, is_bot, self.filtered_champions, self.filtered_spells)
            
            frame.config(width=200)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            if is_own_player:
                frame.set_callback(self.send_player_update)
                # ΠΡΟΣΘΗΚΗ: Σύνδεση callback για ενημέρωση Smart Select
                frame.parent_callback = self.update_smart_select_from_lobby
            elif self.is_host and is_bot:
                frame.set_callback(lambda bot_name=player_name: self.send_bot_update(bot_name))
            
            if self.is_host and not is_own_player:
                frame.set_kick_callback(self.kick_player if not is_bot else self.remove_bot)
            
            self.player_frames[player_name] = frame
        
        for i in range(len(sorted_players)):
            self.players_container.columnconfigure(i, weight=1, minsize=200)

    def _create_expanded_layout(self, sorted_players):
        my_team = None
        for player in sorted_players:
            if player["name"] == self.name:
                my_team = player["team"]
                break
        
        if my_team is None:
            self._create_collapsed_layout(sorted_players)
            return
        
        friendly_players = []
        enemy_players = []
        
        for player in sorted_players:
            if player["team"] == my_team:
                friendly_players.append(player)
            else:
                enemy_players.append(player)
        
        for i, player_data in enumerate(friendly_players):
            player_name = player_data["name"]
            is_own_player = (player_name == self.name)
            is_bot = player_data.get("is_bot", False)
            
            frame = PlayerChampionFrame(self.players_container, player_data, is_own_player, self.is_host, is_bot, self.filtered_champions, self.filtered_spells)
            
            frame.config(width=200)
            frame.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            
            if is_own_player:
                frame.set_callback(self.send_player_update)
                # ΠΡΟΣΘΗΚΗ: Σύνδεση callback για ενημέρωση Smart Select
                frame.parent_callback = self.update_smart_select_from_lobby
            elif self.is_host and is_bot:
                frame.set_callback(lambda bot_name=player_name: self.send_bot_update(bot_name))
            
            if self.is_host and not is_own_player:
                frame.set_kick_callback(self.kick_player if not is_bot else self.remove_bot)
            
            self.player_frames[player_name] = frame
        
        for i, player_data in enumerate(enemy_players):
            player_name = player_data["name"]
            is_own_player = (player_name == self.name)
            is_bot = player_data.get("is_bot", False)
            
            frame = PlayerChampionFrame(self.players_container, player_data, is_own_player, self.is_host, is_bot, self.filtered_champions, self.filtered_spells)
            
            frame.config(width=200)
            frame.grid(row=1, column=i, padx=5, pady=5, sticky="nsew")
            
            if is_own_player:
                frame.set_callback(self.send_player_update)
                # ΠΡΟΣΘΗΚΗ: Σύνδεση callback για ενημέρωση Smart Select
                frame.parent_callback = self.update_smart_select_from_lobby
            elif self.is_host and is_bot:
                frame.set_callback(lambda bot_name=player_name: self.send_bot_update(bot_name))
            
            if self.is_host and not is_own_player:
                frame.set_kick_callback(self.kick_player if not is_bot else self.remove_bot)
            
            self.player_frames[player_name] = frame
        
        max_columns = max(len(friendly_players), len(enemy_players))
        for i in range(max_columns):
            self.players_container.columnconfigure(i, weight=1, minsize=200)

    def sort_players_by_category(self, players_list):
        if not players_list:
            return []
        
        my_team = None
        for player in players_list:
            if player["name"] == self.name:
                my_team = player["team"]
                break
        
        if my_team is None:
            return players_list
        
        categories = {
            "me": [],
            "allied_players": [],
            "allied_bots": [],
            "enemy_bots": [],
            "enemy_players": []
        }
        
        for player in players_list:
            player_name = player["name"]
            is_bot = player.get("is_bot", False)
            is_same_team = (player["team"] == my_team)
            
            if player_name == self.name:
                categories["me"].append(player)
            elif is_same_team and not is_bot:
                categories["allied_players"].append(player)
            elif is_same_team and is_bot:
                categories["allied_bots"].append(player)
            elif not is_same_team and is_bot:
                categories["enemy_bots"].append(player)
            else:
                categories["enemy_players"].append(player)
        
        sorted_players = (
            categories["me"] +
            categories["allied_players"] +
            categories["allied_bots"] +
            categories["enemy_bots"] +
            categories["enemy_players"]
        )
        
        return sorted_players

    def _force_canvas_refresh(self):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
            total_width = len(self.player_frames) * 210
            canvas_width = self.canvas.winfo_width()
            
            content_width = max(total_width, canvas_width)
            self.canvas.itemconfig(self.canvas_window, width=content_width)
            
            self._check_scrollbar_needed()
            
            self.canvas.update_idletasks()
            
        except Exception as e:
            print(f"Canvas refresh error: {e}")

    def _final_canvas_update(self):
        try:
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            self._check_scrollbar_needed()
        except:
            pass

    def add_chat(self, msg):
        self.chat_text.config(state="normal")
        self.chat_text.insert(tk.END, msg + "\n")
        self.chat_text.config(state="disabled")
        self.chat_text.see(tk.END)

    def kick_player(self, player_name):
        if self.is_host and player_name != self.name:
            self.send({"type": "kick_player", "target_player": player_name})
            self.root.after(100, self.update_add_bot_button)

    def remove_bot(self, bot_name):
        if self.is_host:
            self.send({
                "type": "remove_bot",
                "bot_name": bot_name
            })
            self.root.after(100, self.update_add_bot_button)