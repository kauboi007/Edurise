"""
Career Guidance Service (Refactored from original hack the gap 3.py)
-------------------------------------------------------------------
This module provides functions to check which skills a user already has
and which skills they need for a target career. It can use predefined skills
or fall back to Google Custom Search API for skill extraction.
"""
#tried and tested
import os
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")  # Custom search engine ID


# ✅ Predefined career skills (fallbacks for popular careers)
career_skills = {
    "data scientist": ["python", "statistics", "machine learning", "sql", "data visualization", "deep learning"],
    "web developer": ["html", "css", "javascript", "react", "nodejs", "git", "databases"],
    "doctor": ["biology", "chemistry", "clinical knowledge", "anatomy", "patient care"],
    "ux designer": ["wireframing", "prototyping", "figma", "user research", "visual design"],
    "software engineer": ["algorithms", "data structures", "java", "python", "git", "system design"],
    "digital marketer": ["seo", "content marketing", "google analytics", "social media", "email marketing"],
    "graphic designer": ["photoshop", "illustrator", "typography", "color theory", "branding"],
    "cybersecurity analyst": ["network security", "penetration testing", "firewalls", "encryption", "incident response"],
    "financial analyst": ["excel", "financial modeling", "accounting", "forecasting", "data analysis"],
    "civil engineer": ["autocad", "structural analysis", "construction management", "surveying", "project planning"],
    "mechanical engineer": ["solidworks", "thermodynamics", "cad", "fluid mechanics", "materials science"],
    "electrical engineer": ["circuit design", "embedded systems", "matlab", "signal processing", "power systems"],
    "product manager": ["roadmapping", "agile", "user stories", "stakeholder management", "market research"],
    "business analyst": ["requirements gathering", "sql", "process modeling", "data visualization", "stakeholder communication"],
    "teacher": ["lesson planning", "classroom management", "assessment", "pedagogy", "subject expertise"],
    "lawyer": ["legal research", "contract law", "litigation", "negotiation", "writing briefs"],
    "accountant": ["bookkeeping", "taxation", "excel", "financial reporting", "auditing"],
    "architect": ["autocad", "revit", "design principles", "building codes", "3d modeling"],
    "data engineer": ["python", "etl", "sql", "spark", "data warehousing"],
    "ai engineer": ["python", "tensorflow", "deep learning", "nlp", "model deployment"],
    "mobile app developer": ["flutter", "react native", "android", "ios", "firebase"],
    "game developer": ["unity", "c#", "game physics", "3d modeling", "animation"],
    "content writer": ["seo", "grammar", "storytelling", "editing", "research"],
    "hr manager": ["recruitment", "employee relations", "labor laws", "training", "performance management"],
    "nurse": ["patient care", "vital signs", "medication administration", "clinical procedures", "emergency response"],
    "pharmacist": ["pharmacology", "drug interactions", "prescription review", "dosage calculation", "patient counseling"],
    "radiologist": ["medical imaging", "ct scan", "mri", "x-ray interpretation", "anatomy"],
    "physiotherapist": ["rehabilitation", "exercise therapy", "anatomy", "manual therapy", "patient assessment"],
    "dentist": ["oral anatomy", "dental procedures", "radiology", "infection control", "patient communication"],
    "nutritionist": ["diet planning", "nutritional science", "meal assessment", "client consultation", "food safety"],
    "lab technician": ["sample collection", "microscopy", "biochemistry", "reporting", "equipment handling"],
    "surgeon": ["surgical techniques", "anatomy", "sterilization", "patient monitoring", "pre-op/post-op care"],
    "psychiatrist": ["mental health", "diagnosis", "therapy", "pharmacology", "patient interaction"],
    "veterinarian": ["animal anatomy", "diagnosis", "surgery", "vaccination", "client communication"],
    "biomedical engineer": ["medical devices", "biomaterials", "electronics", "anatomy", "regulatory standards"],
    "public health officer": ["epidemiology", "health policy", "data analysis", "community outreach", "disease prevention"],
    "paramedic": ["emergency response", "first aid", "trauma care", "patient transport", "communication"],
    "clinical psychologist": ["cognitive therapy", "behavioral analysis", "diagnosis", "counseling", "research methods"],
    "anesthesiologist": ["anesthesia techniques", "patient monitoring", "pharmacology", "airway management", "surgical prep"],
    "ophthalmologist": ["eye anatomy", "vision testing", "surgical procedures", "optics", "patient care"],
    "cardiologist": ["cardiac anatomy", "ecg interpretation", "clinical diagnosis", "treatment planning", "patient education"],
    "neurosurgeon": ["brain anatomy", "surgical techniques", "neuroimaging", "critical care", "diagnosis"],
    "dermatologist": ["skin anatomy", "clinical diagnosis", "laser therapy", "cosmetic procedures", "patient consultation"],
    "gynecologist": ["reproductive health", "obstetrics", "clinical procedures", "patient care", "diagnosis"],
    "orthopedic surgeon": ["bone anatomy", "surgical techniques", "rehabilitation", "diagnosis", "patient care"],
    "pathologist": ["histology", "lab diagnostics", "microscopy", "reporting", "clinical correlation"],
    "oncologist": ["cancer biology", "chemotherapy", "radiation therapy", "patient counseling", "diagnosis"],
    "genetic counselor": ["genetics", "risk assessment", "family history analysis", "communication", "ethical guidelines"],
    "medical coder": ["icd coding", "medical terminology", "billing systems", "ehr", "compliance"],
    "clinical researcher": ["study design", "data collection", "ethics", "statistical analysis", "report writing"],
    "healthcare administrator": ["hospital operations", "budgeting", "staff management", "compliance", "policy development"],
    "speech therapist": ["speech disorders", "therapy techniques", "patient evaluation", "communication", "rehabilitation"],
    "occupational therapist": ["daily living skills", "rehabilitation", "patient assessment", "therapy planning", "ergonomics"],
    "medical transcriptionist": ["listening skills", "medical terminology", "typing", "ehr systems", "accuracy"],
}


