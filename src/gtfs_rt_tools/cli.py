import argparse
import os
import time
import threading
import socket
from gtfs_rt_tools.download import download_single_feed_once, download_single_feed_interval
from gtfs_rt_tools.process_feeds import process_single_feed_csv
from gtfs_rt_tools.webapp import app as gtfs_webapp, set_csv_folder
from gtfs_rt_tools.feed_comparison import app as new_app
from gtfs_rt_tools.parse import parse_vehicle_positions, parse_trip_updates, parse_alerts
from pathlib import Path

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_available_port(start_port=5000, max_port=5050):
    for port in range(start_port, max_port):
        if not is_port_in_use(port):
            return port
    raise RuntimeError(f"No available ports in range {start_port}-{max_port}")

def run_webapp(app, csv_folder=None, urls=None, port=5000):
    if csv_folder:
        set_csv_folder(csv_folder)
    if urls:
        set_urls(urls)

    app.run(debug=True, use_reloader=False, port=port)

def parse_single_file(input_file: str, feed_type: str, output_file: str = None):
    """Parse a single protobuf file to CSV format.
    
    Args:
        input_file: Path to input .pb file
        feed_type: Type of feed ('vp', 'tu', or 'al')
        output_file: Optional output path, defaults to input path with .csv extension
    """
    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    # Default output path: same as input but with .csv extension
    if output_file is None:
        output_file = str(Path(input_file).with_suffix('.csv'))
    
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file) if os.path.dirname(output_file) else '.', exist_ok=True)
    
    # Select appropriate parser based on feed type
    parser_map = {
        'vp': parse_vehicle_positions,
        'tu': parse_trip_updates,
        'al': parse_alerts
    }
    
    if feed_type not in parser_map:
        raise ValueError(f"Invalid feed type: {feed_type}. Must be one of {list(parser_map.keys())}")
    
    # Parse the file using the appropriate parser
    df = parser_map[feed_type](input_file, use_pandas=True)
    
    # Write to CSV
    df.to_csv(output_file, index=False)
    print(f"Parsed {input_file} to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="GTFS RT Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download feed command
    download_parser = subparsers.add_parser("download", help="Download GTFS RT feed")
    download_parser.add_argument("url", help="URL of the GTFS RT feed")
    download_parser.add_argument("output", help="Output directory")
    download_parser.add_argument("-i", "--interval", type=int, help="Interval in seconds for repeated downloads")

    # Parse feed directory command
    parse_dir_parser = subparsers.add_parser("parse-feed", help="Parse GTFS RT feed directory")
    parse_dir_parser.add_argument("input", help="Input directory containing downloaded feeds")
    parse_dir_parser.add_argument("archive", help="Archive directory for processed files")
    parse_dir_parser.add_argument("output",
