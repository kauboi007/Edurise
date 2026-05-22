from flask import Flask, render_template, abort
import requests, os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# 🔑 Your AllEvents API key (get from .env file)
ALL_EVENTS_KEY = os.getenv("ALL_EVENTS_KEY", "")

# --- Fetch all events in Chennai ---
def fetch_events():
    # If no API key is provided, use fallback events
    if not ALL_EVENTS_KEY:
        print("AllEvents API key not configured. Using fallback events.")
        return fallback_events()
    
    # Using AllEvents API with proper parameters
    # Format: POST http://api.allevents.in/events/list/[city][state][country][page][sdate][edate][category]
    city = "Chennai"
    state = "Tamil Nadu"
    country = "India"
    page = 1
    category = "education"  # Filter for educational events
    
    url = f"http://api.allevents.in/events/list/{city}/{state}/{country}/{page}/{category}"
    
    params = {
        "key": ALL_EVENTS_KEY
    }
    try:
        # Using POST request as per API documentation
        r = requests.post(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        events = []
        for ev in data.get("data", [])[:10]:  # limit to 10
            events.append({
                "id": ev.get("event_id"),
                "title": ev.get("title"),
                "date": ev.get("start_date"),
                "location": ev.get("venue", {}).get("address", "Online"),
                "url": ev.get("event_url"),
                "description": ev.get("description", "No description available.")
            })
        return events
    except Exception as e:
        print("Error fetching events:", e)
        return fallback_events()

# --- Fallback if API fails ---
def fallback_events():
    return [
        {
            "id": "101",
            "title": "Chennai Meetup",
            "date": "2025-09-15",
            "location": "Nungambakkam, Chennai",
            "url": "#",
            "description": "A networking meetup for Chennai students."
        },
        {
            "id": "102",
            "title": "Chennai Coding Jam",
            "date": "2025-09-20",
            "location": "Anna Nagar, Chennai",
            "url": "#",
            "description": "Collaborative coding and problem solving event."
        }
    ]

# --- Home Page ---
@app.route("/")
def index():
    events = fetch_events()
    return render_template("index.html", events=events)

# --- Event Details Page ---
@app.route("/event/<event_id>")
def event_details(event_id):
    events = fetch_events()
    event = next((ev for ev in events if str(ev["id"]) == str(event_id)), None)
    if event is None:
        abort(404)
    return render_template("details.html", event=event)

if __name__ == "__main__":
    app.run(debug=True)

