# GTFS-realtime Tools

This is a Python package used to download, process, and archive GTFS-realtime feeds.

# Python Package

## Current Functionality

- download GTFS-realtime .pb files to date-partitioned archives
- convert .pb files to JSON
- convert .pb files to Dataframes
- write Dataframes to CSV or Databricks Delta tables

## Planned Functionality

- integrate with a web application to quickly compare contents of multiple feeds

# CLI Tool

## Current Functionality

- download TripUpdates, VehiclePositions, and Alerts feeds from a single base URL, writing to date-partitioned output folder
    - example: `gtfs-rt-tools download 'https://svc.metrotransit.org/mtgtfs/' test_out`
    - interval example (will download every 30 seconds): `gtfs-rt-tools download 'https://svc.metrotransit.org/mtgtfs/' test_out -i 30`
- parse a partitioned output folder into a partitioned CSV output folder, moving parsed .pb files into a partitioned archive
    - example: `gtfs-rt-tools parse test_out test_archive test_processed`


