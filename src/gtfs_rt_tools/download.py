# contains functions to download GTFS-rt feeds and format downloaded files
import os
import re
from datetime import datetime
import requests
import time
import sys

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9]', '_', filename)

def get_timestamped_filename(url):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    sanitized_url = sanitize_filename(url)
    return f"{sanitized_url}_{timestamp}.pb"

def download_file(url, save_path):
    headers = {}
    if 'https://api.goswift.ly' in url:
        swiftly_api_key = os.environ.get('SWIFTLY_API')
        if not swiftly_api_key:
            raise ValueError("SWIFTLY_API environmental variable is not set")
        headers['Authorization'] = swiftly_api_key

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    with open(save_path, 'wb') as file:
        file.write(response.content)

def download_single_feed_once(leading_url, out_dir):
    tu_url = f"{leading_url}tripupdates.pb"
    vp_url = f"{leading_url}vehiclepositions.pb"
    al_url = f"{leading_url}alerts.pb"

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    date = datetime.now().strftime("%Y%m%d")
    year = datetime.now().strftime("%Y")
    month = datetime.now().strftime("%m")
    day = datetime.now().strftime("%d")

    sanitized_tu_url = sanitize_filename(tu_url)
    sanitized_vp_url = sanitize_filename(vp_url)
    sanitized_al_url = sanitize_filename(al_url)

    tu_pb_dir = os.path.join(out_dir, 'tu', year, month, day)
    vp_pb_dir = os.path.join(out_dir, 'vp', year, month, day)
    al_pb_dir = os.path.join(out_dir, 'al', year, month, day)

    os.makedirs(tu_pb_dir, exist_ok=True)
    os.makedirs(vp_pb_dir, exist_ok=True)
    os.makedirs(al_pb_dir, exist_ok=True)

    tu_pb_filename = f"{sanitized_tu_url}_{timestamp}.pb"
    vp_pb_filename = f"{sanitized_vp_url}_{timestamp}.pb"
    al_pb_filename = f"{sanitized_al_url}_{timestamp}.pb"

    tu_pb_file_path = os.path.join(tu_pb_dir, tu_pb_filename)
    vp_pb_file_path = os.path.join(vp_pb_dir, vp_pb_filename)
    al_pb_file_path = os.path.join(al_pb_dir, al_pb_filename)

    try:
        download_file(tu_url, tu_pb_file_path)
    except Exception as e:
        print(f"Failed to process TripUpdates feed: {e}", file=sys.stderr)
    try:
        download_file(vp_url, vp_pb_file_path)
    except Exception as e:
        print(f"Failed to process VehiclePositions feed: {e}", file=sys.stderr)
    try:
        download_file(al_url, al_pb_file_path)
    except Exception as e:
        print(f"Failed to process Alerts feed: {e}", file=sys.stderr)

def download_single_feed_interval(leading_url, out_dir, interval):
    while True:
        download_single_feed_once(leading_url, out_dir)
        time.sleep(interval)