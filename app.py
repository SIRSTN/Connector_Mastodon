import requests
from configparser import ConfigParser
from mastodon import Mastodon
from datetime import datetime, timedelta, timezone
import time
from bs4 import BeautifulSoup

# Load configuration file
config = ConfigParser()
config.read('config.ini')

# Retrieve the credentials
client_id = config.get('mastodon', 'client_id')
client_secret = config.get('mastodon', 'client_secret')
access_token = config.get('mastodon', 'access_token')
api_base_url = config.get('mastodon', 'api_base_url')

# Authenticate with Mastodon API
mastodon = Mastodon(
    client_id=client_id,
    client_secret=client_secret,
    access_token=access_token,
    api_base_url=api_base_url
)

# Keywords for Mastodon search
keywords = ["Bitcoin", "BTC"]

# Define the timeframe of the last 12 hours
timeframe_start = datetime.now(timezone.utc) - timedelta(hours=12)

# API URL to send data
api_url = "http://localhost:5000/store-text"

# List to store entries to be sent to the API
entries_to_store = []

# Initialize a counter for comment numbers
toot_number = 0

# For each keyword, perform the search and process the results
for keyword in keywords:
    max_id = None  # Initialize max_id for pagination
    keep_searching = True

    while keep_searching:
        # Search for the keyword in Mastodon
        search_result = mastodon.search(q=keyword, max_id=max_id, resolve=False)
        toots = search_result['statuses']
        
        if not toots:
            break

        # Loop over found toots and process them
        for toot in toots:
            toot_date = toot['created_at']

            # If the toot is older than 12 hours, stop processing
            if toot_date < timeframe_start:
                keep_searching = False
                break

            # Use BeautifulSoup to extract text (if you want to strip HTML tags)
            soup = BeautifulSoup(toot['content'], 'html.parser')
            toot_content = soup.get_text()

            # Print the comment number and the toot content
            toot_number += 1
            print(f"Toot #{toot_number}:")
            print(toot_content)
            print()

            # Create the entry for each toot
            entry = {
                'user': toot['account']['username'],
                'text': toot_content,
                'date': toot_date.isoformat()  # No need to convert as it's already a datetime object
            }

            entries_to_store.append(entry)

        # If we have processed all toots or found an old toot, stop searching
        if not keep_searching or len(toots) < 40:  # Assuming default Mastodon API pagination size
            break

        # Set max_id to the ID of the last toot for the next pagination batch
        max_id = toots[-1]['id']

        # Avoid hitting the rate limit
        time.sleep(1)

# Send the collected toot data to the local API
if entries_to_store:
    # Prepare the data for the API request
    data_to_send = {
        'source': 'Mastodon',
        'keyword': 'Bitcoin',
        'entries': entries_to_store
    }

    # Send a POST request to the API with the toot data
    response = requests.post(api_url, json=data_to_send)
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print("Error response:", response.text)
else:
    print("No new toots found in the last 12 hours.")
