import tkinter as tk
from tkinter import ttk, messagebox
import socket
import threading
from server import run_server, is_port_in_use
from client_gui import LobbyClient
from server_gui import ServerManagerGUI
from history_manager import load_history, add_ip_to_history
from config import DARK_THEME

class LobbyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Lobby - Host or Join")
        self.root.geometry("500x620")  # ΜΕΙΩΣΗ ύψους αφού αφαιρέσαμε το network info
        self.root.configure(bg=DARK_THEME['bg_dark'])
        
        # ΚΕΝΤΡΑΡΙΣΜΟΣ ΤΟΥ ΚΥΡΙΟΥ ΠΑΡΑΘΥΡΟΥ
        self.center_window(self.root)
        
        # Προσθήκη protocol για σωστό κλείσιμο
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        main_frame = tk.Frame(root, padx=20, pady=20, bg=DARK_THEME['bg_dark'])
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(main_frame, text="Game Lobby", font=("Arial", 16, "bold"),
                bg=DARK_THEME['bg_dark'], fg=DARK_THEME['text_primary']).pack(pady=20)
        
        # Host section
        host_frame = tk.LabelFrame(main_frame, text="Host Game", padx=10, pady=10,
                                 bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'])
        host_frame.pack(fill="x", pady=10)
        
        tk.Label(host_frame, text="Select IP Address:", 
                bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).pack(anchor="w")
        
        # Frame για combobox και copy button
        ip_selection_frame = tk.Frame(host_frame, bg=DARK_THEME['bg_medium'])
        ip_selection_frame.pack(fill="x", pady=5)
        
        # Λήψη όλων των IP διευθύνσεων με adapter names
        all_ips = self.get_all_ips_with_friendly_names()
        
        self.host_ip_var = tk.StringVar(value=all_ips[0] if all_ips else "127.0.0.1 (Loopback)")
        self.ip_combo = ttk.Combobox(ip_selection_frame, textvariable=self.host_ip_var, 
                                   values=all_ips, state="readonly", width=42)
        self.ip_combo.pack(side="left", fill="x", expand=True)
        
        # Copy IP button (πολύ μικρό με εικονίδιο)
        self.copy_ip_button = tk.Button(ip_selection_frame, text="📋", 
                                      command=self.copy_selected_ip,
                                      font=("Arial", 8),
                                      width=2,
                                      height=1,
                                      bg=DARK_THEME['accent'],
                                      fg="white",
                                      relief="flat",
                                      bd=1,
                                      cursor="hand2")
        self.copy_ip_button.pack(side="right", padx=(5, 0))
        
        # Refresh IPs button
        refresh_frame = tk.Frame(host_frame, bg=DARK_THEME['bg_medium'])
        refresh_frame.pack(fill="x", pady=5)
        
        tk.Button(refresh_frame, text="🔄 Refresh IPs", command=self.refresh_ips,
                 font=("Arial", 8), bg=DARK_THEME['accent'], fg="white",
                 cursor="hand2").pack(side="left")
        
        # Έλεγχος αν ο server είναι ήδη ενεργός
        server_status = "🟢 Server is RUNNING" if is_port_in_use(5000) else "🔴 Server is STOPPED"
        self.server_status_label = tk.Label(host_frame, text=server_status, 
                                          font=("Arial", 9, "bold"),
                                          fg="green" if "RUNNING" in server_status else "red",
                                          bg=DARK_THEME['bg_medium'])
        self.server_status_label.pack(anchor="w", pady=2)
        
        host_button = tk.Button(host_frame, text="Start Server", command=self.host_game,
                               bg=DARK_THEME['success'], fg="white", font=("Arial", 10, "bold"),
                               cursor="hand2")
        host_button.pack(pady=5, fill="x")
        
        # Join section
        join_frame = tk.LabelFrame(main_frame, text="Join Game", padx=10, pady=10,
                                 bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'])
        join_frame.pack(fill="x", pady=10)
        
        tk.Label(join_frame, text="Server IP:",
                bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary']).pack(anchor="w")
        
        # Frame για join combobox και copy button
        join_ip_frame = tk.Frame(join_frame, bg=DARK_THEME['bg_medium'])
        join_ip_frame.pack(fill="x", pady=5)
        
        # IP history
        history = load_history()
        self.join_ip_var = tk.StringVar()
        join_ip_combo = ttk.Combobox(join_ip_frame, textvariable=self.join_ip_var, 
                                   values=history["ips"], width=20)
        join_ip_combo.pack(side="left", fill="x", expand=True)
        
        # Copy Join IP button
        self.copy_join_ip_button = tk.Button(join_ip_frame, text="📋", 
                                           command=self.copy_join_ip,
                                           font=("Arial", 8),
                                           width=2,
                                           height=1,
                                           bg=DARK_THEME['accent'],
                                           fg="white",
                                           relief="flat",
                                           bd=1,
                                           cursor="hand2")
        self.copy_join_ip_button.pack(side="right", padx=(5, 0))
        
        join_button = tk.Button(join_frame, text="Join Server", command=self.join_game,
                              bg=DARK_THEME['accent'], fg="white", font=("Arial", 10, "bold"),
                              cursor="hand2")
        join_button.pack(pady=5, fill="x")
        
        # Server Manager Button
        manager_frame = tk.LabelFrame(main_frame, text="Server Management", padx=10, pady=10,
                                    bg=DARK_THEME['bg_medium'], fg=DARK_THEME['text_primary'])
        manager_frame.pack(fill="x", pady=10)
        
        manager_button = tk.Button(manager_frame, text="Open Server Manager", command=self.open_server_manager,
                                 bg=DARK_THEME['warning'], fg="white", font=("Arial", 10, "bold"),
                                 cursor="hand2")
        manager_button.pack(pady=5, fill="x")
        
        # ΑΦΑΙΡΕΣΗ NETWORK INFO SECTION - ΣΒΗΣΤΟ ΟΛΟΚΛΗΡΟ ΤΟ ΤΜΗΜΑ ΑΥΤΟ
        # Δεν χρειάζεται πλέον το Network Information frame
        
        # Status
        self.status_label = tk.Label(main_frame, text="", fg="gray", bg=DARK_THEME['bg_dark'])
        self.status_label.pack(pady=10)
        
        self.server_thread = None
        
        # Δεν χρειάζεται πλέον η κλήση update_network_info()
        # self.update_network_info()

    def center_window(self, window):
        """Κεντράρισμα παραθύρου στην οθόνη"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry('{}x{}+{}+{}'.format(width, height, x, y))

    def get_all_ips_with_friendly_names(self):
        """Επιστρέφει όλες τις IP διευθύνσεις του συστήματος με φιλικά ονόματα adapters"""
        ips_with_names = []
        
        try:
            # Προσθήκη της loopback διεύθυνσης
            ips_with_names.append("127.0.0.1 (Loopback)")
            
            # Προσπάθεια χρήσης psutil για φιλικά ονόματα
            try:
                import psutil
                
                # Λήψη όλων των δικτυακών διεπαφών
                net_ifs = psutil.net_if_addrs()
                
                for adapter_name, addresses in net_ifs.items():
                    for addr in addresses:
                        if addr.family == socket.AF_INET:  # IPv4 addresses only
                            ip = addr.address
                            if ip and ip != "127.0.0.1":
                                # Προσθήκη στη λίστα με το φιλικό όνομα του adapter
                                display_text = f"{ip} - {adapter_name}"
                                ips_with_names.append(display_text)
                                
            except ImportError:
                # Fallback αν δεν υπάρχει το psutil - χρήση netifaces
                print("psutil not available, using netifaces fallback")
                try:
                    import netifaces
                    interfaces = netifaces.interfaces()
                    
                    for interface in interfaces:
                        try:
                            addrs = netifaces.ifaddresses(interface)
                            if netifaces.AF_INET in addrs:
                                for addr_info in addrs[netifaces.AF_INET]:
                                    ip = addr_info.get('addr')
                                    if ip and ip != "127.0.0.1":
                                        # Χρήση του interface name ως fallback
                                        display_text = f"{ip} - {interface}"
                                        ips_with_names.append(display_text)
                        except:
                            continue
                except ImportError:
                    print("netifaces also not available")
            
            # Προσθήκη της κύριας IP με socket method (τελευταίο fallback)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                main_ip = s.getsockname()[0]
                s.close()
                
                # Έλεγχος αν η IP υπάρχει ήδη στη λίστα
                ip_exists = False
                for existing_ip in ips_with_names:
                    if main_ip in existing_ip:
                        ip_exists = True
                        break
                
                if not ip_exists and main_ip != "127.0.0.1":
                    ips_with_names.append(f"{main_ip} (Primary)")
            except:
                pass
                
        except Exception as e:
            print(f"Error getting IPs: {e}")
            # Fallback - προσθήκη μόνο της loopback
            ips_with_names = ["127.0.0.1 (Loopback)"]
        
        # Αφαίρεση διπλότυπων και ταξινόμηση
        unique_ips = []
        for ip in ips_with_names:
            if ip not in unique_ips:
                unique_ips.append(ip)
        
        # Ταξινόμηση: πρώτα οι μη-loopback, μετά η loopback
        non_loopback = [ip for ip in unique_ips if "127.0.0.1" not in ip]
        loopback = [ip for ip in unique_ips if "127.0.0.1" in ip]
        
        return non_loopback + loopback

    def get_clean_ip(self, ip_string):
        """Εξάγει την καθαρή IP από string με adapter name"""
        if " - " in ip_string:
            return ip_string.split(" - ")[0].strip()
        elif " (" in ip_string:
            return ip_string.split(" (")[0].strip()
        return ip_string

    def copy_selected_ip(self):
        """Αντιγραφή της επιλεγμένης IP στο clipboard"""
        selected_ip_display = self.host_ip_var.get()
        clean_ip = self.get_clean_ip(selected_ip_display)
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(clean_ip)
            self.root.update()  # Κρατάει το clipboard ανοιχτό
            
            # Προσωρινή αλλαγή του κουμπιού για feedback
            original_text = self.copy_ip_button.cget('text')
            self.copy_ip_button.config(text="✅", bg=DARK_THEME['success'])
            self.status_label.config(text=f"Copied: {clean_ip}", fg="green")
            
            # Επαναφορά μετά από 1.5 δευτερόλεπτα
            self.root.after(1500, lambda: self.copy_ip_button.config(text=original_text, bg=DARK_THEME['accent']))
            self.root.after(2000, lambda: self.status_label.config(text=""))
            
        except Exception as e:
            self.status_label.config(text=f"Copy failed: {e}", fg="red")
            self.root.after(2000, lambda: self.status_label.config(text=""))

    def copy_join_ip(self):
        """Αντιγραφή της join IP στο clipboard"""
        join_ip = self.join_ip_var.get().strip()
        if not join_ip:
            self.status_label.config(text="No IP to copy", fg="orange")
            self.root.after(2000, lambda: self.status_label.config(text=""))
            return
            
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(join_ip)
            self.root.update()
            
            # Προσωρινή αλλαγή του κουμπιού για feedback
            original_text = self.copy_join_ip_button.cget('text')
            self.copy_join_ip_button.config(text="✅", bg=DARK_THEME['success'])
            self.status_label.config(text=f"Copied: {join_ip}", fg="green")
            
            # Επαναφορά μετά από 1.5 δευτερόλεπτα
            self.root.after(1500, lambda: self.copy_join_ip_button.config(text=original_text, bg=DARK_THEME['accent']))
            self.root.after(2000, lambda: self.status_label.config(text=""))
            
        except Exception as e:
            self.status_label.config(text=f"Copy failed: {e}", fg="red")
            self.root.after(2000, lambda: self.status_label.config(text=""))

    def refresh_ips(self):
        """Ανανέωση της λίστας IP διευθύνσεων"""
        all_ips = self.get_all_ips_with_friendly_names()
        self.ip_combo['values'] = all_ips
        if all_ips:
            self.host_ip_var.set(all_ips[0])
        # Δεν χρειάζεται πλέον: self.update_network_info()
        self.status_label.config(text="IP list refreshed", fg="green")
        self.root.after(2000, lambda: self.status_label.config(text=""))

    def host_game(self):
        # Έλεγχος αν ο server είναι ήδη ενεργός
        if is_port_in_use(5000):
            messagebox.showinfo("Server Already Running", 
                              "The server is already running!\n\n"
                              "You can join the existing server or use the Server Manager to stop it.", parent=self.root)
            return
        
        selected_ip_display = self.host_ip_var.get()
        clean_ip = self.get_clean_ip(selected_ip_display)
        
        try:
            # Start server in background thread
            self.server_thread = threading.Thread(target=run_server, args=(clean_ip,), daemon=True)
            self.server_thread.start()
            
            # Προσθήκη IP στο history
            add_ip_to_history(clean_ip)
            
            # Open client window as host
            self.open_client_window(clean_ip)
            
            # Ενημέρωση status
            self.server_status_label.config(text="🟢 Server is RUNNING", fg="green")
            self.status_label.config(text=f"Server started on all network interfaces", fg="green")
            
        except Exception as e:
            messagebox.showerror("Error", f"Cannot start server: {e}", parent=self.root)

    def join_game(self):
        server_ip = self.join_ip_var.get().strip()
        if not server_ip:
            messagebox.showwarning("Warning", "Please enter server IP", parent=self.root)
            return
            
        try:
            # Προσθήκη IP στο history
            add_ip_to_history(server_ip)
            
            # Open client window as client
            self.open_client_window(server_ip)
            self.status_label.config(text="Connecting...", fg="blue")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot connect to server: {e}", parent=self.root)

    def open_client_window(self, host_ip):
        try:
            client_window = tk.Toplevel(self.root)
            client_window.title("Game Lobby - Champion Select")
            
            # ΠΡΟΣΘΗΚΗ: Ορισμός ως transient του κύριου παραθύρου
            client_window.transient(self.root)
            
            LobbyClient(client_window, host_ip)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open client window: {e}", parent=self.root)

    def open_server_manager(self):
        """Ανοίγει το Server Manager GUI"""
        try:
            manager_window = tk.Toplevel(self.root)
            manager_window.title("Server Manager")
            
            # ΠΡΟΣΘΗΚΗ: Ορισμός ως transient του κύριου παραθύρου
            manager_window.transient(self.root)
            
            ServerManagerGUI(manager_window)
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open server manager: {e}", parent=self.root)

    def on_close(self):
        """Χειρίζεται το κλείσιμο του παραθύρου"""
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = LobbyApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")