# config.py
import json
import os
from paths_config import paths_config

# ===================== DARK THEME COLORS =====================
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

# ===================== CONFIGURATION =====================
PORT = 5000

def load_json_data(filepath, default_data=None):
    """Φόρτωση δεδομένων από JSON αρχείο"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"Warning: File {filepath} does not exist")
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    
    return default_data if default_data is not None else {}

# Προσθήκη GAME_DATA_JSON path
GAME_DATA_JSON = os.path.join(paths_config.DATA_DIR, "game_data.json")

# Φόρτωση νέας δομής δεδομένων
GAME_DATA = load_json_data(GAME_DATA_JSON, {
    "champions": {
    },
    "spells": {
    },
    "teams": []
})

# Φόρτωση δεδομένων από τη νέα δομή
CHAMPIONS = list(GAME_DATA.get("champions", {}).keys())
TEAMS = GAME_DATA.get("teams", ["BLUE", "PURPLE"])
SUMMONER_SPELLS = list(GAME_DATA.get("spells", {}).keys())

# Φόρτωση skins από τη νέα δομή - όλα τα skins από όλους τους champions
SKINS = []
SKINS_DICT = {}
for champion_name, champion_data in GAME_DATA.get("champions", {}).items():
    skins = champion_data.get("skins", {})
    SKINS_DICT.update(skins)
    SKINS.extend(skins.keys())

# Αφαίρεση διπλότυπων και ταξινόμηση
SKINS = sorted(list(set(SKINS)))
DEFAULT_SKIN = "Classic"

# Φόρτωση AI difficulty settings
AI_SETTINGS = load_json_data(paths_config.AI_DIFFICULTY_JSON, {
    "levels": {"Easy": 1, "Medium": 2, "Hard": 3},
    "default_difficulty": "Easy"
})
AI_DIFFICULTIES = AI_SETTINGS.get("levels", {"Easy": 1})
AI_DIFFICULTY_OPTIONS = list(AI_DIFFICULTIES.keys())
DEFAULT_AI_DIFFICULTY = AI_SETTINGS.get("default_difficulty", "Easy")

# Φόρτωση Game Settings
GAME_SETTINGS_DATA = load_json_data(paths_config.GAME_SETTINGS_JSON, {
    "game_modes": ["Classic", "ARAM", "URF", "One for All"],
    "maps": ["Summoner's Rift", "Howling Abyss", "Twisted Treeline"],
    "player_counts": ["1v1", "2v2", "3v3", "4v4", "5v5", "6v6", "Custom"],
    "player_limits": {
        "1v1": 2,
        "2v2": 4,
        "3v3": 6,
        "4v4": 8,
        "5v5": 10,
        "6v6": 12,
        "Custom": 0
    },
    "default_game_mode": "Classic",
    "default_map": "Summoner's Rift",
    "default_player_count": "5v5"
})
GAME_MODES = GAME_SETTINGS_DATA.get("game_modes", ["Classic", "ARAM", "URF", "One for All"])
MAPS = GAME_SETTINGS_DATA.get("maps", ["Summoner's Rift", "Howling Abyss", "Twisted Treeline"])
PLAYER_COUNT_OPTIONS = GAME_SETTINGS_DATA.get("player_counts", ["1v1", "2v2", "3v3", "4v4", "5v5", "6v6", "Custom"])
PLAYER_COUNT_LIMITS = GAME_SETTINGS_DATA.get("player_limits", {
    "1v1": 2, "2v2": 4, "3v3": 6, "4v4": 8, "5v5": 10, "6v6": 12, "Custom": 0
})
DEFAULT_GAME_MODE = GAME_SETTINGS_DATA.get("default_game_mode", "Classic")
DEFAULT_MAP = GAME_SETTINGS_DATA.get("default_map", "Summoner's Rift")
DEFAULT_PLAYER_COUNT = GAME_SETTINGS_DATA.get("default_player_count", "5v5")

# Φόρτωση Paths Configuration
PATHS_CONFIG = load_json_data(paths_config.PATHS_JSON, {
    "server_path": "",
    "league_path": "",
    "game_port": 8394
})
SERVER_PATH = PATHS_CONFIG.get("server_path", "")
LEAGUE_PATH = PATHS_CONFIG.get("league_path", "")
GAME_PORT = PATHS_CONFIG.get("game_port", 8394)

# Runes Editor Executable
RUNES_EDITOR_EXE = paths_config.RUNES_EDITOR_EXE
RUNES_JSON = os.path.join(paths_config.DATA_DIR, "runes.json")

# Χρήση των paths από το paths_config
GAMEINFO_PATH = paths_config.GAMEINFO_JSON
BAT_OUTPUT_PATH = paths_config.CONNECT_BAT
HISTORY_FILE = paths_config.HISTORY_JSON

# ΝΕΕΣ ΣΥΝΑΡΤΗΣΕΙΣ ΜΕΤΑΤΡΟΠΗΣ για τη νέα δομή
def get_champion_id(champion_name):
    """Μετατροπή champion name σε ID από τη νέα δομή"""
    champions = GAME_DATA.get("champions", {})
    if champion_name in champions:
        return champions[champion_name].get("champion_id", 1)
    return 1

def get_skin_id(skin_name):
    """Μετατροπή skin name σε ID από τη νέα δομή"""
    # Ψάχνουμε σε όλους τους champions για το skin
    champions = GAME_DATA.get("champions", {})
    for champion_data in champions.values():
        skins = champion_data.get("skins", {})
        if skin_name in skins:
            return skins[skin_name]
    return 0

def get_spell_id(spell_name):
    """Μετατροπή spell name σε ID από τη νέα δομή"""
    spells = GAME_DATA.get("spells", {})
    if spell_name in spells:
        return spells[spell_name].get("spell_id", 1)
    return 1

def get_game_mode_id(game_mode_name):
    """Μετατροπή game mode name σε ID"""
    if game_mode_name in GAME_MODES and GAME_MODE_IDS:
        index = GAME_MODES.index(game_mode_name)
        if index < len(GAME_MODE_IDS):
            return GAME_MODE_IDS[index]
    return GAME_MODE_IDS[0] if GAME_MODE_IDS else 1

def get_map_id(map_name):
    """Μετατροπή map name σε ID"""
    if map_name in MAPS and MAP_IDS:
        index = MAPS.index(map_name)
        if index < len(MAP_IDS):
            return MAP_IDS[index]
    return MAP_IDS[0] if MAP_IDS else 1

# Πρέπει να διατηρήσουμε αυτές τις μεταβλητές για συμβατότητα
# αλλά τώρα θα είναι κενές λίστες αφού τα δεδομένα έρχονται από το game_data.json
CHAMPION_IDS = []
SKIN_IDS = []
SUMMONER_SPELL_IDS = []
GAME_MODE_IDS = load_json_data(paths_config.GAME_MODE_IDS_JSON, [1, 2, 3, 4])
MAP_IDS = load_json_data(paths_config.MAP_IDS_JSON, [1, 2, 3])