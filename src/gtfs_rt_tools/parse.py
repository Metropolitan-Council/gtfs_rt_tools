import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, LongType
from datetime import datetime
import os
from google.protobuf.json_format import MessageToJson
from google.transit import gtfs_realtime_pb2

def convert_pb_to_json(pb_file_path, json_file_path):
    # Read the protobuf .pb file
    with open(pb_file_path, 'rb') as pb_file:
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(pb_file.read())

    # Convert to JSON format
    json_data = MessageToJson(feed, preserving_proto_field_name=True)

    # Write JSON to the specified file
    with open(json_file_path, 'w') as json_file:
        json_file.write(json_data)

    print(f"Converted {pb_file_path} to {json_file_path}")

def parse_trip_updates(input_file, url=None, logtime=None, use_pandas=False, spark=None, filename_meets_schema=False):
    feed = gtfs_realtime_pb2.FeedMessage()
    with open(input_file, 'rb') as f:
        feed.ParseFromString(f.read())
    
    if filename_meets_schema:
        # Extract url and logtime from the filename
        filename = os.path.basename(input_file)
        url, timestamp = filename.rsplit('_', 1)
        url = url.replace('_', '/')  # Assuming underscores in URL were replaced with '_'
        logtime = datetime.strptime(timestamp.split('.')[0], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    
    data = []
    for entity in feed.entity:
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            
            for stop_time_update in trip_update.stop_time_update:
                data.append((
                    url, logtime,
                    trip_update.trip.trip_id,
                    trip_update.trip.route_id,
                    trip_update.trip.direction_id if trip_update.trip.HasField('direction_id') else None,
                    trip_update.trip.start_time,
                    trip_update.trip.start_date,
                    trip_update.trip.schedule_relationship,
                    trip_update.vehicle.id if trip_update.HasField('vehicle') else None,
                    trip_update.vehicle.label if trip_update.HasField('vehicle') else None,
                    trip_update.vehicle.license_plate if trip_update.HasField('vehicle') else None,
                    trip_update.timestamp if trip_update.HasField('timestamp') else None,
                    trip_update.delay if trip_update.HasField('delay') else None,
                    stop_time_update.stop_sequence if stop_time_update.HasField('stop_sequence') else None,
                    stop_time_update.stop_id if stop_time_update.HasField('stop_id') else None,
                    stop_time_update.arrival.delay if stop_time_update.HasField('arrival') else None,
                    stop_time_update.arrival.time if stop_time_update.HasField('arrival') else None,
                    stop_time_update.arrival.uncertainty if stop_time_update.HasField('arrival') and stop_time_update.arrival.HasField('uncertainty') else None,
                    stop_time_update.departure.delay if stop_time_update.HasField('departure') else None,
                    stop_time_update.departure.time if stop_time_update.HasField('departure') else None,
                    stop_time_update.departure.uncertainty if stop_time_update.HasField('departure') and stop_time_update.departure.HasField('uncertainty') else None,
                    stop_time_update.schedule_relationship if stop_time_update.HasField('schedule_relationship') else None
                ))
    
    schema = StructType([
        StructField("url", StringType(), True),
        StructField("logtime", StringType(), True),
        StructField("trip_id", StringType(), True),
        StructField("route_id", StringType(), True),
        StructField("direction_id", IntegerType(), True),
        StructField("start_time", StringType(), True),
        StructField("start_date", StringType(), True),
        StructField("trip_schedule_relationship", IntegerType(), True),
        StructField("vehicle_id", StringType(), True),
        StructField("vehicle_label", StringType(), True),
        StructField("vehicle_license_plate", StringType(), True),
        StructField("timestamp", LongType(), True),
        StructField("delay", IntegerType(), True),
        StructField("stop_sequence", IntegerType(), True),
        StructField("stop_id", StringType(), True),
        StructField("arrival_delay", IntegerType(), True),
        StructField("arrival_time", LongType(), True),
        StructField("arrival_uncertainty", IntegerType(), True),
        StructField("departure_delay", IntegerType(), True),
        StructField("departure_time", LongType(), True),
        StructField("departure_uncertainty", IntegerType(), True),
        StructField("stop_time_update_schedule_relationship", IntegerType(), True)
    ])
    
    if use_pandas:
        return pd.DataFrame(data, columns=[field.name for field in schema.fields])
    else:
        if spark is None:
            raise ValueError("Spark session must be provided when use_pandas is False")
        return spark.createDataFrame(data, schema)

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, LongType, ArrayType

def parse_vehicle_positions(input_file, url=None, logtime=None, use_pandas=False, spark=None, filename_meets_schema=False):
    feed = gtfs_realtime_pb2.FeedMessage()
    with open(input_file, 'rb') as f:
        feed.ParseFromString(f.read())

    if filename_meets_schema:
        # Extract url and logtime from the filename
        filename = os.path.basename(input_file)
        url, timestamp = filename.rsplit('_', 1)
        url = url.replace('_', '/')  # Assuming underscores in URL were replaced with '_'
        logtime = datetime.strptime(timestamp.split('.')[0], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    
    data = []
    for entity in feed.entity:
        if entity.HasField('vehicle'):
            vehicle = entity.vehicle
            
            multi_carriage_details = [
                {
                    'id': carriage.id if carriage.HasField('id') else None,
                    'label': carriage.label if carriage.HasField('label') else None,
                    'occupancy_status': carriage.occupancy_status if carriage.HasField('occupancy_status') else None,
                    'occupancy_percentage': carriage.occupancy_percentage if carriage.HasField('occupancy_percentage') else None,
                } for carriage in vehicle.multi_carriage_details
            ]
            
            data.append((
                url, logtime,
                vehicle.trip.trip_id if vehicle.HasField('trip') else None,
                vehicle.trip.route_id if vehicle.HasField('trip') else None,
                vehicle.trip.direction_id if vehicle.HasField('trip') and vehicle.trip.HasField('direction_id') else None,
                vehicle.trip.start_time if vehicle.HasField('trip') else None,
                vehicle.trip.start_date if vehicle.HasField('trip') else None,
                vehicle.trip.schedule_relationship if vehicle.HasField('trip') else None,
                vehicle.vehicle.id if vehicle.HasField('vehicle') else None,
                vehicle.vehicle.label if vehicle.HasField('vehicle') else None,
                vehicle.vehicle.license_plate if vehicle.HasField('vehicle') else None,
                vehicle.position.latitude if vehicle.HasField('position') else None,
                vehicle.position.longitude if vehicle.HasField('position') else None,
                vehicle.position.bearing if vehicle.HasField('position') and vehicle.position.HasField('bearing') else None,
                vehicle.position.odometer if vehicle.HasField('position') and vehicle.position.HasField('odometer') else None,
                vehicle.position.speed if vehicle.HasField('position') and vehicle.position.HasField('speed') else None,
                vehicle.current_stop_sequence if vehicle.HasField('current_stop_sequence') else None,
                vehicle.stop_id if vehicle.HasField('stop_id') else None,
                vehicle.current_status if vehicle.HasField('current_status') else None,
                vehicle.timestamp if vehicle.HasField('timestamp') else None,
                vehicle.congestion_level if vehicle.HasField('congestion_level') else None,
                vehicle.occupancy_status if vehicle.HasField('occupancy_status') else None,
                vehicle.occupancy_percentage if vehicle.HasField('occupancy_percentage') else None,
                multi_carriage_details
            ))
    
    schema = StructType([
        StructField("url", StringType(), True),
        StructField("logtime", StringType(), True),
        StructField("trip_id", StringType(), True),
        StructField("route_id", StringType(), True),
        StructField("direction_id", IntegerType(), True),
        StructField("start_time", StringType(), True),
        StructField("start_date", StringType(), True),
        StructField("schedule_relationship", IntegerType(), True),
        StructField("vehicle_id", StringType(), True),
        StructField("vehicle_label", StringType(), True),
        StructField("license_plate", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("bearing", DoubleType(), True),
        StructField("odometer", DoubleType(), True),
        StructField("speed", DoubleType(), True),
        StructField("current_stop_sequence", IntegerType(), True),
        StructField("stop_id", StringType(), True),
        StructField("current_status", IntegerType(), True),
        StructField("timestamp", LongType(), True),
        StructField("congestion_level", IntegerType(), True),
        StructField("occupancy_status", IntegerType(), True),
        StructField("occupancy_percentage", IntegerType(), True),
        StructField("multi_carriage_details", ArrayType(StructType([
            StructField("id", StringType(), True),
            StructField("label", StringType(), True),
            StructField("occupancy_status", IntegerType(), True),
            StructField("occupancy_percentage", IntegerType(), True)
        ])), True)
    ])
    
    if use_pandas:
        return pd.DataFrame(data, columns=[field.name for field in schema.fields])
    else:
        if spark is None:
            raise ValueError("Spark session must be provided when use_pandas is False")
        return spark.createDataFrame(data, schema)


def parse_alerts(input_file, url=None, logtime=None, use_pandas=False, spark=None, filename_meets_schema=False):
    feed = gtfs_realtime_pb2.FeedMessage()
    with open(input_file, 'rb') as f:
        feed.ParseFromString(f.read())

    if filename_meets_schema:
        # Extract url and logtime from the filename
        filename = os.path.basename(input_file)
        url, timestamp = filename.rsplit('_', 1)
        url = url.replace('_', '/')  # Assuming underscores in URL were replaced with '_'
        logtime = datetime.strptime(timestamp.split('.')[0], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    
    data = []
    for entity in feed.entity:
        if entity.HasField('alert'):
            alert = entity.alert
            
            # Process TimeRanges
            active_period_start = None
            active_period_end = None
            if alert.active_period:
                active_period_start = alert.active_period[0].start if alert.active_period[0].HasField('start') else None
                active_period_end = alert.active_period[0].end if alert.active_period[0].HasField('end') else None
            
            # Process InformedEntities
            agency_id = None
            route_id = None
            route_type = None
            stop_id = None
            trip_id = None
            trip_route_id = None
            trip_direction_id = None
            trip_start_time = None
            trip_start_date = None
            
            if alert.informed_entity:
                entity = alert.informed_entity[0]
                agency_id = entity.agency_id if entity.HasField('agency_id') else None
                route_id = entity.route_id if entity.HasField('route_id') else None
                route_type = entity.route_type if entity.HasField('route_type') else None
                stop_id = entity.stop_id if entity.HasField('stop_id') else None
                if entity.HasField('trip'):
                    trip = entity.trip
                    trip_id = trip.trip_id if trip.HasField('trip_id') else None
                    trip_route_id = trip.route_id if trip.HasField('route_id') else None
                    trip_direction_id = trip.direction_id if trip.HasField('direction_id') else None
                    trip_start_time = trip.start_time if trip.HasField('start_time') else None
                    trip_start_date = trip.start_date if trip.HasField('start_date') else None
            
            # Process Cause and Effect
            cause = alert.cause if alert.HasField('cause') else None
            effect = alert.effect if alert.HasField('effect') else None
            
            # Process URL, HeaderText, and DescriptionText
            url_text = alert.url.translation[0].text if alert.url.translation else None
            url_language = alert.url.translation[0].language if alert.url.translation and alert.url.translation[0].HasField('language') else None
            
            header_text = alert.header_text.translation[0].text if alert.header_text.translation else None
            header_language = alert.header_text.translation[0].language if alert.header_text.translation and alert.header_text.translation[0].HasField('language') else None
            
            description_text = alert.description_text.translation[0].text if alert.description_text.translation else None
            description_language = alert.description_text.translation[0].language if alert.description_text.translation and alert.description_text.translation[0].HasField('language') else None
            
            # Process TTS HeaderText and DescriptionText
            tts_header_text = alert.tts_header_text.translation[0].text if alert.HasField('tts_header_text') and alert.tts_header_text.translation else None
            tts_header_language = alert.tts_header_text.translation[0].language if alert.HasField('tts_header_text') and alert.tts_header_text.translation and alert.tts_header_text.translation[0].HasField('language') else None
            
            tts_description_text = alert.tts_description_text.translation[0].text if alert.HasField('tts_description_text') and alert.tts_description_text.translation else None
            tts_description_language = alert.tts_description_text.translation[0].language if alert.HasField('tts_description_text') and alert.tts_description_text.translation and alert.tts_description_text.translation[0].HasField('language') else None
            
            # Append all data for this alert
            data.append((
                url, logtime, active_period_start, active_period_end,
                agency_id, route_id, route_type, stop_id,
                trip_id, trip_route_id, trip_direction_id, trip_start_time, trip_start_date,
                cause, effect,
                url_text, url_language,
                header_text, header_language,
                description_text, description_language,
                tts_header_text, tts_header_language,
                tts_description_text, tts_description_language
            ))
    
    # Define the flattened schema for the DataFrame
    schema = StructType([
        StructField("url", StringType(), True),
        StructField("logtime", StringType(), True),
        StructField("active_period_start", LongType(), True),
        StructField("active_period_end", LongType(), True),
        StructField("agency_id", StringType(), True),
        StructField("route_id", StringType(), True),
        StructField("route_type", IntegerType(), True),
        StructField("stop_id", StringType(), True),
        StructField("trip_id", StringType(), True),
        StructField("trip_route_id", StringType(), True),
        StructField("trip_direction_id", IntegerType(), True),
        StructField("trip_start_time", StringType(), True),
        StructField("trip_start_date", StringType(), True),
        StructField("cause", IntegerType(), True),
        StructField("effect", IntegerType(), True),
        StructField("url_text", StringType(), True),
        StructField("url_language", StringType(), True),
        StructField("header_text", StringType(), True),
        StructField("header_language", StringType(), True),
        StructField("description_text", StringType(), True),
        StructField("description_language", StringType(), True),
        StructField("tts_header_text", StringType(), True),
        StructField("tts_header_language", StringType(), True),
        StructField("tts_description_text", StringType(), True),
        StructField("tts_description_language", StringType(), True)
    ])
    
     
    if use_pandas:
        return pd.DataFrame(data, columns=[field.name for field in schema.fields])
    else:
        if spark is None:
            raise ValueError("Spark session must be provided when use_pandas is False")
        return spark.createDataFrame(data, schema)
