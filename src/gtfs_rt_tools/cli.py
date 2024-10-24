import argparse
import os
import time
import threading
import socket
from gtfs_rt_tools.process import download_single_feed_once, download_single_feed_interval, process_single_feed_csv
from gtfs_rt_tools.webapp import app as gtfs_webapp, set_csv_folder  # Existing GTFS Webapp
from gtfs_rt_tools.feed_comparison import app as new_app 

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=5000, max_port=5050):
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")

def run_webapp(app, csv_folder=None, urls=None, port=5000):
    # Configure the web app based on which one is being run
    if csv_folder:
        set_csv_folder(csv_folder)  # Set folder for existing GTFS app
    if urls:
        set_urls(urls)  # Set URLs for the new app

    app.run(debug=True, use_reloader=False, port=port)

def main():
    parser = argparse.ArgumentParser(description="GTFS RT Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download feed command
    download_parser = subparsers.add_parser("download", help="Download GTFS RT feed")
    download_parser.add_argument("url", help="URL of the GTFS RT feed")
    download_parser.add_argument("output", help="Output directory")
    download_parser.add_argument("-i", "--interval", type=int, help="Interval in seconds for repeated downloads")

    # Parse feed command
    parse_parser = subparsers.add_parser("parse", help="Parse GTFS RT feed")
    parse_parser.add_argument("input", help="Input directory containing downloaded feeds")
    parse_parser.add_argument("archive", help="Archive directory for processed files")
    parse_parser.add_argument("output", help="Output directory for parsed CSV files")

    # Existing Web app command (using GTFS CSV files)
    web_parser = subparsers.add_parser("web", help="Run the GTFS web application")
    web_parser.add_argument("csv_folder", help="Path to the folder containing vehicle positions CSV files")

    # New Web app command (for downloading and displaying JSON)
    feed_compare_web_parser = subparsers.add_parser("compare-feeds", help="Run the web application for comparing GTFS feeds")

    args = parser.parse_args()

    if args.command == "download":
        if args.interval:
            download_single_feed_interval(args.url, args.output, args.interval)
        else:
            download_single_feed_once(args.url, args.output)

    elif args.command == "parse":
        process_single_feed_csv(args.input, args.archive, args.output)

    elif args.command == "web":
        # Existing GTFS Webapp (CSV-based)
        port = find_available_port()
        print(f"Starting GTFS CSV web app on port {port}")
        webapp_thread = threading.Thread(target=run_webapp, args=(gtfs_webapp, args.csv_folder, None, port), daemon=True)
        webapp_thread.start()
        print(f"Web app running. Access it at http://127.0.0.1:{port}/")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down the GTFS CSV web app...")

    elif args.command == "compare-feeds":
        # New GTFS Webapp (for .pb and JSON-based display)
        port = find_available_port()
        print(f"Starting GTFS feed comparison web app on port {port}")
        webapp_thread = threading.Thread(target=run_webapp, args=(new_app, None, None, port), daemon=True)
        webapp_thread.start()
        print(f"Web app running. Access it at http://127.0.0.1:{port}/")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down the GTFS feed comparison web app...")

if __name__ == "__main__":
    main()

