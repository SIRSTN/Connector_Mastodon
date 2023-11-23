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

# Keywords for Bitcoin and Ethereum Mastodon search
keywords_bitcoin = ["Bitcoin", "BTC"]
keywords_ethereum = ["Ethereum", "ETH"]

# Define the timeframe of the last 12 hours
timeframe_start = datetime.now(timezone.utc) - timedelta(hours=12)

# API URL to send data
api_url = "http://localhost:5000/store-text"

# Function to process Mastodon posts
def process_mastodon_posts(toots, keywords):
    entries_to_store = []
    toot_number = 0
    for toot in toots:
        toot_date = toot['created_at']

        # Skip toots that are older than the timeframe_start
        if toot_date < timeframe_start:
            continue

        soup = BeautifulSoup(toot['content'], 'html.parser')
        toot_content = soup.get_text()

        toot_number += 1
        print(f"Toot #{toot_number}:")
        print(toot_content)
        print()

        entry = {
            'user': toot['account']['username'],
            'text': toot_content,
            'date': toot_date.isoformat()
        }

        entries_to_store.append(entry)
    
    return entries_to_store

# Function to search and process toots
def search_mastodon(keywords):
    entries_to_store = []
    for keyword in keywords:
        max_id = None
        keep_searching = True

        while keep_searching:
            search_result = mastodon.search(q=keyword, max_id=max_id, resolve=False)
            toots = search_result['statuses']

            if not toots:
                break

            processed_entries = process_mastodon_posts(toots, keywords)
            entries_to_store.extend(processed_entries)

            if not keep_searching or len(toots) < 40:
                break

            max_id = toots[-1]['id']
            time.sleep(1)
    
    return entries_to_store

# Function to send data to API
def send_to_api(entries, source, keyword):
    if entries:
        data = {
            'source': source,
            'keyword': keyword,
            'entries': entries
        }
        response = requests.post(api_url, json=data)
        print(f"{source} - {keyword} Search - Status Code:", response.status_code)
        if response.status_code == 200:
            print(f"{source} - {keyword} Search - Response:", response.json())
        else:
            print(f"{source} - {keyword} Search - Error response:", response.text)
    else:
        print(f"No new {keyword} posts found from {source} in the last 12 hours.")

# Search for Bitcoin related toots and send them to the API
btc_entries = search_mastodon(keywords_bitcoin)
send_to_api(btc_entries, 'Mastodon', 'Bitcoin')

# Search for Ethereum related toots and send them to the API
eth_entries = search_mastodon(keywords_ethereum)
send_to_api(eth_entries, 'Mastodon', 'Ethereum')
