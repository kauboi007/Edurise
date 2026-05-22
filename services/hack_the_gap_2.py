import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def search_notes(query, num_results=5):
    """Search notes using Google Custom Search (edu-priority then general)."""
    if not GOOGLE_API_KEY or not GOOGLE_CX:
        return [{"title": "Notes API not configured", "url": "#"}]

    try:
        # 1) Priority search on known educational sites
        edu_sites = (
            "site:physicswallahnotes.net OR site:vedantu.com OR site:byjus.com "
            "OR site:ncert.nic.in OR site:khanacademy.org"
        )
        edu_params = {
            "key": GOOGLE_API_KEY,
            "cx": GOOGLE_CX,
            "q": f"{query} {edu_sites}",
            "num": num_results,
        }
        r1 = requests.get("https://www.googleapis.com/customsearch/v1", params=edu_params, timeout=10)
        r1.raise_for_status()
        edu_items = r1.json().get("items", [])

        # 2) General search if we still need more results
        gen_params = {"key": GOOGLE_API_KEY, "cx": GOOGLE_CX, "q": query, "num": num_results}
        r2 = requests.get("https://www.googleapis.com/customsearch/v1", params=gen_params, timeout=10)
        r2.raise_for_status()
        gen_items = r2.json().get("items", [])

        # Merge results (edu first), dedupe by link
        seen = set()
        results = []
        for item in edu_items + gen_items:
            link = item.get("link") or item.get("formattedUrl")
            if not link or link in seen:
                continue
            seen.add(link)
            results.append({"title": item.get("title", "No title"), "url": link})
            if len(results) >= num_results:
                break

        if not results:
            return [{"title": "No notes found", "url": "#"}]
        return results

    except Exception as e:
        print("Error searching notes:", e)
        return [{"title": "Error fetching notes", "url": "#"}]


def search_youtube(query, num_results=5):
    """Search YouTube and return list of {title,url}."""
    if not YOUTUBE_API_KEY:
        return [{"title": "YouTube API not configured", "url": "#"}]

    try:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "key": YOUTUBE_API_KEY,
            "maxResults": num_results,
        }
        r = requests.get("https://www.googleapis.com/youtube/v3/search", params=params, timeout=10)
        r.raise_for_status()
        items = r.json().get("items", [])

        results = []
        for it in items:
            video_id = it.get("id", {}).get("videoId")
            title = it.get("snippet", {}).get("title", "No title")
            if video_id:
                results.append({"title": title, "url": f"https://www.youtube.com/watch?v={video_id}"})

        if not results:
            return [{"title": "No videos found", "url": "#"}]
        return results

    except Exception as e:
        print("Error searching YouTube:", e)
        return [{"title": "Error fetching YouTube results", "url": "#"}]
