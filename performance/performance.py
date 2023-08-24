
#!/usr/bin/env python3

import datetime
import json
import re
import requests
import pandas as pd
import matplotlib.pyplot as plt
from pandas.plotting import register_matplotlib_converters
from matplotlib.dates import DateFormatter
from datetime import datetime, timedelta
import argparse
import configparser

register_matplotlib_converters()

# Reading configuration from performance.ini
config = configparser.ConfigParser()
config.read('performance.ini')

GLANCES_API_URL = config.get('DEFAULT', 'GLANCES_API_URL')
GLANCES_AUTH = (config.get('DEFAULT', 'GLANCES_USERNAME'), config.get('DEFAULT', 'GLANCES_PASSWORD'))
LOG_PATH = config.get('DEFAULT', 'LOG_PATH')
PLOT_PATH = config.get('DEFAULT', 'PLOT_PATH')


def get_process_info():
    response = requests.get(GLANCES_API_URL + "processlist", auth=GLANCES_AUTH)
    if response.status_code != 200:
        print(f"Error! Received status code {response.status_code}: {response.text}")
        return []
    data = response.json()
    results = []
    for proc in data:
        cmd = ' '.join(proc['cmdline'])
        if "ShooterGameServer" in cmd:
            session_pattern = re.search(r'SessionName=([^?\s]+)', cmd)
            if session_pattern:
                session_name = session_pattern.group(1)
                cpu = proc['cpu_percent']
                mem = proc['memory_info'][1] / (1024**3)  # Umwandlung in GB
                results.append((cpu, mem, session_name))
    return results

def get_system_load():
    with open("/proc/loadavg", "r") as f:
        load_data = f.read().split()
        return load_data[0]

def save_performance_data():
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    system_load = get_system_load()
    with open(LOG_PATH, 'a') as log_file:
        for cpu, mem, session_name in get_process_info():
            log_file.write(f"{timestamp};{session_name};{cpu:.2f};{mem:.2f};{system_load}\n")

def plot_csv_data(filepath):
    total_rows = sum(1 for line in open(filepath))
    max_rows = 1000
    skip_rows = max(0, total_rows - max_rows)
    df = pd.read_csv(filepath, delimiter=';', header=None, names=["Timestamp", "SessionName", "CPU", "Memory", "Load"], skiprows=skip_rows)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    cutoff = datetime.now() - timedelta(hours=48)
    df = df[df["Timestamp"] > cutoff]
    fig, ax1 = plt.subplots(figsize=(18,8))
    color_list = plt.cm.tab10.colors
    num_colors = len(color_list)
    ax2 = ax1.twinx()
    for idx, session in enumerate(df["SessionName"].unique()):
        subset = df[df["SessionName"] == session]
        color = color_list[idx % num_colors]
        ax1.plot(subset["Timestamp"], subset["CPU"], label=session, linestyle='-', color=color)
        ax2.plot(subset["Timestamp"], subset["Memory"], linestyle=':', color=color)
    ax1.set_xlabel("Timestamp")
    ax1.set_ylabel("CPU (%)")
    ax2.set_ylabel("Memory (GB)")
    plt.title("CPU und Memory-Auslastung nach Session")
    ax1.legend(loc='upper left')
    plt.xticks(rotation=45)
    date_format = DateFormatter("%d.%m %H:%M")
    ax1.xaxis.set_major_formatter(date_format)
    ax2.set_ylim(min(df["Memory"]) - 1, max(df["Memory"]) + 1)
    plt.tight_layout()
    plt.savefig(PLOT_PATH)
    plt.close()

def main():
    parser = argparse.ArgumentParser(description="Performance Monitoring und Visualisierung.")
    parser.add_argument("--plot", action="store_true", help="Erstellt einen Plot basierend auf den Leistungsdaten.")
    args = parser.parse_args()
    if args.plot:
        plot_csv_data(LOG_PATH)
    else:
        save_performance_data()

if __name__ == "__main__":
    main()
