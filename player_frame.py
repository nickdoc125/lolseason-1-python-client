import tkinter as tk
from tkinter import ttk
from config import CHAMPIONS, TEAMS, SUMMONER_SPELLS, SKINS, DEFAULT_SKIN, AI_DIFFICULTY_OPTIONS, DEFAULT_AI_DIFFICULTY, GAME_DATA

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

class PlayerChampionFrame(tk.Frame):
    def __init__(self, parent, player_data, is_own_player=False, is_host=False, is_bot=False, filtered_champions=None, filtered_spells=None):
        super().__init__(parent, relief="solid", bd=1, padx=5, pady=5, width=200, bg=DARK_THEME['bg_medium'])
        self.player_data = player_data
        self.is_own_player = is_own_player
        self.is_host = is_host
        self.is_bot = is_bot
        self.current_champion = player_data["champion"]
        
        self.filtered_champions = filtered_champions if filtered_champions else CHAMPIONS
        self.filtered_spells = filtered_spells if filtered_spells else SUMMONER_SPELLS
        
        # Player name with ready status and bot indicator
        status_icon = "✅" if player_data["ready"] else "❌"
        bot_indicator = "🤖 " if is_bot else ""
        
        name_label = tk.Label(self, text=f"{status_icon} {bot_indicator}{player_data['name']}", 
                             font=("Arial", 10, "bold"),
                             bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'])
        name_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # Kick button for host (only for other players and not for bots)
        if is_host and not is_own_player and not is_bot:
            self.kick_button = tk.Button(self, text="KICK", command=self.kick_player,
                                       bg=DARK_THEME['error'], fg="white", font=("Arial", 8, "bold"),
                                       cursor="hand2")
            self.kick_button.grid(row=0, column=2, padx=5, sticky="e")
        
        # Remove button for bots (only for host)
        if is_host and is_bot:
            self.remove_button = tk.Button(self, text="REMOVE", command=self.kick_player,
                                         bg=DARK_THEME['warning'], fg="white", font=("Arial", 8, "bold"),
                                         cursor="hand2")
            self.remove_button.grid(row=0, column=2, padx=5, sticky="e")
        
        # Champion Selection (readonly for other players and bots)
        tk.Label(self, text="Champion:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=1, column=0, sticky="w", padx=2, pady=1)
        self.champion_var = tk.StringVar(value=player_data["champion"])
        
        # ΓΙΑ BOTS: Ο host μπορεί να αλλάξει τα bots (readonly=False)
        if (is_own_player and not player_data["ready"]) or (is_host and is_bot):
            if self.filtered_champions:
                self.champion_combo = ttk.Combobox(self, textvariable=self.champion_var, 
                                                 values=self.filtered_champions, state="readonly", width=12)
                self.champion_combo.grid(row=1, column=1, padx=2, pady=1)
                self.champion_combo.bind('<<ComboboxSelected>>', self.on_champion_change)
        else:
            bg_color = DARK_THEME['success'] if is_bot else DARK_THEME['bg_light']
            self.champion_label = tk.Label(self, text=player_data["champion"], width=12, 
                    bg=bg_color, fg=DARK_THEME['text_primary'])
            self.champion_label.grid(row=1, column=1, padx=2, pady=1)
        
        # Team Selection
        tk.Label(self, text="Team:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=2, column=0, sticky="w", padx=2, pady=1)
        self.team_var = tk.StringVar(value=player_data["team"])
        
        # ΓΙΑ BOTS: Ο host μπορεί να αλλάξει τα bots (readonly=False)
        if (is_own_player and not player_data["ready"]) or (is_host and is_bot):
            if TEAMS:
                self.team_combo = ttk.Combobox(self, textvariable=self.team_var, 
                                             values=TEAMS, state="readonly", width=12)
                self.team_combo.grid(row=2, column=1, padx=2, pady=1)
                self.team_combo.bind('<<ComboboxSelected>>', self.on_change)
        else:
            if is_bot:
                team_color = DARK_THEME['success']
            else:
                team_color = "#2E86C1" if player_data["team"] == "BLUE" else "#A93226"  # Darker blue/red
            self.team_label = tk.Label(self, text=player_data["team"], width=12, 
                    bg=team_color, fg="white")
            self.team_label.grid(row=2, column=1, padx=2, pady=1)
        
        # Skin Selection με φίλτρο ανά champion
        tk.Label(self, text="Skin:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=3, column=0, sticky="w", padx=2, pady=1)
        self.skin_var = tk.StringVar(value=player_data["skin"])
        
        # Λήψη available skins για τον τρέχοντα champion
        self.available_skins = self.get_champion_skins(player_data["champion"])
        
        # ΓΙΑ BOTS: Ο host μπορεί να αλλάξει τα bots (readonly=False)
        if (is_own_player and not player_data["ready"]) or (is_host and is_bot):
            if self.available_skins:
                self.skin_combo = ttk.Combobox(self, textvariable=self.skin_var, 
                                             values=self.available_skins, state="readonly", width=12)
                self.skin_combo.grid(row=3, column=1, padx=2, pady=1)
                self.skin_combo.bind('<<ComboboxSelected>>', self.on_change)
                
                if player_data["skin"] not in self.available_skins:
                    self.skin_var.set(self.available_skins[0])
        else:
            bg_color = DARK_THEME['success'] if is_bot else DARK_THEME['bg_light']
            self.skin_label = tk.Label(self, text=player_data["skin"], width=12, 
                    bg=bg_color, fg=DARK_THEME['text_primary'])
            self.skin_label.grid(row=3, column=1, padx=2, pady=1)
        
        # Spell 1 Selection
        tk.Label(self, text="Spell 1:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=4, column=0, sticky="w", padx=2, pady=1)
        self.spell1_var = tk.StringVar(value=player_data["spell1"])
        
        # ΓΙΑ BOTS: Ο host μπορεί να αλλάξει τα bots (readonly=False)
        if (is_own_player and not player_data["ready"]) or (is_host and is_bot):
            if self.filtered_spells:
                self.spell1_combo = ttk.Combobox(self, textvariable=self.spell1_var, 
                                               values=self.filtered_spells, state="readonly", width=12)
                self.spell1_combo.grid(row=4, column=1, padx=2, pady=1)
                self.spell1_combo.bind('<<ComboboxSelected>>', self.on_change)
        else:
            bg_color = DARK_THEME['success'] if is_bot else DARK_THEME['bg_light']
            self.spell1_label = tk.Label(self, text=player_data["spell1"], width=12, 
                    bg=bg_color, fg=DARK_THEME['text_primary'])
            self.spell1_label.grid(row=4, column=1, padx=2, pady=1)
        
        # Spell 2 Selection
        tk.Label(self, text="Spell 2:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=5, column=0, sticky="w", padx=2, pady=1)
        self.spell2_var = tk.StringVar(value=player_data["spell2"])
        
        # ΓΙΑ BOTS: Ο host μπορεί να αλλάξει τα bots (readonly=False)
        if (is_own_player and not player_data["ready"]) or (is_host and is_bot):
            if self.filtered_spells:
                self.spell2_combo = ttk.Combobox(self, textvariable=self.spell2_var, 
                                               values=self.filtered_spells, state="readonly", width=12)
                self.spell2_combo.grid(row=5, column=1, padx=2, pady=1)
                self.spell2_combo.bind('<<ComboboxSelected>>', self.on_change)
        else:
            bg_color = DARK_THEME['success'] if is_bot else DARK_THEME['bg_light']
            self.spell2_label = tk.Label(self, text=player_data["spell2"], width=12, 
                    bg=bg_color, fg=DARK_THEME['text_primary'])
            self.spell2_label.grid(row=5, column=1, padx=2, pady=1)
        
        # AI Difficulty (only for bots) - Ο host μπορεί να αλλάξει difficulty
        if is_bot and AI_DIFFICULTY_OPTIONS:
            tk.Label(self, text="AI Difficulty:", bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).grid(row=6, column=0, sticky="w", padx=2, pady=1)
            difficulty = player_data.get("AIDifficulty", DEFAULT_AI_DIFFICULTY)
            
            if is_host:
                self.difficulty_var = tk.StringVar(value=difficulty)
                self.difficulty_combo = ttk.Combobox(self, textvariable=self.difficulty_var, 
                                                   values=AI_DIFFICULTY_OPTIONS, state="readonly", width=12)
                self.difficulty_combo.grid(row=6, column=1, padx=2, pady=1)
                self.difficulty_combo.bind('<<ComboboxSelected>>', self.on_change)
            else:
                self.difficulty_label = tk.Label(self, text=difficulty, width=12, 
                                               bg=DARK_THEME['success'], fg="white", font=("Arial", 8))
                self.difficulty_label.grid(row=6, column=1, padx=2, pady=1)
        
        # Απενεργοποίηση controls αν ο παίκτης είναι ready (μόνο για πραγματικούς παίκτες)
        if not is_bot:
            self._update_controls_state()
    
    def get_champion_skins(self, champion_name):
        """Επιστρέφει τη λίστα με τα skins για τον συγκεκριμένο champion"""
        champions = GAME_DATA.get("champions", {})
        if champion_name in champions:
            skins_dict = champions[champion_name].get("skins", {})
            return list(skins_dict.keys())
        return ["Classic"]  # Fallback
    
    def on_champion_change(self, event=None):
        """Χειρίζεται την αλλαγή champion και ενημερώνει τα available skins"""
        new_champion = self.champion_var.get()
        self.current_champion = new_champion
        
        # Ενημέρωση available skins για τον νέο champion
        self.available_skins = self.get_champion_skins(new_champion)
        
        # Ενημέρωση του skin combobox
        if hasattr(self, 'skin_combo'):
            self.skin_combo['values'] = self.available_skins
            
            # Αλλαγή του skin στο πρώτο διαθέσιμο αν το τρέχον δεν είναι διαθέσιμο
            current_skin = self.skin_var.get()
            if current_skin not in self.available_skins and self.available_skins:
                self.skin_var.set(self.available_skins[0])
        
        # Καλεί το κανονικό callback
        self.on_change(event)
        
        # ΕΙΔΙΚΗ ΕΝΗΜΕΡΩΣΗ ΓΙΑ CHAMPION
        if hasattr(self, 'parent_callback'):
            self.parent_callback("champion")
    
    def on_change(self, event=None):
        """Βελτιωμένο callback με προστασία"""
        # Small delay to ensure UI has updated
        if hasattr(self, '_change_timeout'):
            self.after_cancel(self._change_timeout)
        
        self._change_timeout = self.after(50, self._execute_change_callback)

    def _execute_change_callback(self):
        """Εκτέλεση callback με καθυστέρηση"""
        if (self.is_own_player and hasattr(self, 'callback') and not self.player_data["ready"]) or \
           (self.is_host and self.is_bot and hasattr(self, 'callback')):
            self.callback()
            
            # ΕΝΗΜΕΡΩΣΗ SMART SELECT με προστασία
            if hasattr(self, 'parent_callback'):
                # Use type-specific updates to minimize sync overhead
                if hasattr(self, '_last_champion') and self._last_champion != self.champion_var.get():
                    self.parent_callback("champion")
                    self._last_champion = self.champion_var.get()
                else:
                    self.parent_callback("all")
    
    def kick_player(self):
        if hasattr(self, 'kick_callback'):
            self.kick_callback(self.player_data["name"])
        
    def _update_controls_state(self):
        """Απενεργοποίηση ή ενεργοποίηση των controls βάσει του ready status (μόνο για πραγματικούς παίκτες)"""
        if self.is_own_player and not self.is_bot:
            state = "disabled" if self.player_data["ready"] else "readonly"
            # Απενεργοποίηση combo boxes
            for attr in ['champion_combo', 'team_combo', 'skin_combo', 'spell1_combo', 'spell2_combo']:
                if hasattr(self, attr):
                    getattr(self, attr).config(state=state)
        
    def update_data(self, new_data, is_host=False, is_bot=False, filtered_champions=None, filtered_spells=None):
        self.player_data = new_data
        self.is_host = is_host
        self.is_bot = is_bot
        
        # Ενημέρωση filtered lists
        if filtered_champions:
            self.filtered_champions = filtered_champions
        if filtered_spells:
            self.filtered_spells = filtered_spells
        
        # Update all variables
        self.champion_var.set(new_data["champion"])
        self.team_var.set(new_data["team"])
        self.skin_var.set(new_data["skin"])
        self.spell1_var.set(new_data["spell1"])
        self.spell2_var.set(new_data["spell2"])
        
        # Ενημέρωση available skins αν άλλαξε champion
        if self.current_champion != new_data["champion"]:
            self.current_champion = new_data["champion"]
            self.available_skins = self.get_champion_skins(new_data["champion"])
            
            # Ενημέρωση skin combobox αν υπάρχει
            if hasattr(self, 'skin_combo') and self.available_skins:
                self.skin_combo['values'] = self.available_skins
                
                # Έλεγχος αν το νέο skin είναι διαθέσιμο
                if new_data["skin"] not in self.available_skins:
                    self.skin_var.set(self.available_skins[0])
        
        # Update labels for other players and bots
        if not self.is_own_player or (self.is_bot and not self.is_host):
            bg_color = DARK_THEME['success'] if is_bot else DARK_THEME['bg_light']
            if hasattr(self, 'champion_label'):
                self.champion_label.config(text=new_data["champion"], bg=bg_color)
            
            if is_bot:
                team_color = DARK_THEME['success']
            else:
                team_color = "#2E86C1" if new_data["team"] == "BLUE" else "#A93226"
            if hasattr(self, 'team_label'):
                self.team_label.config(text=new_data["team"], bg=team_color)
            
            if hasattr(self, 'skin_label'):
                self.skin_label.config(text=new_data["skin"], bg=bg_color)
            if hasattr(self, 'spell1_label'):
                self.spell1_label.config(text=new_data["spell1"], bg=bg_color)
            if hasattr(self, 'spell2_label'):
                self.spell2_label.config(text=new_data["spell2"], bg=bg_color)
        
        # Update AI Difficulty for bots
        if self.is_bot and AI_DIFFICULTY_OPTIONS:
            difficulty = new_data.get("AIDifficulty", DEFAULT_AI_DIFFICULTY)
            if self.is_host and hasattr(self, 'difficulty_combo'):
                self.difficulty_var.set(difficulty)
            elif hasattr(self, 'difficulty_label'):
                self.difficulty_label.config(text=difficulty)
        
        # Update ready status and bot indicator
        for widget in self.grid_slaves(row=0, column=0):
            if isinstance(widget, tk.Label):
                status_icon = "✅" if new_data["ready"] else "❌"
                bot_indicator = "🤖 " if is_bot else ""
                widget.config(text=f"{status_icon} {bot_indicator}{new_data['name']}")
        
        # Add or remove kick/remove buttons based on host status
        if self.is_host and not self.is_own_player:
            # Remove existing buttons
            for widget in self.grid_slaves(row=0, column=2):
                widget.destroy()
            
            # Add appropriate button
            if self.is_bot:
                self.remove_button = tk.Button(self, text="REMOVE", command=self.kick_player,
                                             bg=DARK_THEME['warning'], fg="white", font=("Arial", 8, "bold"),
                                             cursor="hand2")
                self.remove_button.grid(row=0, column=2, padx=5, sticky="e")
            else:
                self.kick_button = tk.Button(self, text="KICK", command=self.kick_player,
                                           bg=DARK_THEME['error'], fg="white", font=("Arial", 8, "bold"),
                                           cursor="hand2")
                self.kick_button.grid(row=0, column=2, padx=5, sticky="e")
        elif not self.is_host:
            # Remove buttons if not host
            for widget in self.grid_slaves(row=0, column=2):
                widget.destroy()
        
        # Μετατροπή UI για bots όταν ο host αλλάζει
        if self.is_host and self.is_bot:
            self._convert_to_editable_bot()
        elif not self.is_host and self.is_bot:
            self._convert_to_readonly_bot()
        
        # Απενεργοποίηση controls αν ο παίκτης είναι ready (μόνο για πραγματικούς παίκτες)
        if not self.is_bot:
            self._update_controls_state()
    
    def _convert_to_editable_bot(self):
        """Μετατρέπει τα controls του bot σε editable για τον host"""
        # Champion
        if hasattr(self, 'champion_label') and self.filtered_champions:
            self.champion_label.destroy()
            self.champion_combo = ttk.Combobox(self, textvariable=self.champion_var, 
                                             values=self.filtered_champions, state="readonly", width=12)
            self.champion_combo.grid(row=1, column=1, padx=2, pady=1)
            self.champion_combo.bind('<<ComboboxSelected>>', self.on_champion_change)
        
        # Team
        if hasattr(self, 'team_label') and TEAMS:
            self.team_label.destroy()
            self.team_combo = ttk.Combobox(self, textvariable=self.team_var, 
                                         values=TEAMS, state="readonly", width=12)
            self.team_combo.grid(row=2, column=1, padx=2, pady=1)
            self.team_combo.bind('<<ComboboxSelected>>', self.on_change)
        
        # Skin
        if hasattr(self, 'skin_label') and self.available_skins:
            self.skin_label.destroy()
            self.skin_combo = ttk.Combobox(self, textvariable=self.skin_var, 
                                         values=self.available_skins, state="readonly", width=12)
            self.skin_combo.grid(row=3, column=1, padx=2, pady=1)
            self.skin_combo.bind('<<ComboboxSelected>>', self.on_change)
        
        # Spells
        if hasattr(self, 'spell1_label') and self.filtered_spells:
            self.spell1_label.destroy()
            self.spell1_combo = ttk.Combobox(self, textvariable=self.spell1_var, 
                                           values=self.filtered_spells, state="readonly", width=12)
            self.spell1_combo.grid(row=4, column=1, padx=2, pady=1)
            self.spell1_combo.bind('<<ComboboxSelected>>', self.on_change)
        
        if hasattr(self, 'spell2_label') and self.filtered_spells:
            self.spell2_label.destroy()
            self.spell2_combo = ttk.Combobox(self, textvariable=self.spell2_var, 
                                           values=self.filtered_spells, state="readonly", width=12)
            self.spell2_combo.grid(row=5, column=1, padx=2, pady=1)
            self.spell2_combo.bind('<<ComboboxSelected>>', self.on_change)
        
        # AI Difficulty
        if hasattr(self, 'difficulty_label') and AI_DIFFICULTY_OPTIONS:
            self.difficulty_label.destroy()
            difficulty = self.player_data.get("AIDifficulty", DEFAULT_AI_DIFFICULTY)
            self.difficulty_var = tk.StringVar(value=difficulty)
            self.difficulty_combo = ttk.Combobox(self, textvariable=self.difficulty_var, 
                                               values=AI_DIFFICULTY_OPTIONS, state="readonly", width=12)
            self.difficulty_combo.grid(row=6, column=1, padx=2, pady=1)
            self.difficulty_combo.bind('<<ComboboxSelected>>', self.on_change)
    
    def _convert_to_readonly_bot(self):
        """Μετατρέπει τα controls του bot σε readonly όταν δεν είναι host"""
        # Champion
        if hasattr(self, 'champion_combo'):
            self.champion_combo.destroy()
            bg_color = DARK_THEME['success']
            self.champion_label = tk.Label(self, text=self.champion_var.get(), width=12, bg=bg_color, fg="white")
            self.champion_label.grid(row=1, column=1, padx=2, pady=1)
        
        # Team
        if hasattr(self, 'team_combo'):
            self.team_combo.destroy()
            team_color = DARK_THEME['success']
            self.team_label = tk.Label(self, text=self.team_var.get(), width=12, bg=team_color, fg="white")
            self.team_label.grid(row=2, column=1, padx=2, pady=1)
        
        # Skin
        if hasattr(self, 'skin_combo'):
            self.skin_combo.destroy()
            bg_color = DARK_THEME['success']
            self.skin_label = tk.Label(self, text=self.skin_var.get(), width=12, bg=bg_color, fg="white")
            self.skin_label.grid(row=3, column=1, padx=2, pady=1)
        
        # Spells
        if hasattr(self, 'spell1_combo'):
            self.spell1_combo.destroy()
            bg_color = DARK_THEME['success']
            self.spell1_label = tk.Label(self, text=self.spell1_var.get(), width=12, bg=bg_color, fg="white")
            self.spell1_label.grid(row=4, column=1, padx=2, pady=1)
        
        if hasattr(self, 'spell2_combo'):
            self.spell2_combo.destroy()
            bg_color = DARK_THEME['success']
            self.spell2_label = tk.Label(self, text=self.spell2_var.get(), width=12, bg=bg_color, fg="white")
            self.spell2_label.grid(row=5, column=1, padx=2, pady=1)
        
        # AI Difficulty
        if hasattr(self, 'difficulty_combo') and AI_DIFFICULTY_OPTIONS:
            self.difficulty_combo.destroy()
            difficulty = self.difficulty_var.get()
            self.difficulty_label = tk.Label(self, text=difficulty, width=12, 
                                           bg=DARK_THEME['success'], fg="white", font=("Arial", 8))
            self.difficulty_label.grid(row=6, column=1, padx=2, pady=1)
        
    def set_callback(self, callback):
        self.callback = callback
        
    def set_kick_callback(self, callback):
        self.kick_callback = callback
        
    def get_selection(self):
        selection = {
            "champion": self.champion_var.get(),
            "team": self.team_var.get(),
            "skin": self.skin_var.get(),
            "spell1": self.spell1_var.get(),
            "spell2": self.spell2_var.get()
        }
        
        # Προσθήκη AI difficulty για bots
        if self.is_bot and hasattr(self, 'difficulty_var'):
            selection["AIDifficulty"] = self.difficulty_var.get()
        
        return selection