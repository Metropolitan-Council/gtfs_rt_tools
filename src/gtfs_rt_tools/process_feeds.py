# contains functions to do larger chunks of the logging and processing steps
import os
from datetime import datetime
import shutil
from .download import download_file, sanitize_filename, get_timestamped_filename
from .parse import parse_vehicle_positions, parse_trip_updates, parse_alerts
from .write import write_csv
import sys

def process_single_feed_csv(input_dir, archive_dir, output_dir):
    for feed_type in ['tu', 'vp', 'al']:
        feed_input_dir = os.path.join(input_dir, feed_type)
        feed_archive_dir = os.path.join(archive_dir, feed_type)
        feed_output_dir = os.path.join(output_dir, feed_type)

        for year_dir in os.listdir(feed_input_dir):
            year_path = os.path.join(feed_input_dir, year_dir)
            if os.path.isdir(year_path):
                for month_dir in os.listdir(year_path):
                    month_path = os.path.join(year_path, month_dir)
                    if os.path.isdir(month_path):
                        for day_dir in os.listdir(month_path):
                            day_path = os.path.join(month_path, day_dir)
                            if os.path.isdir(day_path):
                                for file in os.listdir(day_path):
                                    if file.endswith('.pb'):
                                        input_file = os.path.join(day_path, file)
                                        
                                        # Parse the file
                                        if feed_type == 'tu':
                                            df = parse_trip_updates(input_file, filename_meets_schema=True, use_pandas=True)
                                        elif feed_type == 'vp':
                                            df = parse_vehicle_positions(input_file, filename_meets_schema=True, use_pandas=True)
                                        elif feed_type == 'al':
                                            df = parse_alerts(input_file, filename_meets_schema=True, use_pandas=True)
                                        
                                        # Write CSV
                                        csv_filename = file.replace('.pb', '.csv')
                                        csv_output_path = os.path.join(feed_output_dir, year_dir, month_dir, day_dir)
                                        os.makedirs(csv_output_path, exist_ok=True)
                                        csv_file = os.path.join(csv_output_path, csv_filename)
                                        write_csv(df, csv_file)
                                        
                                        # Archive original file
                                        archive_path = os.path.join(feed_archive_dir, year_dir, month_dir, day_dir)
                                        os.makedirs(archive_path, exist_ok=True)
                                        shutil.move(input_file, os.path.join(archive_path, file))

    print(f"Parsing complete. Results saved in {output_dir}")
