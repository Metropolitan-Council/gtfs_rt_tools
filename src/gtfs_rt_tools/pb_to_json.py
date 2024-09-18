import sys
import json
from google.transit import gtfs_realtime_pb2
from google.protobuf.json_format import MessageToJson

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

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python convert_pb_to_json.py <input_pb_file> <output_json_file>")
    else:
        convert_pb_to_json(sys.argv[1], sys.argv[2])

