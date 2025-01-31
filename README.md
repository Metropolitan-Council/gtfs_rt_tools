# GTFS-realtime Tools

This is a Python package and CLI tool used to download, process, and archive GTFS-realtime feeds.

## Current Functionality

### Download

- download GTFS-realtime .pb files to date-partitioned archives at a given interval
      - currently requires a base URL that matches for all feed types (ie metrotransit.org/svc/tripupdates.pb and metrotransit.org/svc/vehiclepositions.pb)
  
### Parse

- can parse a single .pb file to CSV
- can parse the outputs of the `download` command, keeping date-archived structure for archived .pb files and processed CSV files

### View

- display VehiclePositions feed on a map, refreshing to use the most recently produced CSV file
- very shaky feed comparison tool, needs quite a bit of work
    - goal is to be able to use tool to compare contents of feeds from different sources (CAD/AVL vendor vs. prediction vendor, test vs. prod, etc.)

## Planned Functionality

I want to introduce a bit more flexibility in the download/parse process. The CLI tool should make it easy to download and parse a single feed as well as multiple feeds. The current approach of a date-structured archive seems to work well for many purposes, but can be overkill for quicker checks. Some of this is CLI design, some of it is providing simple one-liner examples, and I think there's some wiggle room here. I don't want a million CLI options like `download`, `download-parse`, `download-parse-view`, etc. but I want to make it really easy to spin up monitoring or checking at each level.

I want to be able to enrich the feed results with static GTFS as well. CSVs could be matched to various static components in real time as part of the parsing process.

I also want to build out a web app platform (whether Shiny or something else) that allows a broader range of users to conduct these checks. Something as simple as "put in a feed URL and download a CSV" could be massively helpful. The map-based tool has a lot of potential as well, but I'd like to join it to TripUpdates and the static schedule to get more out of it. Using the archived CSV approach, a map tool could also have a built-in playback feature. I imagine something like watching a live broadcast, where you can scrub backwards and replay, but then hit "Live" and jump to a live view. I want to include all sorts of filters here for vehicle, trip, stop, etc. For UI, [Pantograph](https://pantographapp.com/minneapolis/map) is a fantastic example, I really love that when you click on a vehicle, you get to see its whole pattern. I think this could be inspiration for a less customer-focused, more agency-focused tool.

It might be useful to allow some basic slicing and dicing, like creating a CSV that tracks a single vehicle or trip_id for a time series, rather than just showing a snapshot of all vehicles/trips at one point in time. I think this plus some filtering could allow for a low/no code tool that could get an end user a much more workable dataset. Eyeballing a full TripUpdates feed is pretty challenging, eyeballing a single trip over time is much more doable.

I also want to set up a .config file type of approach, so users can keep common feeds in there and refer to them without typing the whole URL out every time. Lots of other room in .config for standard download intervals, custom processes (ie download every 10 seconds and parse), etc.

We could possibly extend the .config approach to something like a .validations file, where users can define rules that could be checked for. Things like "vehicles whose positions have not changed for X amount of time", "vehicles with more than 1 location", "trip IDs used on multiple vehicles at once", etc. This starts to get a bit dicey, because there are so many ways to express these things. Could be Python statements, SQL, something else? Maybe this is unnecessary and just providing CSVs is enough to allow a broad set of users to ask these questions.
