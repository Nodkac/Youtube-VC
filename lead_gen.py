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
    "vc podcast", "startup podcast", "founder interview", "venture capital podcast",
    "angel investor podcast", "seed funding podcast", "startup pitch podcast",
    "founder journey", "entrepreneur podcast", "startup AMA", "startup accelerator",
    "bootstrap founder", "tech founders", "early stage investing", "fundraising interview",
    "product market fit podcast", "SaaS founder", "web3 investor", "startup talk", "funding journey"
]

VIDEO_KEYWORDS = ["podcast", "episode", "interview", "founder", "startup"]

CHANNEL_KEYWORDS = [
    "vc", "venture", "capital", "investor", "startup", "angel",
    "accelerator", "founder", "bootstrap", "pitch", "growth", "business"
]

MAX_LEADS = 100
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

def get_channel_details(channel_ids, apply_filters=True):
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
            snippet = item["snippet"]
            branding = item.get("brandingSettings", {}).get("channel", {})
            country = branding.get("country", "").upper()
            if country == "IN":
                continue

            title = snippet["title"].lower()
            description = snippet.get("description", "").lower()

            if apply_filters:
                combined = title + description
                if not any(k in combined for k in CHANNEL_KEYWORDS):
                    continue

            channel_url = f"https://www.youtube.com/channel/{item['id']}"
            subs = item["statistics"].get("subscriberCount", "Hidden")
            all_data.append([snippet["title"], channel_url, subs])
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
            found_channels.add(snippet["channelId"])

        if len(found_channels) >= MAX_LEADS * 2:
            break

    print(f"🔍 Found {len(found_channels)} unique candidate channels.")

    channel_details = get_channel_details(list(found_channels), apply_filters=True)

    for name, url, subs in channel_details:
        if url not in seen_urls and len(all_leads) < MAX_LEADS:
            all_leads.append([name, url, subs, today_str])
            seen_urls.add(url)

    # Fallback Mode if no leads passed filters
    if len(all_leads) == 0:
        print("⚠️ No filtered leads passed. Running fallback mode with looser checks.")
        fallback_channels = get_channel_details(list(found_channels), apply_filters=False)
        for name, url, subs in fallback_channels:
            if url not in seen_urls and len(all_leads) < MAX_LEADS:
                all_leads.append([name, url, subs, today_str])
                seen_urls.add(url)

    # Save CSV (even if empty)
    df = pd.DataFrame(all_leads, columns=["Channel Name", "Channel URL", "Subscriber Count", "Date Added"])
    filename = f"vc_podcast_leads_{today_str}.csv"
    df.to_csv(filename, index=False)

    if len(df) == 0:
        print("⚠️ No relevant leads found. Empty file saved.")
    else:
        print(f"✅ {len(df)} leads saved to {filename}")

    updated_history = pd.concat([history_df, df], ignore_index=True)
    save_history(updated_history)

if __name__ == "__main__":
    run()
