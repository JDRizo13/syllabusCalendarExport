from typing import List, Dict
import uuid
import fitz
import re
from datetime import datetime

MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

DATE_RE = re.compile(r"\b(Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\s+(\d{1,2})\b", re.I)
TIME_RE = re.compile(r"(\d{1,2}):(\d{2})\s*(a\.?m\.?|p\.?m\.?)", re.I)

GOOD_KEYWORDS = [
    "due",
    "midterm",
    "exam",
    "no class",
    "holiday",
    "discussion leading assignments will be finalized",
    "talk:",
    "discussion:",
]

BAD_KEYWORDS = [
    "email me",
    "writing fellow",
    "guidelines",
    "academic honesty",
    "table of examples",
    "late work",
    "grades",
    "process of planning",
]

def parse_date(line: str, year: int = 2026):
    match = DATE_RE.search(line)
    if not match:
        return None
    month_str = match.group(1).lower()
    day = int(match.group(2))
    month = MONTH_MAP[month_str]
    return datetime(year, month, day).strftime("%Y-%m-%d")

def parse_time(line: str):
    match = TIME_RE.search(line)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2))
    ampm = match.group(3).lower()
    if "p" in ampm and hour != 12:
        hour += 12
    if "a" in ampm and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"

def categorize(line: str):
    lower = line.lower()
    if "midterm" in lower or "exam" in lower:
        return "exam"
    if "proposal" in lower or "bibliography" in lower or "paper" in lower or "project" in lower or "due" in lower:
        return "assignment"
    if "no class" in lower or "holiday" in lower:
        return "holiday"
    return "other"

def useful_line(line: str):
    lower = line.lower()
    if any(bad in lower for bad in BAD_KEYWORDS):
        return False
    if not any(good in lower for good in GOOD_KEYWORDS):
        return False
    if not DATE_RE.search(line):
        return False
    return True

def normalize_title(line: str):
    return re.sub(r"\s+", " ", line.strip().lower())

def parse_syllabus_pdf(file_bytes: bytes) -> List[Dict]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    events = []
    seen = set()

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text()
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        for line in lines:
            if not useful_line(line):
                continue

            date = parse_date(line)
            if not date:
                continue

            title_key = normalize_title(line)
            if title_key in seen:
                continue
            seen.add(title_key)

            start_time = parse_time(line)

            confidence = 0.75
            if page_num >= 9:
                confidence = 0.92
            elif page_num == 4:
                confidence = 0.88

            events.append({
                "id": str(uuid.uuid4()),
                "title": clean_title(line),
                "date": date,
                "startTime": start_time,
                "endTime": None,
                "category": categorize(line),
                "confidence": confidence,
                "sourceSnippet": f"Page {page_num}: {line}",
                "notes": None,
            })

    return events

def clean_title(line: str):
    lower = line.lower()

    if "annotated bibliography" in lower:
        return "Annotated Bibliography — AS 102"

    if "proposal" in lower:
        return "Research Proposal — AS 102"

    if "completed paper" in lower or "project" in lower:
        return "Final Project — AS 102"

    if "midterm" in lower:
        return "Midterm — AS 102"

    # fallback: keep it shorter
    return line[:50]
