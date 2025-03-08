import requests
import csv
import os
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import configparser

API_KEY = ""
# The ID and range of the spreadsheet.
SPREADSHEET_ID = '1fT3rfQ0r1VjWcBV0_74xK85n3ATZNL9OW8CRoJcW1RI'
RANGE_NAME = 'Лист1!A2:F'
song_col=2
artist_col=1

# Authentication
def authenticate_gsheet():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json',  # Path to your credentials.json file
                ['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

def read_google_sheet():
    # Authenticate and create the API client
    creds = authenticate_gsheet()
    service = build('sheets', 'v4', credentials=creds)
    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    rows = result.get('values', [])
    return rows

# Function to get song genre from Last.fm
def get_song_genre(song_name, artist_name):
    # Initialize the parser
    config = configparser.ConfigParser()
    # Read the ini file
    config.read('path/to/your/config.ini')
    # Retrieve the API key from the 'settings' section
    API_KEY = config.get('settings', 'api_key')
    url = f"http://ws.audioscrobbler.com/2.0/?method=track.getTopTags&api_key={API_KEY}&artist={artist_name}&track={song_name}&format=json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "toptags" in data and "tag" in data["toptags"]:
            return ", ".join([tag["name"] for tag in data["toptags"]["tag"][:15]])  # Get top 15 tags
        else:
            return "Unknown"
    return "Error fetching data"

# Function to get country of artist from wikidata
def get_artist_country(artist_name):
    # Step 1: Search for the artist on Wikidata using their name
    search_url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&format=json&search={artist_name}&language=en"
    search_response = requests.get(search_url)
    search_data = search_response.json()

    if search_data.get('search'):
        # Step 2: Get the first result, assuming it's the correct artist
        artist_entity_id = search_data['search'][0]['id']
        
        # Step 3: Fetch detailed data about the artist using the entity ID
        entity_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={artist_entity_id}&props=claims"
        entity_response = requests.get(entity_url)
        entity_data = entity_response.json()

        # Step 4: Look for country information (P495 is the property ID for country)
        claims = entity_data['entities'][artist_entity_id].get('claims', {})
        country_claims = claims.get('P495', [])

        if country_claims:
            country_id = country_claims[0]['mainsnak']['datavalue']['value']['id']
            country_url = f"https://www.wikidata.org/w/api.php?action=wbgetentities&format=json&ids={country_id}&props=labels&languages=en"
            country_response = requests.get(country_url)
            country_data = country_response.json()
            country_name = country_data['entities'][country_id]['labels']['en']['value']
            return country_name
        else:
            return "TO_FIND"
    else:
        return "TO_FIND"

def process_songs(output_csv_file):
    rows = read_google_sheet()  # Get data from Google Sheets
    # Open the output CSV file
    with open(output_csv_file, mode='w', newline='', encoding='utf-8') as outfile:
        csv_writer = csv.writer(outfile)
        # Write the header to the output file
        csv_writer.writerow(['Artist', 'Song', 'Genres'])
        # Loop through the rows from Google Sheets
        for row in rows: 
            # Extract artist and song information from the row           
            artist = row[artist_col]
            song = row[song_col]
            # Get genres for the song and artist
            genres = get_song_genre(song, artist)
            # Split genres into a list
            genres_list = genres.split(', ')  # Split genres by commas
            # Write the result to the output CSV file
            for genre in genres_list:
                if genre!='':
                    print(artist+" "+song+" "+genre)
                    # Write the result to the output CSV file
                    csv_writer.writerow([artist, song, genre.lower()])

def process_distinct_artists(output_csv_file):
    rows = read_google_sheet()  # Get data from Google Sheets
    with open(output_csv_file, mode='w', newline='', encoding='utf-8') as outfile:
        # Create a CSV writer object for the output file
        csv_writer = csv.writer(outfile)
        # Write the header to the output file
        csv_writer.writerow(['Artist'])
        artists_list=set()
        # Loop through the rows from Google Sheets
        for row in rows: 
            # Extract artist and song information from the row           
            artist = row[artist_col]
            # Add artist to set
            artists_list.add(artist)
        for artist in artists_list:
            # Write the result to the output CSV file
            csv_writer.writerow([artist])

def process_artists_countries(input_csv_file, output_csv_file):
    with open(input_csv_file, mode='r', encoding='utf-8') as infile,open(output_csv_file, mode='w', newline='', encoding='utf-8') as outfile:
        # Read the CSV file
        csv_reader = csv.reader(infile)
        # Create a CSV writer object for the output file
        csv_writer = csv.writer(outfile)
        # Write the header to the output file
        csv_writer.writerow(['Artist','Country'])
        # Skip the header row for input file
        next(csv_reader)
        # Loop through all rows in the input CSV
        for row in csv_reader:
            # Extract artist from the row
            artist = row[0]
            # Get country info for the artist
            country = get_artist_country(artist)# Get country for the artist
            # Write the result to the output CSV file
            csv_writer.writerow([artist, country])
            if country=='TO_FIND':
                print(artist+" "+country)
            if country=='TO_FIND':
                print(artist+" "+country)

output_csv_file = 'output_with_genres.csv'
process_songs(output_csv_file)

output_csv_file = 'output_artists.csv'
process_distinct_artists(output_csv_file)

input_csv_file = 'output_artists.csv'
output_csv_file = 'output_artists_countries.csv'
process_artists_countries(input_csv_file,output_csv_file)