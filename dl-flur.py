import csv
import requests
import time
import logging
import os
from datetime import datetime
from collections import defaultdict

# Script version
script_version = 'v2.0'
print(script_version)
time.sleep(1)

# Get current timestamp and format it
current_time = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")

# Define headers as a dictionary
HEADERS = {
    "Host": "geodaten.schleswig-holstein.de",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Connection": "keep-alive",
    "Referer": "https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/dl-alkis.html",
}

# Use headers in requests
#response = requests.get(check_url, headers=HEADERS)

# Create 'download' directory if not exists
if not os.path.exists("download"):
    os.makedirs("download")

# Setup logging
logging.basicConfig(filename=f'download-log_{current_time}.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_and_print(message):
    """Prints and logs a message simultaneously"""
    print(message)
    logging.info(message)

def download_file(url, ogc_fid, flur, download_id):
    filename = f"ogc_fid-{ogc_fid}_flur-{flur}_downloadID-{download_id}.zip"
    path_to_save = os.path.join("download", filename)  # Save into the 'download' subfolder
    response = requests.get(url, headers=HEADERS, stream=True)
    with open(path_to_save, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)

def get_successful_downloads():
    success_ids = set()
    try:
        with open('download_ids.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Download Status'] == 'Success':
                    success_ids.add((row['Flur'], row['OGC FID']))
    except FileNotFoundError:
        pass  # File may not exist on first run
    return success_ids

def chunks(lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

def main():
    initial_wait_time = 5
    wait_time = initial_wait_time
    print(f"Wait time: {wait_time} seconds")
    multiplier = 1.2
    print(f"Multiplier: {multiplier}")
    termination_threshold = 50
    print(f"Terminated after: {termination_threshold} tries")
    chunk_size = 20
    print(f"Chunk size: {chunk_size}")

    successful_downloads = get_successful_downloads()
    print("Load successful: download_ids.csv")
    time.sleep(1)

    download_attempts = defaultdict(int)
    print("Load successful: downloads into defaultdict")
    time.sleep(1)

    # Load the CSV with all IDs
    ids = []
    responses_filename = 'responses.csv'
    with open(responses_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            ids.append((row['flur'], row['ogc_fid']))
    print(f"Loaded {responses_filename}.")
    time.sleep(1)

    # Filtering out already successful IDs
    ids = [i for i in ids if i not in successful_downloads]
    print("Successfully filtered IDs")
    time.sleep(1)

    for chunked_ids in chunks(ids, chunk_size):

        download_ids = []
        download_results = {}

        for flur, ogc_fid in chunked_ids:
            # Send a download request
            log_and_print(f"Sending download request for flur: {flur}, ogc_fid: {ogc_fid}")
            url = f"https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/multi.php?url={flur}.xml.gz&buttonClass=file1&id={ogc_fid}&type=alkis&action=start"
            response = requests.get(url).json()

            download_id = None
            if response.get("success"):
                download_results[download_id] = False
                download_id = response.get("id")
                download_ids.append((download_id, ogc_fid, flur))
                log_and_print(f"Received download ID: {download_id}")
            else:
                log_and_print(f"Failed to get download ID for flur: {flur}, ogc_fid: {ogc_fid}")

        
        # Save the download IDs, ogc_fid, and flur to a CSV
        file_name = 'download_ids.csv'

        with open(file_name, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            write_header = not os.path.exists(file_name)
            if write_header:
                writer.writerow(['Download ID', 'OGC FID', 'Flur', 'Download Status', 'Download Attempts', 'Download Time'])

            # Send a download request to the download ID every x seconds
            for download_id, ogc_fid, flur in download_ids:
                while True:
                    download_attempts[download_id] += 1
                    log_and_print(f"Checking download status for ID: {download_id}. Download attempt {download_attempts[download_id]}")

                    if download_attempts[download_id] > termination_threshold:
                        log_and_print(f"Terminating after {termination_threshold} unsuccessful attempts for ID: {download_id}.")
                        return

                    check_url = f"https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/multi.php?action=status&job={download_id}&_=1698319514025"
                    response = requests.get(check_url, headers=HEADERS)
                
                    # Check if the response is JSON
                    try:
                        data = response.json()
                    except ValueError:
                        log_and_print(f"Invalid JSON response for ID: {download_id}. Retrying...")
                        log_and_print(f"Response content: {response.content}")  # Log the actual response content
                        time.sleep(wait_time)
                        wait_time *= multiplier
                        continue

                    if data.get("status") == "done":
                        log_and_print(f"Downloading file for ID: {download_id}")
                        download_file(data.get("downloadUrl"), ogc_fid, flur, download_id)
                        download_results[download_id] = True
                        success_status = 'Success' if download_results[download_id] else 'Failed'
                        
                        download_timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
                        
                        writer.writerow([download_id, ogc_fid, flur, success_status, download_attempts[download_id], download_timestamp])
                        break
                    elif data.get("status") == "wait":
                        log_and_print(f"Waiting for download ID: {download_id} to be ready")
                        log_and_print(f"Response content: {response.content.decode('utf-8')}")  # Log the actual response content
                        print(f"Waiting {round(wait_time, 2)} seconds before next attempt.")
                        time.sleep(wait_time)
                        wait_time *= multiplier
                    else:
                        log_and_print(f"Error for download ID: {download_id}")
                        break                
        
        # Optional: Clear the download_ids list to be ready for the next chunk
        download_ids.clear()
        wait_time = initial_wait_time
        print(f"Wait time reset to {initial_wait_time}.")

        wait_time_after_download = 5
        print(f"Waiting {wait_time_after_download} seconds before next chunk.")
        time.sleep(wait_time_after_download)

if __name__ == "__main__":
    main()
