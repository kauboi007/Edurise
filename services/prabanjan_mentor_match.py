# app.py
"""
Dropout Risk Predictor & Mentor Matching (single-file Flask app)
- Upload students CSV and optional mentors.csv
- Computes dropout risk using rule-based scoring
- Expands mentor availability into 30-min slots and assigns highest-risk students first
- Shows uploaded filenames + timestamps (persisted in session)
- Clickable, client-side sortable results table (with Risk Level special ordering)
"""

import os
import re
import pandas as pd
from flask import Flask, request, render_template_string, session
from datetime import datetime, timedelta

# ------------------ CONFIG ------------------
SLOT_MINUTES = 30
MENTORS_CSV = "mentors.csv"
EXPECTED_STUDENT_COLS = [
    "RollNumber", "Name", "AttendancePercent", "AvgGrade", "DistanceKM",
    "ParentEducation", "FamilyIncome", "Siblings", "PastAbsences"
]

# ------------------ FLASK APP ------------------
app = Flask(__name__)
# Use env secret if provided; otherwise dev fallback (change for production!)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

COLUMN_ORDER = [
    "Roll No", "Student Name", "Attendance %", "Average Grade", "Distance (km)",
    "Parent Education", "Family Income", "No. of Siblings", "Past Absences",
    "Dropout Risk (%)", "Risk Level", "Reason", "Mentor Assigned", "Mentor Slot"
]

