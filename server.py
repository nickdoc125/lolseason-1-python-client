import asyncio
import websockets
import json
import random
import string
import os
from config import PORT, CHAMPIONS, TEAMS, SUMMONER_SPELLS, DEFAULT_SKIN, DEFAULT_GAME_MODE, DEFAULT_MAP, RUNES_JSON, DEFAULT_PLAYER_COUNT, PLAYER_COUNT_LIMITS
from config import get_champion_id, get_skin_id, get_spell_id

# ===================== WEBSOCKET SERVER =====================
clients = {}   # {websocket: {"name": str, "ready": bool, "champion": str, "team": str, "skin": str, "spell1": str, "spell2": str, "runes": dict, "talents": dict}}
host_connection = None  # Θα αποθηκεύει τη σύνδεση του host
bots = {}  # {bot_name: bot_data}

# Game settings
game_settings = {
    "game_mode": DEFAULT_GAME_MODE,
    "map": DEFAULT_MAP,
    "player_count": DEFAULT_PLAYER_COUNT,
    "manacosts": True,
    "cooldowns": True,
    "cheats": False,
    "minion_spawns": True
}

# Global server instance
server_instance = None

def load_shared_runes_and_talents():
    """Φόρτωση κοινών runes και talents από το runes.json για bots"""
    try:
        if os.path.exists(RUNES_JSON):
            with open(RUNES_JSON, 'r', encoding='utf-8') as f:
                runes_data = json.load(f)
            
            if isinstance(runes_data, dict):
                runes = runes_data.get("runes", {})
                talents = runes_data.get("talents", {})
                
                if not runes:
                    runes = generate_default_runes()
                if not talents:
                    talents = generate_default_talents()
                    
                return runes, talents
                
    except Exception as e:
        print(f"Error loading shared runes and talents: {e}")
    
    return generate_default_runes(), generate_default_talents()

def generate_default_runes():
    """Δημιουργία default runes"""
    runes = {}
    for i in range(1, 31):
        runes[str(i)] = 5260
    return runes

def generate_default_talents():
    """Δημιουργία default talents"""
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

def generate_players_data():
    """Δημιουργεί τα player data με IDs και keys που θα χρησιμοποιηθούν από ΟΛΟΥΣ"""
    all_players = list(clients.values()) + list(bots.values())
    processed_players = []
    
    player_id = 1
    bot_id = -1
    
    for player in all_players:
        player_data = player.copy()
        
        if player_data.get("is_bot", False):
            player_data["playerId"] = bot_id
            bot_id -= 1
        else:
            player_data["playerId"] = player_id
            player_id += 1
        
        chars = string.ascii_letters + string.digits
        player_data["blowfishKey"] = ''.join(random.choice(chars) for _ in range(22)) + "=="
        
        player_data["champion"] = get_champion_id(player_data.get("champion", ""))
        player_data["skin"] = get_skin_id(player_data.get("skin", DEFAULT_SKIN))
        
        player_data["summoner1"] = get_spell_id(player_data.get("spell1", ""))
        player_data["summoner2"] = get_spell_id(player_data.get("spell2", ""))
        
        if "spell1" in player_data:
            del player_data["spell1"]
        if "spell2" in player_data:
            del player_data["spell2"]
        
        player_runes = player_data.get("runes", {})
        player_talents = player_data.get("talents", {})
        
        if not player_runes or not player_talents:
            loaded_runes, loaded_talents = load_shared_runes_and_talents()
            if not player_runes:
                player_runes = loaded_runes
            if not player_talents:
                player_talents = loaded_talents
        
        player_data.update({
            "rank": "UNRANKED",
            "ribbon": 0,
            "icon": 0,
            "runes": player_runes,
            "talents": player_talents
        })
        
        if "talent" in player_data:
            del player_data["talent"]
        
        processed_players.append(player_data)
    
    return processed_players

async def broadcast(data):
    """Στέλνει σε όλους τους clients δεδομένα"""
    msg = json.dumps(data)
    disconnected = []
    
    for websocket in list(clients.keys()):
        try:
            await websocket.send(msg)
        except:
            disconnected.append(websocket)
    
    for ws in disconnected:
        if ws in clients:
            del clients[ws]

