import requests
import pandas as pd
import time
import random
from datetime import date
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")
  # GitHub Action will inject this

SEARCH_QUERIES = [
    "vc podcast", "venture capital podcast", "startup investing",
    "seed fund podcast", "angel investor podcast", "early stage investing",
    "startup pitch", "tech investor podcast"
]

MAX_RESULTS_PER_DAY = 150
RESULTS_PER_PAGE = 50

def search_channel_ids(query, limit=150):
    channel_ids = set()
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'type': 'channel',
        'q': query,
        'maxResults': RESULTS_PER_PAGE,
        'key': API_KEY
    }

    fetched = 0
    while fetched < limit:
        response = requests.get(url, params=params).json()
        items = response.get('items', [])
        for item in items:
            channel_ids.add(item['snippet']['channelId'])
        fetched += len(items)
        if 'nextPageToken' not in response or fetched >= limit:
            break
        params['pageToken'] = response['nextPageToken']
        time.sleep(0.5)
    return list(channel_ids)

def get_channel_details(channel_ids):
    url = 'https://www.googleapis.com/youtube/v3/channels'
    all_data = []
    for i in range(0, len(channel_ids), 50):
        batch_ids = channel_ids[i:i+50]
        params = {
            'part': 'snippet,statistics',
            'id': ','.join(batch_ids),
            'key': API_KEY
        }
        response = requests.get(url, params=params).json()
        for item in response.get('items', []):
            title = item['snippet']['title']
            channel_url = f"https://www.youtube.com/channel/{item['id']}"
            subs = item['statistics'].get('subscriberCount', 'Hidden')
            all_data.append([title, channel_url, subs])
        time.sleep(0.5)
    return all_data

def run():
    today = date.today().isoformat()
    all_leads = []
    random.shuffle(SEARCH_QUERIES)

    print("✅ API Key loaded:", bool(API_KEY))  # ← shows if the key was passed correctly

    fetched = 0
    for query in SEARCH_QUERIES:
        print(f"🔍 Searching for: {query}")
        to_fetch = min(MAX_RESULTS_PER_DAY - fetched, RESULTS_PER_PAGE * 3)
        ids = search_channel_ids(query, to_fetch)
        print(f"→ Found {len(ids)} channels for: {query}")
        details = get_channel_details(ids)
        all_leads.extend(details)
        fetched += len(details)
        if fetched >= MAX_RESULTS_PER_DAY:
            break

    print(f"📦 Total leads collected: {len(all_leads)}")

    df = pd.DataFrame(all_leads, columns=["Channel Name", "Channel URL", "Subscriber Count"])
    df.drop_duplicates(subset=["Channel URL"], inplace=True)
    filename = f"vc_leads_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ CSV generated: {filename}")

    
    fetched = 0
    for query in SEARCH_QUERIES:
        print(f"Searching for: {query}")
        to_fetch = min(MAX_RESULTS_PER_DAY - fetched, RESULTS_PER_PAGE * 3)
        ids = search_channel_ids(query, to_fetch)
        details = get_channel_details(ids)
        all_leads.extend(details)
        fetched += len(details)
        if fetched >= MAX_RESULTS_PER_DAY:
            break

    df = pd.DataFrame(all_leads, columns=["Channel Name", "Channel URL", "Subscriber Count"])
    df.drop_duplicates(subset=["Channel URL"], inplace=True)
    filename = f"vc_leads_{today}.csv"
    df.to_csv(filename, index=False)
    print(f"✅ {len(df)} leads saved to {filename}")

if __name__ == "__main__":
    run()
