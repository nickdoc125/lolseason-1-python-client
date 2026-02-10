import os
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from paths_config import paths_config
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

class ServerManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Children of the Grave Server Manager")
        self.root.geometry("700x650")
        self.root.configure(bg=DARK_THEME['bg_dark'])
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ SERVER MANAGER
        self.center_window(self.root)
        
        # Ορισμός διαδρομών για τα .bat αρχεία από το paths_config
        from paths_config import paths_config
        self.bat_files = {
            'update': paths_config.UPDATE_SERVER_BAT,
            'compile': paths_config.COMPILE_SERVER_BAT, 
            'download': paths_config.DOWNLOAD_CLIENT_DATA_BAT,
            'extract': paths_config.EXTRACT_CLIENT_DATA_BAT
        }
        
        # Variables
        self.progress_var = tk.DoubleVar()
        self.progress_text = tk.StringVar()
        self.status_var = tk.StringVar()
        
        # Initial values
        self.progress_text.set("Waiting...")
        self.status_var.set("Waiting for action...")
        
        self.create_widgets()
    
    def center_window(self, window):
        """Κεντράρισμα παραθύρου στην οθόνη"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def create_widgets(self):
        # Header
        tk.Label(self.root, text="Children of the Grave Server Manager", 
                font=("Arial", 16, "bold"),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(pady=10)
        
        tk.Label(self.root, text="Installation and Compilation Management", 
                font=("Arial", 10),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_secondary']).pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg=DARK_THEME['bg_dark'])
        button_frame.pack(pady=20)
        
        self.update_btn = tk.Button(button_frame, text="Update Server", 
                                   font=("Arial", 12), width=20, height=2,
                                   command=self.update_server,
                                   bg=DARK_THEME['accent'], fg="white",
                                   cursor="hand2")
        self.update_btn.grid(row=0, column=0, padx=10, pady=10)
        
        self.compile_btn = tk.Button(button_frame, text="Compile Server", 
                                    font=("Arial", 12), width=20, height=2,
                                    command=self.compile_server,
                                    bg=DARK_THEME['success'], fg="white",
                                    cursor="hand2")
        self.compile_btn.grid(row=0, column=1, padx=10, pady=10)
        
        self.download_btn = tk.Button(button_frame, text="Download Client Data", 
                                     font=("Arial", 12), width=20, height=2,
                                     command=self.download_client_data,
                                     bg=DARK_THEME['warning'], fg="white",
                                     cursor="hand2")
        self.download_btn.grid(row=1, column=0, padx=10, pady=10)
        
        self.extract_btn = tk.Button(button_frame, text="Extract Client Data", 
                                    font=("Arial", 12), width=20, height=2,
                                    command=self.extract_client_data,
                                    bg=DARK_THEME['accent'], fg="white",
                                    cursor="hand2")
        self.extract_btn.grid(row=1, column=1, padx=10, pady=10)
        
        # Progress
        tk.Label(self.root, textvariable=self.progress_text, 
                font=("Arial", 10),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(pady=5)
        
        progress_bar = ttk.Progressbar(self.root, variable=self.progress_var, 
                       maximum=100)
        progress_bar.pack(fill="x", padx=50, pady=5)
        
        # Log
        tk.Label(self.root, text="Log Output:", 
                font=("Arial", 10, "bold"),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(anchor="w", padx=50)
        
        self.log_text = tk.Text(self.root, height=15, width=80,
                              bg=DARK_THEME['bg_light'], fg=DARK_THEME['text_primary'],
                              insertbackground=DARK_THEME['text_primary'])
        self.log_text.pack(padx=50, pady=10, fill="both", expand=True)
        
        # Status
        tk.Label(self.root, textvariable=self.status_var, 
                relief="sunken", anchor="w",
                bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).pack(fill="x", side="bottom")
    
    def log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        self.root.update()
    
    def check_bat_file(self, bat_type):
        bat_path = self.bat_files[bat_type]
        if not os.path.exists(bat_path):
            error_msg = f"File not found: {bat_path}"
            self.log(f"ERROR: {error_msg}")
            messagebox.showerror("Error", error_msg)
            return False
        return True
    
    def run_bat_file(self, bat_type, action_name):
        if not self.check_bat_file(bat_type):
            return
            
        self.disable_buttons()
        self.progress_text.set(f"Running {action_name}...")
        self.status_var.set(f"Running {action_name}...")
        
        def thread_function():
            try:
                from paths_config import paths_config
                script_dir = paths_config.BASE_DIR
                os.chdir(script_dir)
                
                bat_path = self.bat_files[bat_type]
                
                self.log(f"Starting {action_name}...")
                self.log(f"Executing: {bat_path}")
                self.log(f"Working directory: {script_dir}")
                self.log("-" * 50)
                
                if os.name == 'nt':
                    process = subprocess.Popen(
                        f'"{bat_path}"',
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        encoding='utf-8',
                        errors='replace',
                        shell=True
                    )
                else:
                    process = subprocess.Popen(
                        [bat_path],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                        universal_newlines=True,
                        encoding='utf-8',
                        errors='replace'
                    )
                
                for line in process.stdout:
                    if line.strip():
                        self.log(line.strip())
                
                process.wait()
                
                if process.returncode == 0:
                    success_msg = f"{action_name} completed successfully!"
                    self.log(success_msg)
                    messagebox.showinfo("Success", success_msg)
                else:
                    error_msg = f"{action_name} failed with exit code {process.returncode}"
                    self.log(error_msg)
                    messagebox.showerror("Error", error_msg)
                    
            except FileNotFoundError:
                error_msg = f"File not found: {self.bat_files[bat_type]}"
                self.log(error_msg)
                messagebox.showerror("Error", error_msg)
            except Exception as e:
                error_msg = f"Unexpected error during {action_name}: {e}"
                self.log(error_msg)
                messagebox.showerror("Error", error_msg)
            finally:
                self.enable_buttons()
                self.progress_text.set("Completed")
                self.status_var.set("Ready")
        
        thread = threading.Thread(target=thread_function)
        thread.daemon = True
        thread.start()
    
    def disable_buttons(self):
        self.update_btn.config(state="disabled")
        self.compile_btn.config(state="disabled")
        self.download_btn.config(state="disabled")
        self.extract_btn.config(state="disabled")
    
    def enable_buttons(self):
        self.update_btn.config(state="normal")
        self.compile_btn.config(state="normal")
        self.download_btn.config(state="normal")
        self.extract_btn.config(state="normal")
    
    def update_server(self):
        self.run_bat_file('update', "Server Update")
    
    def compile_server(self):
        self.run_bat_file('compile', "Server Compilation")
    
    def download_client_data(self):
        self.run_bat_file('download', "Client Data Download")
    
    def extract_client_data(self):
        self.run_bat_file('extract', "Client Data Extraction")

def gui_main():
    root = tk.Tk()
    app = ServerManagerGUI(root)
    root.mainloop()

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def run_bat_from_cli(bat_filename, action_name):
    """Εκτελεί αρχείο .bat από command line"""
    from paths_config import paths_config
    
    print(f"Starting {action_name}...")
    print(f"Executing: {bat_filename}")
    print(f"Working directory: {paths_config.BASE_DIR}")
    print("-" * 50)
    
    try:
        # Αλλαγή στον φάκελο του script
        os.chdir(paths_config.BASE_DIR)
        
        # Έλεγχος ύπαρξης αρχείου
        if not os.path.exists(bat_filename):
            print(f"Error: File not found: {bat_filename}")
            return False
        
        # Εκτέλεση του .bat αρχείου
        if os.name == 'nt':  # Windows
            result = subprocess.run(
                f'"{bat_filename}"',
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                shell=True
            )
        else:  # Linux/Mac
            result = subprocess.run(
                [bat_filename],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
        
        # Εκτύπωση εξόδου
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("Errors:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"{action_name} completed successfully!")
            return True
        else:
            print(f"{action_name} failed with exit code {result.returncode}")
            return False
            
    except FileNotFoundError:
        print(f"Error: File not found: {bat_filename}")
        return False
    except Exception as e:
        print(f"Error during {action_name}: {e}")
        return False

def main():
    """Κύρια συνάρτηση dispatcher"""
    from paths_config import paths_config
    
    # Ορισμός διαδρομών για τα .bat αρχεία από το paths_config
    bat_files = {
        'compile': paths_config.COMPILE_SERVER_BAT,
        'download': paths_config.DOWNLOAD_CLIENT_DATA_BAT,
        'extract': paths_config.EXTRACT_CLIENT_DATA_BAT,
        'update': paths_config.UPDATE_SERVER_BAT
    }
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "compile":
            success = run_bat_from_cli(bat_files['compile'], "Server Compilation")
            sys.exit(0 if success else 1)
        elif command == "download":
            success = run_bat_from_cli(bat_files['download'], "Client Data Download")
            sys.exit(0 if success else 1)
        elif command == "extract":
            success = run_bat_from_cli(bat_files['extract'], "Client Data Extraction")
            sys.exit(0 if success else 1)
        elif command == "update":
            success = run_bat_from_cli(bat_files['update'], "Server Update")
            sys.exit(0 if success else 1)
        elif command == "gui":
            gui_main()
        else:
            print("Available commands:")
            print("  compile  - Compile the server")
            print("  download - Download client data")
            print("  extract  - Extract client data")
            print("  update   - Update server from git")
            print("  gui      - Launch GUI (default)")
            sys.exit(1)
    else:
        # Default to GUI
        gui_main()

if __name__ == "__main__":
    main()