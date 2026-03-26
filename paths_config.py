import os
import sys
import json

# ===================== BASE PATHS CONFIGURATION =====================
class PathsConfig:
    def __init__(self):
        # Προσδιορισμός base directory
        if getattr(sys, 'frozen', False):
            # Εκτελείται ως exe
            self.BASE_DIR = os.path.dirname(sys.executable)
        else:
            # Εκτελείται ως script
            self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            
        self.DATA_DIR = os.path.join(self.BASE_DIR, "data")
        self.OUTPUT_DIR = os.path.join(self.BASE_DIR, "Fishbones_Data", "ChildrenOfTheGrave-Gameserver", "ChildrenOfTheGraveServerConsole", "bin", "Debug", "net10.0", "Settings")
        self.TOOLS_DIR = os.path.join(self.BASE_DIR, "tools")
        
        # Δημιουργία φακέλων αν δεν υπάρχουν
        os.makedirs(self.DATA_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)
        os.makedirs(self.TOOLS_DIR, exist_ok=True)
        
        # ΚΕΝΤΡΙΚΟ ΑΡΧΕΙΟ ΔΕΔΟΜΕΝΩΝ - Νέα δομή
        self.GAME_DATA_JSON = os.path.join(self.DATA_DIR, "game_data.json")
        
        # Configuration Files
        self.AI_DIFFICULTY_JSON = os.path.join(self.DATA_DIR, "ai_difficulty.json")
        self.GAME_SETTINGS_JSON = os.path.join(self.DATA_DIR, "game_settings.json")
        self.PATHS_JSON = os.path.join(self.DATA_DIR, "paths.json")
        self.HISTORY_JSON = os.path.join(self.DATA_DIR, "lobby_history.json")
        
        # Game Mode και Map IDs (ακόμα χρειάζονται)
        self.GAME_MODE_IDS_JSON = os.path.join(self.DATA_DIR, "game_mode_ids.json")
        self.MAP_IDS_JSON = os.path.join(self.DATA_DIR, "map_ids.json")
        
        # Output Files
        self.GAMEINFO_JSON = os.path.join(self.OUTPUT_DIR, "gameinfo.json")
        self.CONNECT_BAT = os.path.join(self.BASE_DIR, "connect.bat")
        
        # Runes Editor Executable
        self.RUNES_EDITOR_EXE = os.path.join(self.DATA_DIR, "runes", "Runes Calculator.exe")
        
        # Server Management BAT Files - ΟΛΑ ΤΑ BAT ΑΡΧΕΙΑ
        self.UPDATE_SERVER_BAT = os.path.join(self.TOOLS_DIR, "update_server.bat")
        self.COMPILE_SERVER_BAT = os.path.join(self.TOOLS_DIR, "compile_server.bat")
        self.DOWNLOAD_CLIENT_DATA_BAT = os.path.join(self.TOOLS_DIR, "download_client_data.bat")
        self.EXTRACT_CLIENT_DATA_BAT = os.path.join(self.TOOLS_DIR, "extract_client_data.bat")
        
        # Smart Select Data Paths
        self.SMART_SELECT_BASE_PATH = os.path.join(self.BASE_DIR, "Fishbones_Data", "playable_client_126", "DATA")
        self.SMART_SELECT_CHAMPIONS_PATH = os.path.join(self.SMART_SELECT_BASE_PATH, "Characters")
        self.SMART_SELECT_SPELLS_PATH = os.path.join(self.SMART_SELECT_BASE_PATH, "Spells", "Icons2D")

# Create global instance
paths_config = PathsConfig()
