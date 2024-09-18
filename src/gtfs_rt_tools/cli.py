import argparse
from gtfs_rt_tools.process import download_single_feed_once, parse_single_feed_csv

def main():
    parser = argparse.ArgumentParser(description="GTFS RT Tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Download feed command
    download_parser = subparsers.add_parser("download", help="Download GTFS RT feed")
    download_parser.add_argument("url", help="URL of the GTFS RT feed")
    download_parser.add_argument("output", help="Output directory")

    # Parse feed command
    parse_parser = subparsers.add_parser("parse", help="Parse GTFS RT feed")
    parse_parser.add_argument("input", help="Input directory containing downloaded feeds")
    parse_parser.add_argument("archive", help="Archive directory for processed files")
    parse_parser.add_argument("output", help="Output directory for parsed CSV files")

    args = parser.parse_args()

    if args.command == "download":
        download_single_feed_once(args.url, args.output)
    elif args.command == "parse":
        parse_single_feed_csv(args.input, args.archive, args.output)

if __name__ == "__main__":
    main()
