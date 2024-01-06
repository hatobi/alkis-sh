import os
import zipfile
import subprocess
import glob
import datetime
import gzip
import csv

# ANSI escape codes for text styling
RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"
RED_TEXT = "\033[91m"
GREEN_TEXT = "\033[92m"
YELLOW_TEXT = "\033[93m"
ORANGE_TEXT = "\033[38;5;208m"

def read_processed_database(csv_file, log):
    """Reads the CSV database and returns a set of processed (flur, ogc_id) tuples."""
    processed = set()
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        log_entry = "Database successfully loaded."
        print(GREEN_TEXT + BOLD + log_entry + RESET)
        log.write(log_entry + "\n")
        for row in reader:
            if row['status'] == 'converted' and row['target_format'] == 'shapes':
                processed.add((row['flur'], row['ogc_id']))
    return processed

def extract_variables_from_zip(zip_filename, log):
    """Extract variables (ogc_id and flur_id) from the ZIP filename."""
    parts = zip_filename.split('_')
    ogc_id = parts[1].split('-')[1]
    flur_id = parts[2].split('-')[1]
    log_message = f"Extracted OGC ID: {ogc_id}, Flur ID: {flur_id} from ZIP filename: {zip_filename}"
    print(log_message)
    log.write(log_message + "\n")
    return ogc_id, flur_id

def extract_gz_from_zip(zip_filepath, log):
    """Extract the GZ (gzipped XML) file from the ZIP and return its filename."""
    with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
        gz_files = [f for f in zip_ref.namelist() if f.endswith('.xml.gz')]
        if not gz_files:
            log_message = f"No XML.GZ file found in ZIP: {zip_filepath}"
            print(log_message)
            log.write(log_message + "\n")
            return None
        for file in gz_files:
            zip_ref.extract(file, path='extracted')
            log_message = f"Extracted XML.GZ file: {file} from ZIP: {zip_filepath}"
            print(log_message)
            log.write(log_message + "\n")
            return file  # Assuming only one XML.GZ file per ZIP
    return None

def extract_xml_from_gz(gz_filepath, log):
    """Extract the XML file from the GZ file and return its filename."""
    xml_filename = gz_filepath.replace('.gz', '')
    with gzip.open(gz_filepath, 'rb') as f_in:
        with open(xml_filename, 'wb') as f_out:
            f_out.write(f_in.read())
        log_message = f"Extracted XML file from GZ: {xml_filename}"
        print(log_message)
        log.write(log_message + "\n")
        return xml_filename

def convert_xml_to_shape(xml_filename, ogc_id, flur_id, log):
    """Convert XML to shapefile using ogr2ogr and rename and move shapefiles."""
    output_folder = f'converted/converted_shapes_{flur_id}_{ogc_id}'
    os.makedirs(output_folder, exist_ok=True)
    cmd = f'ogr2ogr -f "ESRI Shapefile" {output_folder} {xml_filename} --config OGR2OGR_SKIP_FAILURES YES --config OGR2OGR_WARN_ON_FAILURE YES'
    subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)  # Suppress warnings

    # Rename and move shapefiles and associated files
    for shapefile in glob.glob(f'{output_folder}/*.shp'):
        base_filename = os.path.splitext(os.path.basename(shapefile))[0]
        for extension in ['.shp', '.shx', '.dbf', '.prj', '.cpg', '.sbn', '.sbx']:
            original_file = os.path.join(output_folder, base_filename + extension)
            if os.path.exists(original_file):
                attribute = base_filename
                new_filename = f"{flur_id}-{ogc_id}-{attribute}{extension}"
                sorted_folder = os.path.join('sorted', attribute)
                os.makedirs(sorted_folder, exist_ok=True)

                new_filepath = os.path.join(sorted_folder, new_filename)
                os.rename(original_file, new_filepath)
                log_message = f"Converted and moved file: {original_file} to {new_filepath}"
                print(log_message)
                log.write(log_message + "\n")

