import os
import re
from datetime import datetime
import requests

def sanitize_filename(filename):
    return re.sub(r'[^a-zA-Z0-9]', '_', filename)

def get_timestamped_filename(url):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    sanitized_url = sanitize_filename(url)
    return f"{sanitized_url}_{timestamp}.pb"

def download_file(url, save_path):
    headers = {}
    if 'https://api.goswift.ly' in url:
        swiftly_api_key = os.environ.get('SWIFTLY_API')
        if not swiftly_api_key:
            raise ValueError("SWIFTLY_API environmental variable is not set")
        headers['Authorization'] = swiftly_api_key

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    with open(save_path, 'wb') as file:
        file.write(response.content)

