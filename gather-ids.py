import requests
import csv
import os
import json
import time

# Constants
BASE_URL = "https://geodaten.schleswig-holstein.de/gaialight-sh/_apps/dladownload/_ajax/details.php?type=alkis&id={}"
OUTPUT_JSON = "responses.json"
OUTPUT_CSV = "responses.csv"
ID_FOLDER = "IDs"

# ANSI escape codes for text styling
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
RED_TEXT = "\033[91m"
GREEN_TEXT = "\033[92m"
YELLOW_TEXT = "\033[93m"
ORANGE_TEXT = "\033[38;5;208m"

# Prepare the output directory for individual IDs
if not os.path.exists(ID_FOLDER):
    os.makedirs(ID_FOLDER)

# For accumulating all responses
all_responses = []

# CSV Setup
csv_file = open(OUTPUT_CSV, "w", newline='', encoding='utf-8')

# Predefined headers based on the given structure
headers = ["success", "status", "gemarkung", "flur", "a_datum", "a_datum_dmy", "quartal", "gemeinde", "ogc_fid", "type"]
csv_writer = csv.DictWriter(csv_file, fieldnames=headers)
csv_writer.writeheader()

for i in range(18172):  # From 0 to 18171
    response = requests.get(BASE_URL.format(i))
    response_data = response.json()

    csv_row = {key: "" for key in headers}  # Initialize csv_row with empty strings

    if not response_data["success"]:
        print(RED_TEXT + f"Error at ID {i}: {response_data.get('message', 'Unknown error')}" + RESET)
        csv_row["success"] = response_data["success"]
        csv_row["status"] = "false"
    else:
        print(GREEN_TEXT + f"Success at ID {i}." + RESET)
        # Append to global list
        all_responses.append(response_data)

        # Write to individual ID file
        with open(os.path.join(ID_FOLDER, f"{i}.txt"), "w") as txt_file:
            json.dump(response_data, txt_file)

        csv_row.update({
            "success": response_data["success"],
            "status": "true"
        })
        csv_row.update(response_data["object"])

    csv_writer.writerow(csv_row)

    # Sleep for 0.1 seconds to ensure not more than 10 requests per second
    time.sleep(0.1)

# Save all responses to JSON
with open(OUTPUT_JSON, "w") as json_file:
    json.dump(all_responses, json_file)

csv_file.close()