def get_skills_from_google(career: str):
    """Fetch structured skills/topics from Google Custom Search"""
    query = f"list of skills or syllabus topics to become a {career}"
    url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={GOOGLE_API_KEY}&cx={GOOGLE_CX}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        skills = []
        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "").lower()

                # Split snippet into lines
                lines = [l.strip() for l in snippet.split("\n")]
                for l in lines:
                    if any(symbol in l for symbol in ["-", "•", "1.", "2.", "3."]):
                        cleaned = l.replace("-", "").replace("•", "").strip()
                        if 2 <= len(cleaned.split()) <= 5:
                            skills.append(cleaned)

                # Fallback: comma-separated phrases
                parts = [p.strip() for p in snippet.replace(";", ",").split(",")]
                for p in parts:
                    if 2 <= len(p.split()) <= 4 and p not in skills:
                        skills.append(p)

        return list(dict.fromkeys(skills))[:10]  # remove duplicates, max 10
    except Exception as e:
        print("Google API error:", e)
        return []


def career_guidance(career: str, skills_text: str):
    """
    Main function to check skills.
    Args:
        career (str): target career (e.g. "data scientist")
        skills_text (str): comma-separated user skills
    Returns:
        dict: { "career": ..., "have": [...], "missing": [...] }
    """
    if not career.strip():
        return {"career": "", "have": [], "missing": []}

    user_skills = [s.strip().lower() for s in skills_text.split(",") if s.strip()]

    # Step 1: Predefined list
    if career.lower() in career_skills:
        required = career_skills[career.lower()]
    else:
        # Step 2: Google API fallback
        required = get_skills_from_google(career)

    # Step 3: Compare
    have = list(set(user_skills) & set(required))
    missing = list(set(required) - set(user_skills))

    return {
        "career": career.title(),
        "have": have,
        "missing": missing
    }
