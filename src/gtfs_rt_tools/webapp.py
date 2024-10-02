import os
import glob
from flask import Flask, render_template, jsonify
import pandas as pd
import threading
import time

app = Flask(__name__)

# Global variable to hold the path of the CSV folder
csv_folder = None

def set_csv_folder(folder_path):
    """Set the folder containing CSV files."""
    global csv_folder
    csv_folder = folder_path

def get_latest_csv_file():
    """Get the most recent CSV file in the specified folder."""
    if csv_folder:
        csv_files = glob.glob(os.path.join(csv_folder, '*.csv'))
        if not csv_files:
            return None
        return max(csv_files, key=os.path.getctime)
    return None

def read_vehicle_positions():
    """Read the latest vehicle positions from the CSV file."""
    latest_file = get_latest_csv_file()
    if latest_file:
        try:
            df = pd.read_csv(latest_file)
            # You may want to customize this part based on the structure of your CSV
            return df[['vehicle_id', 'latitude', 'longitude']].to_dict(orient='records')
        except Exception as e:
            print(f"Error reading CSV: {e}")
    return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/vehicle_positions')
def vehicle_positions():
    """API endpoint to get vehicle positions."""
    positions = read_vehicle_positions()
    return jsonify(positions)

def refresh_vehicle_positions():
    """Function to periodically refresh vehicle positions."""
    while True:
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
        print(f"Error: {e}")

