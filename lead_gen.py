import requests
import pandas as pd
import time
import random
from datetime import date
import os

API_KEY = os.getenv("YOUTUBE_API_KEY")
if not API_KEY:
    raise ValueError("❌ Missing YOUTUBE_API_KEY environment variable")

SEARCH_QUERIES = [
    "vc podcast", "startup podcast", "venture capital interview",
    "founder podcast", "startup pitch", "angel investor interview"
]

VIDEO_KEYWORDS = ["podcast", "episode", "ep.", "interview", "talk", "pitch", "founder"]
CHANNEL_KEYWORDS = ["vc", "venture", "capital", "investor", "startup", "angel", "accelerator", "seed"]

MAX_LEADS = 5
RESULTS_PER_PAGE = 50
HISTORY_FILE = "history.csv"

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Channel Name", "Channel URL", "Subscriber Count", "Date Added"])

def save_history(df_history):
    df_history.to_csv(HISTORY_FILE, index=False)

def search_videos(query):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "type": "video",
        "q": query,
        "maxResults": RESULTS_PER_PAGE,
        "key": API_KEY
    }
    response = requests.get(url, params=params).json()
    return response.get("items", [])

def is_valid_video(snippet):
    text = (snippet.get("title", "") + " " + snippet.get("description", "")).lower()
    return any(keyword in text for keyword in VIDEO_KEYWORDS)

def get_channel_details(channel_ids):
    url = "https://www.googleapis.com/youtube/v3/channels"
    all_data = []

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i+50]
        params = {
            "part": "snippet,statistics,brandingSettings",
            "id": ",".join(batch),
            "key": API_KEY
        }
        response = requests.get(url, params=params).json()
        for item in response.get("items", []):
            branding = item.get("brandingSettings", {}).get("channel", {})
            country = branding.get("country", "").upper()
            if country == "IN":
                continue

            title = item["snippet"]["title"].lower()
            description = item["snippet"].get("description", "").lower()
            if not any(k in title or k in description for k in CHANNEL_KEYWORDS):
                continue

            url = f"https://www.youtube.com/channel/{item['id']}"
            subs = item["statistics"].get("subscriberCount", "Hidden")
            all_data.append([item["snippet"]["title"], url, subs])
        time.sleep(0.5)
    return all_data

def run():
    today_str = date.today().isoformat()
    seen_urls = set()
    all_leads = []

    history_df = load_history()
    seen_urls.update(history_df["Channel URL"].tolist())

    random.shuffle(SEARCH_QUERIES)
    found_channels = set()

    for query in SEARCH_QUERIES:
        videos = search_videos(query)
        for video in videos:
            snippet = video["snippet"]
            if not is_valid_video(snippet):
                continue

            channel_id = snippet["channelId"]
            found_channels.add(channel_id)

        if len(found_channels) >= MAX_LEADS * 2:
            break

    channel_details = get_channel_details(list(found_channels))

    for name, url, subs in channel_details:
        if url not in seen_urls and len(all_leads) < MAX_LEADS:
            all_leads.append([name, url, subs, today_str])
            seen_urls.add(url)

    if all_leads:
        df = pd.DataFrame(all_leads, columns=["Channel Name", "Channel URL", "Subscriber Count", "Date Added"])
        filename = f"vc_podcast_leads_{today_str}.csv"
        df.to_csv(filename, index=False)
        print(f"✅ {len(df)} leads saved to {filename}")

        updated_history = pd.concat([history_df, df], ignore_index=True)
        save_history(updated_history)
    else:
        print("⚠️ No relevant leads found.")

if __name__ == "__main__":
    run()
