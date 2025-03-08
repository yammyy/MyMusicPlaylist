import csv
import os
import shutil

def copy_file_from_downloads(filename):
    """Copies a file from the Downloads folder to the current working directory."""
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads", filename)
    destination_path = os.path.join(os.getcwd(), 'file1.csv')
    
    if os.path.exists(downloads_path):
        shutil.copy(downloads_path, destination_path)
        print(f"File '{filename}' copied from Downloads to current folder.")
    else:
        print(f"File '{filename}' not found in Downloads.")

def read_csv(file_path):
    """Reads a CSV file and returns a list of rows."""
    with open(file_path, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        data = list(reader)
    return data

def write_csv(file_path, data):
    """Writes data to a CSV file."""
    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerows(data)

def append_missing_rows(file1, file2):
    """Appends rows from file2 to file1 if their first column values are not already present."""
    data1 = read_csv(file1)
    data2 = read_csv(file2)
    
    # Extract first column values for comparison (excluding headers)
    existing_first_column = set(row[0] for row in data1[1:] if row)
    new_rows = [row for row in data2[1:] if row and row[0] not in existing_first_column]
    
    if new_rows:
        with open(file1, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(new_rows)
        print(f"Appended {len(new_rows)} new rows to {file1}")
    else:
        print("No new rows to append.")

file_to_copy = "output_artists_countries.csv"
copy_file_from_downloads(file_to_copy)

file1 = "file1.csv"
file2 = "output_artists_countries.csv"
append_missing_rows(file1, file2)
