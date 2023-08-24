#!/usr/bin/env python3
import requests
import os
import time
import argparse

BASE_URL = "https://ark.wiki.gg/api.php"
EXPORT_URL = "https://ark.wiki.gg/wiki/Special:Export"
OUTPUT_DIR = "/home/ark/src/wiki"
DELAY = 0.1
TIMEOUT = 10

def fetch_all_pages_from_main_namespace():
    params = {
        "action": "query",
        "format": "json",
        "list": "allpages",
        "apnamespace": 0,
        "aplimit": 500
    }
    
    pages = []
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        pages.extend(data['query']['allpages'])
        
        while 'continue' in data:
            time.sleep(DELAY)
            params.update(data['continue'])
            
            response = requests.get(BASE_URL, params=params)
            response.raise_for_status()
            
            data = response.json()
            pages.extend(data['query']['allpages'])
    except requests.RequestException as e:
        print(f"Fehler beim Abrufen der Seiten: {e}")
    
    return [page['title'] for page in pages]

def export_page(title, verbose):
    filepath = os.path.join(OUTPUT_DIR, title.replace('/', '_') + ".xml")

    params = {
        "pages": title,
        "action": "submit",
        "curonly": 1
    }
    
    try:
        if verbose:
            print(f"Senden einer Anfrage an {EXPORT_URL}...")
        response = requests.post(EXPORT_URL, data=params, timeout=TIMEOUT)
        response.raise_for_status()
        
        # Wenn die Datei bereits existiert, vergleiche ihre Größe mit der Größe der neuen Daten
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            new_data_size = len(response.content)

            if file_size == new_data_size:
                if verbose:
                    print(f"'{title}' hat sich nicht geändert seit dem letzten Download. Überspringen...")
                return

        if response.content:
            if verbose:
                print(f"Speichern von {title} in {filepath}...")
            with open(filepath, "wb") as f:
                f.write(response.content)
            if verbose:
                print(f"{title} erfolgreich gespeichert.")
        else:
            print(f"Kein Inhalt empfangen für '{title}'. Antwort war: {response.text}")
    except requests.RequestException as e:
        print(f"Fehler beim Exportieren von '{title}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Skript zum Exportieren von Wiki-Seiten.")
    parser.add_argument('--verbose', action='store_true', help='Detaillierte Ausgabe anzeigen.')
    args = parser.parse_args()
    
    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        start_time = time.time()
        page_titles = fetch_all_pages_from_main_namespace()
        total_pages = len(page_titles)
        print(f"{total_pages} Seiten gefunden.")
        exported_pages = 0

        for title in page_titles:
            print(f"Exportiere: {title} ({exported_pages + 1}/{total_pages})")
            export_page(title, args.verbose)
            exported_pages += 1
            if args.verbose:
                elapsed_time = time.time() - start_time
                print(f"Verstrichene Zeit: {elapsed_time:.2f} Sekunden")
            time.sleep(DELAY)
        
        print("Script beendet.")

    except Exception as e:
        print(f"Ein Fehler ist aufgetreten: {e}")
