from .download import download_file
from .parse import parse_trip_updates
from .process import download_single_feed_once
def download_feed() -> None:
    download_single_feed_once("https://svc.metrotransit.org/mtgtfs/", out_dir = "./test_feed")
