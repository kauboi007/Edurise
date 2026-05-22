from flask import Flask, render_template_string
import requests, random

app = Flask(__name__)

# 🔑 Eventbrite API Token (replace with your real one)
EVENTBRITE_TOKEN = ""  # Leave empty → will use fallback events


# --- Dataset of quotes ---
QUOTES = [
    {"text": "The best way to get started is to quit talking and begin doing.", "author": "Walt Disney"},
    {"text": "Don’t let yesterday take up too much of today.", "author": "Will Rogers"},
    {"text": "It’s not whether you get knocked down, it’s whether you get up.", "author": "Vince Lombardi"},
    {"text": "If you are working on something exciting, it will keep you motivated.", "author": "Steve Jobs"},
    {"text": "Success is not in what you have, but who you are.", "author": "Bo Bennett"},
    {"text": "Hardships often prepare ordinary people for an extraordinary destiny.", "author": "C.S. Lewis"},
    {"text": "Don’t watch the clock; do what it does. Keep going.", "author": "Sam Levenson"},
    {"text": "Great things never come from comfort zones.", "author": "Anonymous"},
    {"text": "Dream it. Wish it. Do it.", "author": "Anonymous"},
    {"text": "Push yourself, because no one else is going to do it for you.", "author": "Anonymous"},
    {"text": "Success doesn’t just find you. You have to go out and get it.", "author": "Anonymous"},
    {"text": "The harder you work for something, the greater you’ll feel when you achieve it.", "author": "Anonymous"},
    {"text": "Dream bigger. Do bigger.", "author": "Anonymous"},
    {"text": "Don’t stop when you’re tired. Stop when you’re done.", "author": "Anonymous"},
    {"text": "Wake up with determination. Go to bed with satisfaction.", "author": "Anonymous"},
    {"text": "Little things make big days.", "author": "Anonymous"},
    {"text": "It’s going to be hard, but hard does not mean impossible.", "author": "Anonymous"},
    {"text": "Don’t wait for opportunity. Create it.", "author": "Anonymous"},
    {"text": "Sometimes later becomes never. Do it now.", "author": "Anonymous"},
    {"text": "Great things take time. Be patient.", "author": "Anonymous"}
]


# --- Fetch events ---
def fetch_events():
    if not EVENTBRITE_TOKEN:
        return fallback_events()

    url = "https://www.eventbriteapi.com/v3/events/search/"
    headers = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"}
    params = {
        "location.address": "Tamil Nadu, India",
        "sort_by": "date",
        "status": "live",
        "expand": "venue"
    }

    try:
        r = requests.get(url, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        events = []
        for ev in data.get("events", [])[:10]:
            title = (ev.get("name") or {}).get("text") or "Untitled Event"
            start_local = (ev.get("start") or {}).get("local") or ""
            date = start_local[:10] if start_local else "TBA"
            url_ev = ev.get("url") or "#"
            venue = ev.get("venue") or {}
            address = (venue.get("address") or {}).get("localized_address_display") or "Online"

            events.append({
                "title": title,
                "date": date,
                "url": url_ev,
                "location": address,
            })

        return events if events else fallback_events()
    except Exception as e:
        print("Error fetching events:", e)
        return fallback_events()


# --- Fallback events ---
def fallback_events():
    return [
        {
            "title": "Chennai Hackathon 2025",
            "date": "2025-09-20",
            "url": "https://example.com/chennai-hackathon",
            "location": "IIT Madras, Chennai"
        },
        {
            "title": "AI & ML Workshop",
            "date": "2025-09-25",
            "url": "https://example.com/ai-workshop",
            "location": "Anna University, Chennai"
        }
    ]


# --- Pick a random quote ---
def get_random_quote():
    return random.choice(QUOTES)


# --- HTML Template ---
TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Events in Tamil Nadu</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f7f8fb; color: #333; }
        h1 { color: #2c3e50; }
        .event { margin-bottom: 20px; padding: 10px; border: 1px solid #ccc; border-radius: 8px; background: #fff; }
        .quote { margin-top: 40px; padding: 20px; border-radius: 8px; background: #eef; }
    </style>
</head>
<body>
    <h1>Upcoming Events in Tamil Nadu</h1>

    {% for event in events %}
    <div class="event">
        <h3><a href="{{ event.url }}" target="_blank">{{ event.title }}</a></h3>
        <p><strong>Date:</strong> {{ event.date }}</p>
        <p><strong>Location:</strong> {{ event.location }}</p>
    </div>
    {% endfor %}

    <div class="quote">
        <h2>Daily Motivation</h2>
        <blockquote>"{{ quote.text }}"</blockquote>
        <p>— {{ quote.author }}</p>
    </div>
</body>
</html>
"""


# --- Routes ---
@app.route("/")
def index():
    events = fetch_events()
    quote = get_random_quote()
    return render_template_string(TEMPLATE, events=events, quote=quote)


if __name__ == "__main__":
    app.run(debug=True)