def rename_and_sort_shapefiles(shapefiles, flur_id, ogc_id, log):
    """Rename and sort shapefiles into subfolders."""
    for shapefile in shapefiles:
        attribute = os.path.basename(shapefile).replace('.shp', '')
        new_filename = f"{flur_id}-{ogc_id}-{attribute}.shp"
        sorted_folder = os.path.join('sorted', attribute)
        os.makedirs(sorted_folder, exist_ok=True)
        new_filepath = os.path.join(sorted_folder, new_filename)

        os.rename(shapefile, new_filepath)
        log_message = f"Renamed and moved Shapefile: {shapefile} to {new_filepath}"
        print(log_message)
        log.write(log_message + "\n")

def process_zip_files(csv_database):
    """Process all ZIP files in the given folder."""
    log_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    print(BOLD + f'Log timestamp: {log_time}' + RESET)

    with open('path.txt', 'r') as path_file:
        folder_path = path_file.read().strip()  # Read and strip any trailing newline or spaces

    log_folder = "log"
    os.makedirs(log_folder, exist_ok=True)
    log_file = os.path.join(log_folder, f'process_log_{log_time}.txt')

    with open(log_file, 'w') as log:
        processed = read_processed_database(csv_database, log)
        total_processed = 0
        total_skipped = 0
        total_converted = 0

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                log_entry = "==== Next file ===="
                print("\n" + BOLD + log_entry + RESET)
                log.write("\n" + log_entry + "\n")

                log_entry = f"Found file {file}."
                print(log_entry)
                log.write(log_entry + "\n")
                if file.endswith('.zip'):
                    
                    log_entry = f"File is ZIP-file."
                    print(log_entry)
                    log.write(log_entry + "\n")

                    zip_filepath = os.path.join(root, file)
                    ogc_id, flur_id = extract_variables_from_zip(file, log)
                    
                    # Check if already processed
                    if (flur_id, ogc_id) not in processed:

                        log_entry = f"{file} not in processed database"
                        print(log_entry)
                        log.write(log_entry + "\n")

                        gz_filename = extract_gz_from_zip(zip_filepath, log)

                        log_entry = f"{gz_filename} extracted."
                        print(log_entry)
                        log.write(log_entry + "\n")

                        if gz_filename:
                            gz_path = os.path.join('extracted', gz_filename)
                            xml_filename = extract_xml_from_gz(gz_path, log)
                            conversion_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                            convert_xml_to_shape(xml_filename, ogc_id, flur_id, log)

                            log_entry = f"{datetime.datetime.now()}: Processed ZIP file: {file}"
                            print(BOLD + GREEN_TEXT + log_entry + RESET)
                            log.write(log_entry + "\n")

                            # Update processed set and CSV database
                            processed.add((flur_id, ogc_id))
                            total_converted += 1
                            intermediate_summary = (f"Processed: {total_processed}\n"
                                                f"Converted: {total_converted}\n"
                                                f"Skipped: {total_skipped}")
                            print(BOLD + intermediate_summary + RESET)
                            log.write(intermediate_summary + "\n")

                            with open(csv_database, mode='a', newline='', encoding='utf-8') as db_file:
                                db_writer = csv.writer(db_file)
                                db_writer.writerow(['converted', 'shapes', flur_id, ogc_id, conversion_time])
                    else:
                        log_entry = f"Skipped already processed ZIP file: {file}"
                        print(BOLD + ORANGE_TEXT + log_entry + RESET)
                        log.write(log_entry + "\n")
                        total_skipped += 1

                        intermediate_summary = (f"Processed: {total_processed}\n"
                                                f"Converted: {total_converted}\n"
                                                f"Skipped: {total_skipped}")
                        print(BOLD + intermediate_summary + RESET)
                        log.write(intermediate_summary + "\n")

                    total_processed += 1
        
        # Summary at the end
        summary = (f"\nTotal ZIP files processed: {total_processed}\n"
                   f"Total files converted: {total_converted}\n"
                   f"Total files skipped: {total_skipped}")
        print(BOLD + summary + RESET)
        log.write(summary + "\n")

    print(GREEN_TEXT + BOLD + "Finished conversion" + RESET)
# Example usage
csv_database = 'convert-db.csv'
process_zip_files(csv_database)
