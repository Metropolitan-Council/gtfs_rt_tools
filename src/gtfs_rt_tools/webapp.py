import os
import glob
from flask import Flask, render_template, jsonify
import pandas as pd
import threading
import time
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# Global variable to hold the path of the CSV folder
csv_folder = None

def set_csv_folder(folder_path):
    """Set the folder containing CSV files."""
    global csv_folder
    csv_folder = folder_path
    logging.info(f"CSV folder set to: {csv_folder}")

def get_latest_csv_file():
    """Get the most recent CSV file in the specified folder."""
    if csv_folder:
        csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
        if not csv_files:
            logging.warning("No CSV files found in the specified folder.")
            return None
        latest_file = max(csv_files, key=os.path.getctime)
        logging.info(f"Latest CSV file: {latest_file}")
        return latest_file
    logging.warning("CSV folder not set.")
    return None

def read_vehicle_positions():
    """Read the latest vehicle positions from the CSV file."""
    latest_file = get_latest_csv_file()
    if latest_file:
        try:
            df = pd.read_csv(latest_file)
            columns = ['vehicle_id', 'latitude', 'longitude', 'route_id', 'trip_id', 'vehicle_label']
            result = df[columns].to_dict(orient='records')
            logging.info(f"Read {len(result)} vehicle positions from CSV.")
            
            # Replace NaN values with None (which will be converted to null in JSON)
            for item in result:
                for key, value in item.items():
                    if pd.isna(value):
                        item[key] = None
            
            # Get the logtime value (assuming it's the same for all rows)
            logtime = df['logtime'].iloc[0] if 'logtime' in df.columns else None
            
            return {"logtime": logtime, "vehicles": result}
        except Exception as e:
            logging.error(f"Error reading CSV: {e}")
    return {"logtime": None, "vehicles": []}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vehicle_positions')
def vehicle_positions():
    """API endpoint to get vehicle positions."""
    data = read_vehicle_positions()
    logging.info(f"Returning {len(data['vehicles'])} vehicle positions with logtime: {data['logtime']}")
    return jsonify(data)

def refresh_vehicle_positions():
    """Function to periodically refresh vehicle positions."""
    while True:
        logging.info("Refreshing vehicle positions.")
        time.sleep(30)  # Refresh every 30 seconds

@app.route('/set_folder/<path:folder_path>')
def set_folder(folder_path):
    """API endpoint to set the CSV folder path."""
    set_csv_folder(folder_path)
    return jsonify({"status": "success", "folder": folder_path})

if __name__ == '__main__':
    # Example: set folder for testing, replace with your actual path
    set_csv_folder('/path/to/your/csv/folder')
    # Start the background thread to refresh vehicle positions
    threading.Thread(target=refresh_vehicle_positions, daemon=True).start()
    # Run the app
    try:
        app.run(debug=True)
    except Exception as e:
        logging.error(f"Error running the app: {e}")