async def broadcast_lobby():
    """Στέλνει την τρέχουσα λίστα παικτών και ρυθμίσεις"""
    all_players = list(clients.values()) + list(bots.values())
    
    all_ready = all_players and all(p.get("ready", False) for p in all_players)
    
    data = {
        "type": "lobby_update",
        "players": all_players,
        "is_host": False,
        "game_settings": game_settings
    }
    
    disconnected = []
    
    for websocket, info in clients.items():
        try:
            if websocket == host_connection:
                host_data = data.copy()
                host_data["is_host"] = True
                await websocket.send(json.dumps(host_data))
                
                if all_ready:
                    await websocket.send(json.dumps({
                        "type": "all_players_ready",
                        "all_ready": True
                    }))
            else:
                await websocket.send(json.dumps(data))
        except:
            disconnected.append(websocket)
    
    for ws in disconnected:
        if ws in clients:
            del clients[ws]

async def handle_client(websocket):
    """Χειρίζεται έναν client connection (χωρίς path argument)"""
    global host_connection
    
    try:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "join":
                current_limit = PLAYER_COUNT_LIMITS.get(game_settings.get("player_count", "5v5"), 10)
                if current_limit > 0:
                    total_players = len(clients) + len(bots)
                    if total_players >= current_limit:
                        try:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": f"Cannot join: Player limit reached ({current_limit} players)"
                            }))
                            await websocket.close()
                            continue
                        except:
                            pass
                
                if host_connection is None:
                    host_connection = websocket
                
                default_champion = CHAMPIONS[0] if CHAMPIONS else ""
                default_team = TEAMS[0] if TEAMS else ""
                default_spell1 = SUMMONER_SPELLS[0] if SUMMONER_SPELLS else ""
                default_spell2 = SUMMONER_SPELLS[1] if len(SUMMONER_SPELLS) > 1 else ""
                
                clients[websocket] = {
                    "name": data["name"], 
                    "ready": False,
                    "champion": data.get("champion", default_champion),
                    "team": data.get("team", default_team),
                    "skin": data.get("skin", DEFAULT_SKIN),
                    "spell1": data.get("spell1", default_spell1),
                    "spell2": data.get("spell2", default_spell2),
                    "runes": data.get("runes", {}),
                    "talents": data.get("talents", {})
                }
                
                await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"{data['name']} joined the lobby"})
                await broadcast_lobby()
                
                total_players = len(clients) + len(bots)
                if current_limit > 0 and total_players >= current_limit:
                    await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"⚠️ Player limit reached: {current_limit}/{current_limit}"})
                elif current_limit > 0 and total_players == current_limit - 1:
                    await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"ℹ️ Only 1 slot remaining ({total_players}/{current_limit})"})

            elif data["type"] == "ready":
                if websocket in clients:
                    clients[websocket]["ready"] = data["ready"]
                    await broadcast_lobby()

            elif data["type"] == "chat":
                await broadcast({"type": "chat", "sender": data["sender"], "message": data["message"]})
                
            elif data["type"] == "player_update":
                if websocket in clients:
                    clients[websocket].update({
                        "champion": data["champion"],
                        "team": data["team"],
                        "skin": data["skin"],
                        "spell1": data["spell1"],
                        "spell2": data["spell2"],
                        "runes": data.get("runes", clients[websocket].get("runes", {})),
                        "talents": data.get("talents", clients[websocket].get("talents", {}))
                    })
                    await broadcast_lobby()
                    
            elif data["type"] == "update_runes":
                if websocket in clients:
                    clients[websocket]["runes"] = data.get("runes", {})
                    clients[websocket]["talents"] = data.get("talents", {})
                    await broadcast_lobby()
                    
            elif data["type"] == "kick_player":
                if websocket == host_connection and "target_player" in data:
                    target_name = data["target_player"]
                    target_ws = None
                    for client_ws, client_info in clients.items():
                        if client_info["name"] == target_name:
                            target_ws = client_ws
                            break
                    
                    if target_ws and target_ws != host_connection:
                        try:
                            kick_msg = json.dumps({"type": "kicked"})
                            await target_ws.send(kick_msg)
                        except:
                            pass
                        
                        if target_ws in clients:
                            del clients[target_ws]
                        try:
                            await target_ws.close()
                        except:
                            pass
                        
                        await broadcast_lobby()
                        await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"{target_name} was kicked by the host"})
            
            elif data["type"] == "add_bot":
                if websocket == host_connection and "bot_data" in data:
                    current_limit = PLAYER_COUNT_LIMITS.get(game_settings.get("player_count", "5v5"), 10)
                    if current_limit > 0:
                        total_players = len(clients) + len(bots)
                        if total_players >= current_limit:
                            try:
                                await websocket.send(json.dumps({
                                    "type": "error", 
                                    "message": f"Cannot add bot: Player limit reached ({current_limit} players)"
                                }))
                            except:
                                pass
                            continue
                    
                    bot_data = data["bot_data"]
                    bot_name = bot_data["name"]
                    
                    bots[bot_name] = bot_data
                    shared_runes, shared_talents = load_shared_runes_and_talents()
                    bots[bot_name]["runes"] = shared_runes
                    bots[bot_name]["talents"] = shared_talents
                    await broadcast_lobby()
                    await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"{bot_name} (bot) joined the lobby"})
            
            elif data["type"] == "remove_bot":
                if websocket == host_connection and "bot_name" in data:
                    bot_name = data["bot_name"]
                    
                    if bot_name in bots:
                        del bots[bot_name]
                        await broadcast_lobby()
                        await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"{bot_name} (bot) left the lobby"})
            
            elif data["type"] == "update_bot":
                if websocket == host_connection and "bot_name" in data and "bot_data" in data:
                    bot_name = data["bot_name"]
                    bot_updates = data["bot_data"]
                    
                    if bot_name in bots:
                        bots[bot_name].update(bot_updates)
                        await broadcast_lobby()
                        await broadcast({"type": "chat", "sender": "SYSTEM", "message": f"Host updated {bot_name} settings"})
            
            elif data["type"] == "update_game_settings":
                if websocket == host_connection:
                    if "player_count" in data:
                        new_limit = PLAYER_COUNT_LIMITS.get(data["player_count"], 10)
                        total_players = len(clients) + len(bots)
                        
                        if new_limit > 0 and total_players > new_limit:
                            try:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": f"Cannot change to {data['player_count']}. Current player count ({total_players}) exceeds the new limit ({new_limit})"
                                }))
                                continue
                            except:
                                pass
                    
                    if "game_mode" in data:
                        game_settings["game_mode"] = data["game_mode"]
                    if "map" in data:
                        game_settings["map"] = data["map"]
                    if "player_count" in data:
                        game_settings["player_count"] = data["player_count"]
                    if "manacosts" in data:
                        game_settings["manacosts"] = data["manacosts"]
                    if "cooldowns" in data:
                        game_settings["cooldowns"] = data["cooldowns"]
                    if "cheats" in data:
                        game_settings["cheats"] = data["cheats"]
                    if "minion_spawns" in data:
                        game_settings["minion_spawns"] = data["minion_spawns"]
                    
                    await broadcast_lobby()
                    settings_msg = f"Host updated game settings: {game_settings['game_mode']} on {game_settings['map']} ({game_settings['player_count']})"
                    if "manacosts" in data or "cooldowns" in data or "cheats" in data or "minion_spawns" in data:
                        settings_msg += " (advanced settings changed)"
                    await broadcast({"type": "chat", "sender": "SYSTEM", "message": settings_msg})
            
            elif data["type"] == "move_player":
                if websocket == host_connection and "player_name" in data and "new_team" in data:
                    player_name = data["player_name"]
                    new_team = data["new_team"]
                    
                    moved = False
                    for client_info in clients.values():
                        if client_info["name"] == player_name:
                            old_team = client_info["team"]
                            client_info["team"] = new_team
                            moved = True
                            await broadcast_lobby()
                            await broadcast({"type": "chat", "sender": "SYSTEM", 
                                           "message": f"{player_name} moved from {old_team} to {new_team}"})
                            break
                    
                    if not moved and player_name in bots:
                        old_team = bots[player_name]["team"]
                        bots[player_name]["team"] = new_team
                        await broadcast_lobby()
                        await broadcast({"type": "chat", "sender": "SYSTEM", 
                                       "message": f"{player_name} moved from {old_team} to {new_team}"})
            
            elif data["type"] == "launch_game":
                if websocket == host_connection:
                    all_players_data = generate_players_data()
                    
                    try:
                        gameinfo_data = {
                            "type": "gameinfo_data",
                            "players_data": all_players_data,
                            "game_settings": game_settings
                        }
                        await websocket.send(json.dumps(gameinfo_data))
                    except:
                        pass
                    
                    for player_data in all_players_data:
                        if not player_data.get("is_bot", False):
                            player_ws = None
                            for client_ws, client_info in clients.items():
                                if client_info["name"] == player_data["name"]:
                                    player_ws = client_ws
                                    break
                            
                            if player_ws:
                                try:
                                    launch_data = {
                                        "type": "launch_game",
                                        "player_data": player_data,
                                        "host_ip": data["host_ip"],
                                        "game_port": data["game_port"]
                                    }
                                    await player_ws.send(json.dumps(launch_data))
                                except:
                                    pass

    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        if websocket == host_connection:
            host_connection = None
            if clients:
                host_connection = next(iter(clients.keys()))
                asyncio.create_task(broadcast({"type": "chat", "sender": "SYSTEM", "message": "New host assigned"}))

        if websocket in clients:
            player_name = clients[websocket]["name"]
            del clients[websocket]
            asyncio.create_task(broadcast_lobby())
            asyncio.create_task(broadcast({"type": "chat", "sender": "SYSTEM", "message": f"{player_name} left the lobby"}))