# ------------------ HTML TEMPLATE ------------------
HTML_PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Dropout Risk Predictor & Mentor Matching</title>
  {% raw %}
  <style>
    body { font-family: Arial, sans-serif; margin: 28px; background:#fafafa; color:#222; }
    h2 { color:#333; margin:0 0 8px 0; }
    .panel { background:white; padding:12px; border-radius:8px; border:1px solid #eee; margin-bottom:16px; box-shadow:0 1px 3px rgba(0,0,0,0.03); }
    table { border-collapse:collapse; width:100%; margin-top:12px; }
    th, td { border:1px solid #e6e6e6; padding:8px; text-align:center; font-size:13px; vertical-align:middle; }
    th { background:#2f4f4f; color:white; user-select:none; cursor:pointer; }
    tr.Low { background:#eaf7ea; }
    tr.Medium { background:#fff9e6; }
    tr.High { background:#fff1f1; }
    .reason-good { color:green; font-weight:600; }
    .reason-medium { color:orange; font-weight:600; }
    .reason-bad { color:red; font-weight:600; }
    .controls { display:flex; gap:12px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }
    .uform { display:inline-block; }
    input[type=file] { padding:6px; }
    button { padding:6px 10px; border-radius:6px; border:none; background:#2f8bd3; color:white; cursor:pointer; }
    .small { font-size:12px; color:#666; margin-top:6px; }
    .uploaded-info { margin-left:8px; font-size:12px; color:#444; }
    .msg { font-weight:600; }
    code { background:#f4f4f4; padding:2px 6px; border-radius:4px; font-size:12px; }
    @media (max-width:900px) { th, td { font-size:12px; padding:6px; } }
  </style>

  <script>
    function getRiskOrder(val) {
      if (val === "Low") return 1;
      if (val === "Medium") return 2;
      if (val === "High") return 3;
      var n = parseFloat(val.replace(/[^0-9.-]+/g,""));
      return isNaN(n) ? val : n;
    }

    function sortTable(colIndex) {
      var table = document.querySelector("table");
      if (!table) return;
      var tbody = table.tBodies[0];
      var rows = Array.from(tbody.rows);
      var currentDir = table.getAttribute("data-sortdir-" + colIndex) || "desc";
      var asc = currentDir !== "asc";

      rows.sort(function(a, b) {
        var A = a.cells[colIndex] ? a.cells[colIndex].innerText.trim() : "";
        var B = b.cells[colIndex] ? b.cells[colIndex].innerText.trim() : "";

        var riskValues = ["Low","Medium","High"];
        if (riskValues.indexOf(A) !== -1 || riskValues.indexOf(B) !== -1) {
          var vA = getRiskOrder(A), vB = getRiskOrder(B);
          return asc ? (vA - vB) : (vB - vA);
        }

        var numA = parseFloat(A.replace(/[^0-9.-]+/g,""));
        var numB = parseFloat(B.replace(/[^0-9.-]+/g,""));
        var bothNumeric = !isNaN(numA) && !isNaN(numB);

        if (bothNumeric) return asc ? (numA - numB) : (numB - numA);
        return asc ? A.localeCompare(B) : B.localeCompare(A);
      });

      rows.forEach(function(r) { tbody.appendChild(r); });
      table.setAttribute("data-sortdir-" + colIndex, asc ? "asc" : "desc");
    }

    // Auto-sort by Dropout Risk (%) descending on load
    document.addEventListener("DOMContentLoaded", function() {
      var ths = document.querySelectorAll("table thead th");
      for (var i = 0; i < ths.length; i++) {
        if (ths[i].innerText.trim() === "Dropout Risk (%)") {
          sortTable(i); sortTable(i); // toggle twice to land on desc
          break;
        }
      }
    });
  </script>
  {% endraw %}
</head>
<body>
  <div class="panel">
    <h2>Dropout Risk Predictor & Mentor Matching</h2>
    <div class="controls">
      <div class="uform">
        <form action="/predict" method="post" enctype="multipart/form-data" style="display:inline;">
          <label class="small">Upload students CSV</label>&nbsp;
          <input type="file" name="file" required>
          <button type="submit">Upload & Predict</button>
        </form>
        {% if last_students %}
          <div class="uploaded-info">{{ last_students }}</div>
        {% endif %}
      </div>

      <div class="uform">
        <form action="/upload_mentors" method="post" enctype="multipart/form-data" style="display:inline;">
          <label class="small">Upload mentors.csv</label>&nbsp;
          <input type="file" name="mentors_file" required>
          <button type="submit">Upload Mentors</button>
        </form>
        {% if last_mentors %}
          <div class="uploaded-info">{{ last_mentors }}</div>
        {% endif %}
      </div>

      <div class="uform">
        <form action="/" method="get" style="display:inline;">
          <button type="submit">Reset</button>
        </form>
      </div>
    </div>

    <div class="small">
      Expected student CSV columns: <code>RollNumber, Name, AttendancePercent, AvgGrade, DistanceKM, ParentEducation, FamilyIncome, Siblings, PastAbsences</code>
    </div>
  </div>

  {% if table %}
    <div class="panel">
      <h3>Results (click headers to sort)</h3>
      {{ table|safe }}
    </div>
  {% endif %}

  {% if message %}
    <div class="panel msg">{{message}}</div>
  {% endif %}
</body>
</html>
"""

# ------------------ UTILITIES ------------------
def parse_datetime_flexible(s, default_date=None):
    """Parse 'YYYY-MM-DD HH:MM', 'YYYY-MM-DDTHH:MM', 'HH:MM' (uses default_date or today), or pandas fallback."""
    if pd.isna(s) or s is None:
        return None
    if isinstance(s, datetime):
        return s
    s = str(s).strip()
    if default_date is None:
        default_date = datetime.today().date()
    fmts = ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%H:%M", "%Y-%m-%d %H:%M:%S"]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            if f == "%H:%M":
                dt = datetime.combine(default_date, dt.time())
            return dt
        except Exception:
            continue
    try:
        dt = pd.to_datetime(s)
        if pd.isna(dt):
            return None
        return pd.Timestamp(dt).to_pydatetime()
    except Exception:
        return None

def load_mentors_list(path=MENTORS_CSV):
    """
    Read mentors.csv and expand into list with discrete 30-min slots.
    Requires columns: MentorName, Expertise, SlotStart, SlotEnd
    Returns: [{MentorName, Expertise, Slots:[datetime,...]}, ...]
    """
    mentors_list = []
    if not os.path.exists(path):
        return mentors_list
    df = pd.read_csv(path)
    required = {"MentorName", "Expertise", "SlotStart", "SlotEnd"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"mentors.csv must contain columns: {required}. Found: {list(df.columns)}")

    for _, r in df.iterrows():
        start = parse_datetime_flexible(r["SlotStart"])
        end = parse_datetime_flexible(r["SlotEnd"])
        if start is None or end is None:  # skip bad rows
            continue
        if end <= start:  # skip invalid windows
            continue

        slots = []
        cur = start
        # generate slots [start, end) in SLOT_MINUTES steps
        while cur + timedelta(minutes=SLOT_MINUTES) <= end:
            slots.append(cur)
            cur += timedelta(minutes=SLOT_MINUTES)

        mentors_list.append({
            "MentorName": str(r["MentorName"]),
            "Expertise": str(r["Expertise"]),
            "Slots": slots
        })
    return mentors_list

# ------------------ PARENT EDUCATION NORMALIZATION & SCORING ------------------
def normalize_parent_education(raw):
    """
    Map raw ParentEducation to one of:
    "None", "Primary", "Secondary", "Higher Secondary", "Graduate", "Postgraduate", "Unknown"
    """
    if pd.isna(raw) or raw is None:
        return "Unknown"
    s = str(raw).strip()
    if s == "":
        return "Unknown"
    low = s.lower()

    if any(tok in low for tok in ["no education", "none", "illiterate", "no school", "n/a", "na", "nil"]):
        return "None"

    if any(tok in low for tok in ["post", "postgrad", "post-graduate", "masters", "master", "m.sc", "m.a", "mtech", "m.tech", "mba", "phd", "doctor"]):
        return "Postgraduate"

    if any(tok in low for tok in ["graduate", "bachelor", "b.sc", "b.a", "bcom", "btech", "be ", "b.e", "b.tech", "ug ", "undergrad"]):
        return "Graduate"

    if any(tok in low for tok in ["higher secondary", "12th", "12", "intermediate", "senior secondary"]):
        return "Higher Secondary"

    if any(tok in low for tok in ["secondary", "high school", "highschool", "10th", "matric", "s.s.c", "ssc", "hs"]):
        return "Secondary"

    if any(tok in low for tok in ["primary", "elementary", "5th", "8th", "primary school"]):
        return "Primary"

    # numeric hints
    if re.search(r'\b12\b|\b10\b|\bgraduat', low):
        if '12' in low or re.search(r'\b12\b', low):
            return "Higher Secondary"
        if '10' in low:
            return "Secondary"
        if 'graduat' in low:
            return "Graduate"

    return "Unknown"

def feature_risk_parentedu(pe_normalized):
    if pd.isna(pe_normalized) or pe_normalized is None:
        return 1.0
    label = str(pe_normalized).strip()
    if label == "None": return 1.0
    if label == "Primary": return 0.6
    if label == "Secondary": return 0.3
    if label == "Higher Secondary": return 0.2
    if label in ("Graduate", "Postgraduate"): return 0.0
    if label == "Unknown": return 0.5
    return 0.5

# ------------------ OTHER FEATURE RISK FUNCTIONS ------------------
def feature_risk_attendance(att):
    try:
        a = float(att)
    except Exception:
        return 1.0
    if a >= 85: return 0.0
    if a >= 75: return 0.25
    if a >= 60: return 0.5
    if a >= 45: return 0.75
    return 1.0

def feature_risk_grade(g):
    try:
        gg = float(g)
    except Exception:
        return 1.0
    if gg >= 85: return 0.0
    if gg >= 70: return 0.25
    if gg >= 50: return 0.6
    return 1.0

def feature_risk_absences(pa):
    try:
        p = float(pa)
    except Exception:
        return 1.0
    if p <= 5: return 0.0
    if p <= 15: return 0.25
    if p <= 30: return 0.6
    return 1.0

def feature_risk_distance(d):
    try:
        dd = float(d)
    except Exception:
        return 1.0
    if dd <= 5: return 0.0
    if dd <= 12: return 0.25
    if dd <= 20: return 0.6
    return 1.0

def feature_risk_income(income):
    if pd.isna(income) or income == "" or income is None:
        return 1.0
    try:
        val = float(income)
        if val >= 50000: return 0.0
        if val >= 20000: return 0.25
        return 1.0
    except Exception:
        s = str(income).strip().lower()
        if s in ("high", "h", "hi"): return 0.0
        if s in ("medium", "med", "m"): return 0.25
        if s in ("low", "l"): return 1.0
        return 0.5

def feature_risk_siblings(sib):
    try:
        x = int(sib)
    except Exception:
        return 0.0
    if x >= 6: return 0.35
    if x >= 3: return 0.15
    return 0.0

def color_label_from_risk(risk):
    if risk <= 0.25: return "good"
    if risk <= 0.6: return "medium"
    return "bad"

# ------------------ COMBINE FEATURES INTO RULE SCORE ------------------
def compute_rule_score_and_reasons(row):
    weights = {
        "attendance": 0.27,
        "grade": 0.24,
        "absences": 0.18,
        "distance": 0.08,
        "income": 0.12,
        "parentedu": 0.07,
        "siblings": 0.04
    }

    a = feature_risk_attendance(row.get("AttendancePercent"))
    g = feature_risk_grade(row.get("AvgGrade"))
    pa = feature_risk_absences(row.get("PastAbsences"))
    d = feature_risk_distance(row.get("DistanceKM"))
    inc = feature_risk_income(row.get("FamilyIncome"))
    ped = feature_risk_parentedu(row.get("ParentEducation"))
    sib = feature_risk_siblings(row.get("Siblings"))

    contribs = {
        "attendance": weights["attendance"] * a,
        "grade": weights["grade"] * g,
        "absences": weights["absences"] * pa,
        "distance": weights["distance"] * d,
        "income": weights["income"] * inc,
        "parentedu": weights["parentedu"] * ped,
        "siblings": weights["siblings"] * sib
    }

    final_score = sum(contribs.values()) / sum(weights.values())
    final_pct = round(final_score * 100, 1)

    reasons = []
    lab = color_label_from_risk(a)
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Good attendance ({row.get('AttendancePercent')}%)</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Average attendance ({row.get('AttendancePercent')}%)</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Low attendance ({row.get('AttendancePercent')}%)</span>")

    lab = color_label_from_risk(g)
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Strong grades ({row.get('AvgGrade')})</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Moderate grades ({row.get('AvgGrade')})</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Poor grades ({row.get('AvgGrade')})</span>")

    lab = color_label_from_risk(pa)
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Consistent presence ({row.get('PastAbsences')} absences)</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Some absences ({row.get('PastAbsences')})</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Many absences ({row.get('PastAbsences')})</span>")

    lab = color_label_from_risk(d)
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Close to school ({row.get('DistanceKM')} km)</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Moderate commute ({row.get('DistanceKM')} km)</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Long commute ({row.get('DistanceKM')} km)</span>")

    lab = color_label_from_risk(inc)
    income_raw = row.get("FamilyIncome")
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Stable household income ({income_raw})</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Moderate household income ({income_raw})</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Low household income ({income_raw})</span>")

    lab = color_label_from_risk(ped)
    ped_raw = row.get("ParentEducation")
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Supportive family education ({ped_raw})</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Limited family education ({ped_raw})</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Very limited family education ({ped_raw})</span>")

    lab = color_label_from_risk(sib)
    sib_raw = row.get("Siblings")
    if lab == "good":
        reasons.append(f"<span class='reason-good'>Few siblings ({sib_raw})</span>")
    elif lab == "medium":
        reasons.append(f"<span class='reason-medium'>Several siblings ({sib_raw})</span>")
    else:
        reasons.append(f"<span class='reason-bad'>Many siblings ({sib_raw})</span>")

    reasons_html = "<br>".join(reasons)
    return final_pct, reasons_html, contribs

# ------------------ MENTOR MATCHING ------------------
def assign_mentors(df, mentors_list):
    """
    Assign mentor slots to students by risk (desc) and domain match.
    """
    work = df.copy().reset_index(drop=True).sort_values(by="Dropout Risk (%)", ascending=False).reset_index(drop=True)

    mentors_state = []
    for m in mentors_list:
        mentors_state.append({
            "MentorName": m["MentorName"],
            "Expertise": m["Expertise"].lower(),
            "Slots": list(m["Slots"])
        })

    assigned = []
    assigned_slots = []

    for _, row in work.iterrows():
        requested = str(row.get("RequestedDomain", "") or "").strip().lower()
        if requested:
            domain = requested
        else:
            # simple inference from grades
            try:
                g = float(row.get("AvgGrade", 0))
            except Exception:
                g = 0
            if g >= 75: domain = "computer"
            elif g >= 60: domain = "mathematics"
            else: domain = "science"

        candidates = []
        for ment in mentors_state:
            tokens = [t.strip().lower() for t in ment["Expertise"].replace(";", ",").split(",")]
            if any(domain in tok or tok in domain for tok in tokens):
                if ment["Slots"]:
                    candidates.append(ment)
        if not candidates:
            candidates = [m for m in mentors_state if m["Slots"]]
        if not candidates:
            assigned.append(None)
            assigned_slots.append(None)
            continue

        candidates.sort(key=lambda m: m["Slots"][0])
        chosen = candidates[0]
        slot_dt = chosen["Slots"].pop(0)
        assigned.append(chosen["MentorName"])
        assigned_slots.append(slot_dt.strftime("%Y-%m-%d %H:%M"))

    work["Mentor Assigned"] = assigned
    work["Mentor Slot"] = assigned_slots

    out = df.copy().set_index("RollNumber")
    assign_map = work.set_index("RollNumber")[["Mentor Assigned", "Mentor Slot"]]
    for rn, row in assign_map.iterrows():
        if rn in out.index:
            out.at[rn, "Mentor Assigned"] = row["Mentor Assigned"]
            out.at[rn, "Mentor Slot"] = row["Mentor Slot"]
    out = out.reset_index()
    return out

# ------------------ DATA PROCESSING ------------------
def process_students_df(df_students):
    # ensure expected columns exist
    for c in EXPECTED_STUDENT_COLS:
        if c not in df_students.columns:
            df_students[c] = pd.NA

    # normalize & convert types
    df_students["AttendancePercent"] = pd.to_numeric(df_students["AttendancePercent"], errors="coerce").fillna(0).astype(float)
    df_students["AvgGrade"] = pd.to_numeric(df_students["AvgGrade"], errors="coerce").fillna(0).astype(float)
    df_students["DistanceKM"] = pd.to_numeric(df_students["DistanceKM"], errors="coerce").fillna(0).astype(float)
    df_students["PastAbsences"] = pd.to_numeric(df_students["PastAbsences"], errors="coerce").fillna(0).astype(int)
    df_students["Siblings"] = pd.to_numeric(df_students["Siblings"], errors="coerce").fillna(0).astype(int)

    # normalize ParentEducation into canonical labels
    df_students["ParentEducation"] = df_students["ParentEducation"].apply(normalize_parent_education)

    # ensure RequestedDomain exists
    if "RequestedDomain" not in df_students.columns:
        df_students["RequestedDomain"] = ""

    # compute rule score & reasons
    pct_list, reasons_list = [], []
    for _, r in df_students.iterrows():
        pct, reasons_html, _ = compute_rule_score_and_reasons(r)
        pct_list.append(pct)
        reasons_list.append(reasons_html)

    df_students["Dropout Risk (%)"] = pct_list
    df_students["Reason"] = reasons_list
    df_students["Risk Level"] = pd.cut(
        df_students["Dropout Risk (%)"], bins=[-0.01, 30, 60, 100], labels=["Low", "Medium", "High"], include_lowest=True
    )
    df_students["Mentor Assigned"] = None
    df_students["Mentor Slot"] = None

    # ensure RollNumber exists - if missing, generate from index
    if "RollNumber" not in df_students.columns or df_students["RollNumber"].isnull().all():
        df_students["RollNumber"] = df_students.index.astype(str)

    return df_students

# ------------------ TABLE HTML ------------------
def make_html_table(df_display):
    cols = COLUMN_ORDER
    table_html = "<table data-sortdir='desc'><thead><tr>"
    for i, c in enumerate(cols):
        table_html += f"<th onclick='sortTable({i})'>{c}</th>"
    table_html += "</tr></thead><tbody>"
    for _, r in df_display.iterrows():
        risk_class = str(r.get("Risk Level", ""))
        table_html += f"<tr class='{risk_class}'>"
        for c in cols:
            val = r.get(c, "")
            if c == "Reason":
                table_html += f"<td>{val}</td>"
            else:
                table_html += f"<td>{'' if pd.isna(val) else val}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"
    return table_html

# ------------------ ROUTES ------------------
@app.route("/", methods=["GET"])
def home():
    return render_template_string(
        HTML_PAGE, table=None, message=None,
        last_students=session.get("last_students"),
        last_mentors=session.get("last_mentors")
    )

@app.route("/upload_mentors", methods=["POST"])
def upload_mentors():
    f = request.files.get("mentors_file")
    if not f:
        return render_template_string(
            HTML_PAGE, table=None, message="No mentors file uploaded.",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )
    try:
        content = f.read()
        with open(MENTORS_CSV, "wb") as fh:
            fh.write(content)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session["last_mentors"] = f"{f.filename} uploaded at {ts}"
        return render_template_string(
            HTML_PAGE, table=None, message=f"Saved mentors to {MENTORS_CSV} at {ts}.",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )
    except Exception as e:
        return render_template_string(
            HTML_PAGE, table=None, message=f"Error saving mentors file: {e}",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )

@app.route("/predict", methods=["POST"])
def predict():
    f = request.files.get("file")
    if not f:
        return render_template_string(
            HTML_PAGE, table=None, message="No student CSV uploaded.",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )
    try:
        # pandas auto-detects encoding fairly well; fallback to utf-8 if needed
        df_students = pd.read_csv(f)
    except Exception as e:
        return render_template_string(
            HTML_PAGE, table=None, message=f"Failed to read CSV: {e}",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )

    try:
        df_proc = process_students_df(df_students)
        filename = getattr(f, "filename", "students.csv")
        session["last_students"] = f"{filename} uploaded at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    except Exception as e:
        return render_template_string(
            HTML_PAGE, table=None, message=f"Error processing students: {e}",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )

    try:
        mentors_list = load_mentors_list(MENTORS_CSV)
        if not mentors_list:
            # show table without mentors + prompt
            scheduled_display = df_proc.rename(columns={
                "RollNumber": "Roll No", "Name": "Student Name", "AttendancePercent": "Attendance %",
                "AvgGrade": "Average Grade", "DistanceKM": "Distance (km)", "ParentEducation": "Parent Education",
                "FamilyIncome": "Family Income", "Siblings": "No. of Siblings", "PastAbsences": "Past Absences"
            }).copy()

            for col in COLUMN_ORDER:
                if col not in scheduled_display.columns:
                    scheduled_display[col] = ""
            table = make_html_table(scheduled_display[COLUMN_ORDER])
            return render_template_string(
                HTML_PAGE, table=table,
                message="No mentors found in mentors.csv — upload one or check file format.",
                last_students=session.get("last_students"),
                last_mentors=session.get("last_mentors")
            )

        scheduled = assign_mentors(df_proc, mentors_list)
        scheduled_display = scheduled.rename(columns={
            "RollNumber": "Roll No", "Name": "Student Name", "AttendancePercent": "Attendance %",
            "AvgGrade": "Average Grade", "DistanceKM": "Distance (km)", "ParentEducation": "Parent Education",
            "FamilyIncome": "Family Income", "Siblings": "No. of Siblings", "PastAbsences": "Past Absences"
        }).copy()

        for col in COLUMN_ORDER:
            if col not in scheduled_display.columns:
                scheduled_display[col] = ""
        table_html = make_html_table(scheduled_display[COLUMN_ORDER])
        session["last_results"] = scheduled_display.to_dict(orient="records")
        return render_template_string(
            HTML_PAGE, table=table_html, message="Prediction & mentor assignment complete.",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )
    except Exception as e:
        return render_template_string(
            HTML_PAGE, table=None, message=f"Error during mentor assignment: {e}",
            last_students=session.get("last_students"),
            last_mentors=session.get("last_mentors")
        )

# ------------------ MAIN ------------------
if __name__ == "__main__":
    # create a helpful sample mentors.csv if missing
    if not os.path.exists(MENTORS_CSV):
        sample = """MentorName,Expertise,SlotStart,SlotEnd
Dr. Smith,Mathematics,2025-09-09 09:00,2025-09-09 11:00
Prof. Anita,Science,2025-09-09 11:30,2025-09-09 13:30
Mr. John,Computer Science,2025-09-09 14:00,2025-09-09 16:00
Ms. Priya,English,2025-09-09 16:30,2025-09-09 18:30
Dr. Raj,Mathematics,2025-09-10 09:00,2025-09-10 11:00
Prof. Meera,Science,2025-09-10 11:30,2025-09-10 13:30
Mr. Karthik,Computer Science,2025-09-10 14:00,2025-09-10 16:00
Ms. Neha,English,2025-09-10 16:30,2025-09-10 18:30
"""
        with open(MENTORS_CSV, "w", encoding="utf-8") as fh:
            fh.write(sample)
        print(f"Sample mentors.csv created at {MENTORS_CSV}.")
    app.run(debug=True)
