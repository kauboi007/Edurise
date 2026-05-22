from flask import Flask, render_template, request, redirect
from services.hack_the_gap_2 import search_notes, search_youtube
from services.hack_the_gap_3 import career_guidance
import services.prabanjan_mentor_match as mentor_module
import random

app = Flask(__name__)
app.secret_key = "super-secret-key"

# ---------------- MOTIVATION (Quotes only on homepage) ----------------
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
]

def get_random_quote():
    return random.choice(QUOTES)

# ---------------- HOME ----------------
@app.route("/")
def home():
    quote = get_random_quote()
    return render_template("index.html", quote=quote)

# ---------------- RESOURCES ----------------
@app.route("/resources", methods=["GET", "POST"])
def resources():
    notes, videos, query = [], [], ""
    if request.method == "POST":
        query = request.form.get("query", "")
        if query:
            notes = search_notes(query)
            videos = search_youtube(query)  # educational filter is inside function
    return render_template("resources.html", query=query, notes=notes, videos=videos)

# ---------------- CAREER GUIDANCE ----------------
@app.route("/career", methods=["GET", "POST"])
def career():
    result = None
    if request.method == "POST":
        career_name = request.form.get("career", "")
        skills_text = request.form.get("skills", "")
        result = career_guidance(career_name, skills_text)
    return render_template("career.html", result=result)

# ---------------- MENTOR MATCHING ----------------
@app.route("/mentor", methods=["GET"])
def mentor_home():
    return render_template("mentor.html")

@app.route("/predict", methods=["POST"])
def mentor_predict():
    return mentor_module.predict()

@app.route("/upload_mentors", methods=["POST"])
def mentor_upload():
    return mentor_module.upload_mentors()

# ---------------- LOCAL EVENTS ----------------
@app.route("/events")
def events():
    # Redirect to AllEvents website with filters for Chennai educational events
    all_events_url = "https://allevents.in/chennai/education"
    return redirect(all_events_url)

# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(debug=True)
