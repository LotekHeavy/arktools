#!/bin/python3

import os
import glob
import psutil
import requests
from datetime import datetime

# ANSI Farbcodes
COLOR_OK = "\033[92m"  # Hellgrün
COLOR_OFFLINE = "\033[91m"  # Hellrot
END_COLOR = "\033[0m"  # Setzt die Farbe zurück

# Pfad zum Verzeichnis mit den .cfg-Dateien
dir_path = "/etc/arkmanager/instances"

# Wörterbuch, in dem die Dateinamen und Pfade gespeichert werden
process_dict = {}

# Durchlaufen aller .cfg-Dateien im Verzeichnis
for file_path in glob.glob(os.path.join(dir_path, "*.cfg")):
    # Öffnen der Datei zum Lesen
    with open(file_path, 'r') as file:
        # Durchlaufen aller Zeilen in der Datei
        for line in file:
            # Prüfen, ob die Zeile mit 'arkserverroot' beginnt
            if line.startswith('arkserverroot'):
                # Extrahieren des Pfades aus der Zeile
                path = line.split('=')[1].strip().split('#')[0].strip().strip('"')

                # Extrahieren des Dateinamens ohne Endung
                filename = os.path.basename(file_path).split('.')[0]

                # Speichern des Dateinamens und Pfades im Wörterbuch
                process_dict[filename] = path

# Überprüfen, ob die Prozesse laufen
now = datetime.now()
formatted_now = now.strftime("%d-%m-%Y %H:%M:%S")
print(f"{formatted_now}: Server Status")

# Liste um den Status der Server zu sammeln
server_statuses = []

for filename, path in process_dict.items():
    for proc in psutil.process_iter(['name', 'cmdline']):
        if proc.info['name'] == 'ShooterGameServer' and filename in [segment for arg in proc.info['cmdline'] for segment in arg.split('/')]:
            print(f" - {filename}: {COLOR_OK}OK{END_COLOR}")
            server_statuses.append(f"<li>{filename[0].upper() + filename[1:]}: <span style=\"color:green\">OK</span></li>")
            break
    else:
        print(f" - {filename}: {COLOR_OFFLINE}OFFLINE{END_COLOR}")
        server_statuses.append(f"<li>{filename[0].upper() + filename[1:]}: <span style=\"color:red\">OFFLINE</span></li>")


# Senden der Server-Status an Drupal 9 REST API
current_date = datetime.now().strftime("%m.%d.%y %H:%M")
content = {
    "_links": {
        "type": {
            "href": "https://XXXXXXXXXXX/rest/type/node/page"
        }
    },
    "title": [
        {
            "value": f"Server Status"
        }
    ],
    "body": [
        {
            "value": f"<p><ul>{''.join(server_statuses)}</ul></p><p><i>Letzte Aktualisierung am {current_date}</i></p>",
            "format": "raw_html"
        }
    ]
}

website = "https://XXXXXXXXXXX/node/XXXXX?_format=hal_json"
response = requests.patch(website, headers={'Accept': 'application/hal+json', 'Content-Type': 'application/hal+json'}, json=content, auth=('XXXX', 'XXXXX'))

