# contains functions to do larger chunks of the logging and processing steps
import os
import time
from datetime import datetime
import shutil
from .download import download_file, sanitize_filename, get_timestamped_filename
from .parse import parse_vehicle_positions, parse_trip_updates, parse_alerts
from .write import write_csv, write_delta
from pyspark.sql import SparkSession
from pyspark.sql.functions import lit
import sys

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

def process_feeds_delta(vp_url, tu_url, interval, bronze_path, silver_path, output_format="delta"):
    spark = SparkSession.builder.appName("GTFS-RT Processor").getOrCreate()
    
    while True:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        date = datetime.now().strftime("%Y%m%d")
        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%m")
        day = datetime.now().strftime("%d")

        sanitized_vp_url = sanitize_filename(vp_url)
        sanitized_tu_url = sanitize_filename(tu_url)

        vp_pb_dir = os.path.join(bronze_path, 'vp', year, month, 'pb')
        tu_pb_dir = os.path.join(bronze_path, 'tu', year, month, 'pb')
        vp_output_dir = os.path.join(silver_path, 'vp')
        tu_output_dir = os.path.join(silver_path, 'tu')

        os.makedirs(vp_pb_dir, exist_ok=True)
        os.makedirs(tu_pb_dir, exist_ok=True)

        vp_pb_filename = f"{sanitized_vp_url}_{timestamp}.pb"
        tu_pb_filename = f"{sanitized_tu_url}_{timestamp}.pb"

        vp_pb_file_path = os.path.join(vp_pb_dir, vp_pb_filename)
        tu_pb_file_path = os.path.join(tu_pb_dir, tu_pb_filename)

        try:
            download_file(vp_url, vp_pb_file_path)
            vp_df = parse_vehicle_positions(spark, vp_pb_file_path, vp_url, timestamp)
            vp_df = vp_df.withColumn("year", lit(year)).withColumn("month", lit(month)).withColumn("day", lit(day))
            if output_format == "delta":
                write_delta(vp_df, vp_output_dir)
            elif output_format == "csv":
                write_csv(vp_df, vp_output_dir)
        except Exception as e:
            print(f"Failed to process VehiclePositions feed: {e}", file=sys.stderr)

        try:
            download_file(tu_url, tu_pb_file_path)
            tu_df = parse_trip_updates(spark, tu_pb_file_path, tu_url, timestamp)
            tu_df = tu_df.withColumn("year", lit(year)).withColumn("month", lit(month)).withColumn("day", lit(day))
            if output_format == "delta":
                write_delta(tu_df, tu_output_dir)
            elif output_format == "csv":
                write_csv(tu_df, tu_output_dir)
        except Exception as e:
            print(f"Failed to process TripUpdates feed: {e}", file=sys.stderr)

        time.sleep(interval)

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
