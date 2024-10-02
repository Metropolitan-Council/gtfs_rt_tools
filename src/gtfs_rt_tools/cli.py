# defines the CLI tool
import argparse
import os
import time
import threading
from gtfs_rt_tools.process import download_single_feed_once, download_single_feed_interval, process_single_feed_csv
from gtfs_rt_tools.webapp import app, set_csv_folder  # Import the web app and the function to set the folder

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

    # Web app command
    web_parser = subparsers.add_parser("web", help="Run the web application")
    web_parser.add_argument("csv_folder", help="Path to the folder containing vehicle positions CSV files")

    args = parser.parse_args()

    if args.command == "download":
        if args.interval:
            download_single_feed_interval(args.url, args.output, args.interval)
        else:
            download_single_feed_once(args.url, args.output)
    elif args.command == "parse":
        process_single_feed_csv(args.input, args.archive, args.output)
    elif args.command == "web":
        # Set the CSV folder for the web app
        set_csv_folder(args.csv_folder)

        # Start the web app in a separate thread
        threading.Thread(target=lambda: app.run(debug=True, use_reloader=False), daemon=True).start()

        print(f"Web app running. Access it at http://127.0.0.1:5000/")

        # Keep the main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down the web app...")

if __name__ == "__main__":
    main()