async def start_server():
    global server_instance, host_connection
    
    # Reset global state
    host_connection = None
    clients.clear()
    bots.clear()
    
    # Reset game settings to defaults
    game_settings.update({
        "game_mode": DEFAULT_GAME_MODE,
        "map": DEFAULT_MAP,
        "player_count": DEFAULT_PLAYER_COUNT,
        "manacosts": True,
        "cooldowns": True,
        "cheats": False,
        "minion_spawns": True
    })
    
    try:
        server_instance = await websockets.serve(
            handle_client, 
            "0.0.0.0",
            PORT
        )
        
        print(f"[WEBSOCKET SERVER] Listening on all interfaces (0.0.0.0:{PORT})")
        print(f"[WEBSOCKET SERVER] Local connections: ws://127.0.0.1:{PORT}")
        print(f"[WEBSOCKET SERVER] Network connections: ws://<your-ip>:{PORT}")
        
        await server_instance.wait_closed()
        
    except OSError as e:
        if e.errno == 10048:  # Address already in use
            print(f"[SERVER] Port {PORT} is already in use. Server might already be running.")
            print(f"[SERVER] If you want to restart, close any existing server first.")
        else:
            print(f"[SERVER] Error starting server: {e}")
    except Exception as e:
        print(f"[SERVER] Unexpected error: {e}")

def is_port_in_use(port):
    """Ελέγχει αν μια θύρα είναι σε χρήση"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return False
        except OSError:
            return True

def run_server(host_ip):
    global server_instance
    
    # Έλεγχος αν ο server είναι ήδη ενεργός
    if is_port_in_use(PORT):
        print(f"[SERVER] Port {PORT} is already in use. Server is already running.")
        print(f"[SERVER] You can connect to the existing server.")
        return
    
    print(f"[SERVER] Starting WebSocket server on 0.0.0.0:{PORT}")
    
    try:
        # Δημιουργία νέου event loop για το thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Εκτέλεση του server
        loop.run_until_complete(start_server())
        
    except KeyboardInterrupt:
        print(f"[SERVER] Server stopped by user")
    except Exception as e:
        print(f"[SERVER] Error: {e}")
    finally:
        # Καθαρισμός
        if server_instance:
            server_instance.close()
        clients.clear()
        bots.clear()

def stop_server():
    """Σταματάει τον server"""
    global server_instance
    if server_instance:
        server_instance.close()
        print("[SERVER] Server stopped")