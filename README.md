# EduRise

EduRise is a Flask-based educational support web app that helps students discover resources, explore career guidance, and match with mentors. It combines Google search integration, YouTube recommendations, career skill analysis, and dropout risk-driven mentor matching.

## Features

- Home page with rotating motivational quotes.
- Resources search powered by Google Custom Search and YouTube.
- Career guidance that compares a user's listed skills against target career requirements.
- Mentor matching with student dropout risk prediction and mentor slot allocation.
- Local events redirect to Chennai education events on AllEvents.

## Project Structure

- `app.py` - Main Flask application with routes for home, resources, career guidance, mentor matching, and events.
- `services/` - Helper modules for search, career guidance, mentor matching, and event logic.
- `templates/` - HTML templates for each page.
- `static/style.css` - Styling for the front-end.
- `students.csv` - Student dataset used for dropout risk prediction.
- `mentors.csv` - Mentor availability and expertise data for matching.
- `dropout_model.joblib` - Saved model artifact included in the repository.

## Requirements

- Python 3.9+ recommended
- Install dependencies from `requirements.txt`

## Setup

1. Create a virtual environment:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root and add API keys:

   ```env
   GOOGLE_API_KEY=your_google_api_key
   GOOGLE_CX=your_google_custom_search_engine_id
   YOUTUBE_API_KEY=your_youtube_api_key
   FLASK_SECRET_KEY=your_secret_key
   ```

## Running the App

Start the application with:

```bash
python app.py
```

Then open `http://127.0.0.1:5000/` in your browser.

## Usage

- `Home` shows a motivational quote.
- `Resources` lets users search for study notes and educational YouTube videos.
- `Career` accepts a target career and current skills to highlight skills you already have and skills you may still need.
- `Mentor` allows upload of `students.csv` and `mentors.csv`, then predicts dropout risk and assigns mentors to high-risk students.
- `Events` redirects to local Chennai education event listings.

## CSV Data Guidelines

### `students.csv`
Expected columns:

- `RollNumber`
- `Name`
- `AttendancePercent`
- `AvgGrade`
- `DistanceKM`
- `ParentEducation`
- `FamilyIncome`
- `Siblings`
- `PastAbsences`

### `mentors.csv`
Expected columns:

- `MentorName`
- `Expertise`
- `SlotStart`
- `SlotEnd`

Mentor slots are expanded into 30-minute intervals for assignment.

## Notes

- The app uses Google Custom Search and YouTube APIs for resource searches.
- If API keys are not configured, search pages will show placeholder messages.
- `FLASK_SECRET_KEY` should be set for production deployments.

## License

This project is provided as-is for educational and development use.