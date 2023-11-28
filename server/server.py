#!/usr/bin/env python3
import sys
import os
import subprocess

# Konstanten
ARKMANAGER_PATH = "/home/ark/bin/arkmanager"
INSTANCE_DIR = "/etc/arkmanager/instances/"

def show_help():
    """Zeigt die verfügbaren Befehle an."""
    print("Verfügbare Befehle:")
    print("  start [<map>]     - Startet den Server. Falls kein Kartenname angegeben wird, wird 'all' verwendet.")
    print("  stop [<map>]      - Stoppt den Server. Falls kein Kartenname angegeben wird, wird 'all' verwendet.")
    print("  restart [<map>]   - Startet den Server neu. Falls kein Kartenname angegeben wird, wird 'all' verwendet.")
    print("  update [<map>]    - Aktualisiert den Server. Falls kein Kartenname angegeben wird, wird 'all' verwendet.")
    print("  enable <map>      - Aktiviert den angegebenen Server. Ein Kartenname ist erforderlich.")
    print("  disable <map>     - Deaktiviert den angegebenen Server. Ein Kartenname ist erforderlich.")
    print("  list, status      - Zeigt eine Liste aller aktivierten und deaktivierten Server.")

def arkmanager_cmd(cmd, map_name=None):
    """Führt den arkmanager Befehl aus."""
    if map_name:
        cmd.append(f"@{map_name}")
    subprocess.run([ARKMANAGER_PATH] + cmd)

def change(action, map_name):
    """Aktiviert oder deaktiviert den angegebenen Server."""
    if not map_name:
        print(f"Fehler: Ein Kartenname ist erforderlich, um {action} auszuführen.")
        sys.exit(1)
    
    file_path = os.path.join(INSTANCE_DIR, map_name)
    from_path, to_path = {
        "enable": (f"{file_path}.cfg.stop", f"{file_path}.cfg"),
        "disable": (f"{file_path}.cfg", f"{file_path}.cfg.stop")
    }.get(action)

    print(f"Trying to {action} {map_name}")
    
    if os.path.exists(to_path):
        print(f"Error: File {to_path} already exists.")
        return

    if os.path.exists(from_path):
        if action == "disable":
            arkmanager_cmd(["stop", "--warn", "--saveworld"], map_name)
        os.rename(from_path, to_path)
        if action == "enable":
            arkmanager_cmd(["update", "--saveworld", "--update-mods", "--backup", "--warn"], map_name)
        print(f"Done: Server '{map_name}' {action}d!")
    else:
        print(f"Error: File {from_path} not found")

def list_servers():
    """Listet die aktivierten und deaktivierten Server auf."""
    print("Enabled Maps:")
    print("-------------")
    for file_name in os.listdir(INSTANCE_DIR):
        if file_name.endswith(".cfg"):
            print(file_name.replace('.cfg', ''))
    print("\nDisabled Maps:")
    print("--------------")
    for file_name in os.listdir(INSTANCE_DIR):
        if file_name.endswith(".cfg.stop"):
            print(file_name.replace('.cfg.stop', ''))

# Hauptteil
os.chdir('/home/ark')

if len(sys.argv) == 1:
    show_help()
    sys.exit(0)

action = sys.argv[1]
map_name = "all" if action in ["start", "stop", "restart", "update"] and len(sys.argv) <= 2 else sys.argv[2] if len(sys.argv) > 2 else None

if action in ["start", "stop", "restart", "update"]:
    print(f"> {action.capitalize()} @{map_name}")
    if action == "restart":
        arkmanager_cmd(["restart", "--warn", "--saveworld"], map_name)
    elif action == "stop":
        arkmanager_cmd(["stop", "--warn", "--saveworld"], map_name)
    elif action == "update":
        arkmanager_cmd(["update", "--warn", "--saveworld", "--update-mods", "--backup"], map_name)
    else:
        arkmanager_cmd([action], map_name)
elif action in ["enable", "disable"]:
    change(action, map_name)
elif action in ["list", "status"]:
    list_servers()
else:
    print(f"Unbekannte Aktion: {action}.")
    show_help()

