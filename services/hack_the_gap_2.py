import os
import requests
from dotenv import load_dotenv
#tried adn tested
# Load API keys from .env
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_notes(query, num_results=5):
    """
    Search academic notes using Google Custom Search API.
    Returns a list of dicts with title + link.
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return [{"title": "Notes API not configured", "link": "#"}]

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CX,
        "q": query
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        results = []
        for item in data.get("items", [])[:num_results]:
            results.append({
                "title": item.get("title"),
                "url": item.get("link")
            })
        return results

    except Exception as e:
        print("Error searching notes:", e)
        return [{"title": "Error fetching notes", "link": "#"}]


def search_youtube(query, num_results=5):
    """
    Search YouTube videos using YouTube Data API v3.
    Returns a list of dicts with title + video link.
    """
    if not YOUTUBE_API_KEY:
        return [{"title": "YouTube API not configured", "link": "#"}]

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "key": YOUTUBE_API_KEY,
        "maxResults": num_results
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        results = []
        for item in data.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            link = f"https://www.youtube.com/watch?v={video_id}"
            results.append({"title": title, "url": link})
        return results

    except Exception as e:
        print("Error searching YouTube:", e)
        return [{"title": "Error fetching YouTube results", "link": "#"}]
