import requests
import pandas as pd
import time
import random
from datetime import datetime, timedelta, date
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")

SEARCH_QUERIES = [
    "vc podcast", "venture capital podcast", "startup investing",
    "seed fund podcast", "angel investor podcast", "early stage investing",
    "startup pitch", "tech investor podcast", "founder interviews", "startup accelerator",
    "funding podcast", "startup AMA", "startup mentors", "bootstrap founder podcast",
    "angel network", "SaaS VC", "web3 VC", "fintech investor", "startup pitch event"
]

MAX_RESULTS_PER_DAY = 200
RESULTS_PER_PAGE = 50
HISTORY_FILE = "history.csv"
PUBLISHED_AFTER_DAYS = 180  # Fetch videos only from last 6 months

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Channel Name", "Channel URL", "Subscriber Count", "Date Added"])

def save_history(df_history):
    df_history.to_csv(HISTORY_FILE, index=False)

def search_channel_ids(query, limit=150):
    channel_ids = set()
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'type': 'channel',
        'q': query,
        'maxResults': RESULTS_PER_PAGE,
        'key': API_KEY,
        'publishedAfter': (datetime.utcnow() - timedelta(days=PUBLISHED_AFTER_DAYS)).isoformat("T") + "Z"
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
    today_str = date.today().isoformat()
    all_leads = []
    seen_urls = set()
    random.shuffle(SEARCH_QUERIES)

    # Load historical memory
    history_df = load_history()
    seen_urls.update(history_df["Channel URL"].tolist())

    fetched = 0
    for query in SEARCH_QUERIES:
        to_fetch = min(MAX_RESULTS_PER_DAY - fetched, RESULTS_PER_PAGE * 3)
        ids = search_channel_ids(query, to_fetch)
        details = get_channel_details(ids)
        for name, url, subs in details:
            if url not in seen_urls and fetched < MAX_RESULTS_PER_DAY:
                all_leads.append([name, url, subs, today_str])
                seen_urls.add(url)
                fetched += 1
        if fetched >= MAX_RESULTS_PER_DAY:
            break

    # Save daily file
    if all_leads:
        df_new = pd.DataFrame(all_leads, columns=["Channel Name", "Channel URL", "Subscriber Count", "Date Added"])
        filename = f"vc_leads_{today_str}.csv"
        df_new.to_csv(filename, index=False)
        print(f"✅ {len(df_new)} new leads saved to {filename}")

        # Append to history
        updated_history = pd.concat([history_df, df_new], ignore_index=True)
        save_history(updated_history)
    else:
        print("⚠️ No new leads found today.")

    if fetched < MAX_RESULTS_PER_DAY:
        print(f"ℹ️ Only {fetched} unique leads were found today (goal: {MAX_RESULTS_PER_DAY})")

if __name__ == "__main__":
    run()
