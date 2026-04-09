from typing import List, Dict, Optional
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
NUMERIC_DATE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b")
DATE_RANGE_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})\s*[–-]\s*(\d{1,2})\b")
TIME_RE = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(a\.?m\.?|p\.?m\.?)", re.I)

DEFAULT_YEAR = 2026

GOOD_KEYWORDS = [
    "due",
    "midterm",
    "exam",
    "final",
    "quiz",
    "no class",
    "holiday",
    "recess",
    "spring break",
    "discussion leading assignments will be finalized",
    "talk:",
    "discussion:",
    "lecture",
    "review",
    "ps",
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
    "office hours",
    "respond to emails",
    "mailbox",
    "text:",
]

def extract_class_name(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    search_lines = lines[:40]
    season_words = {"SPRING", "SUMMER", "FALL", "WINTER"}
    admin_phrases = {
        "department of",
        "university of california",
        "course information",
        "course description",
        "lecture and sections",
        "readings",
        "assignments",
        "grading",
        "office hours",
    }

    def clean_line(line: str) -> str:
        line = re.sub(r"[\u00ad\u2010\u2011\u2012\u2013\u2014]", "-", line)
        line = re.sub(r"\s+", " ", line).strip(" -|:\t•")
        return line

    def subject_to_abbrev(subject: str) -> str:
        cleaned = re.sub(r"[^A-Za-z& ]", " ", subject).upper()
        cleaned = re.sub(r"\b(DEPARTMENT OF|UNIVERSITY OF CALIFORNIA|UNIVERSITY|DEPARTMENT)\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        alias_map = {
            "AMERICAN STUDIES": "AS",
            "ECONOMICS": "ECON",
            "HISTORY": "HIST",
            "ENGLISH": "ENGL",
            "POLITICAL SCIENCE": "POLSCI",
            "PSYCHOLOGY": "PSYCH",
            "SOCIOLOGY": "SOCIOL",
            "MATHEMATICS": "MATH",
            "STATISTICS": "STAT",
            "PHYSICS": "PHYS",
            "CHEMISTRY": "CHEM",
            "BIOLOGY": "BIO",
            "MOLECULAR AND CELL BIOLOGY": "MCB",
            "COMPUTER SCIENCE": "CS",
            "DATA SCIENCE": "DATA",
            "ELECTRICAL ENGINEERING AND COMPUTER SCIENCES": "EECS",
            "MECHANICAL ENGINEERING": "ME",
            "CIVIL AND ENVIRONMENTAL ENGINEERING": "CEE",
            "CHEMICAL ENGINEERING": "CHEME",
            "INDUSTRIAL ENGINEERING AND OPERATIONS RESEARCH": "IEOR",
            "BUSINESS ADMINISTRATION": "UGBA",
            "PUBLIC HEALTH": "PBHLTH",
            "ENVIRONMENTAL SCIENCE POLICY AND MANAGEMENT": "ESPM",
            "CHEMC": "CHEMC",
            "MCBC": "MCBC",
        }
        if cleaned in alias_map:
            return alias_map[cleaned]

        words = [word for word in cleaned.split() if word not in {"AND", "OF", "THE"}]
        if not words:
            return ""
        if len(words) == 1:
            return words[0][:8]
        return "".join(word[0] for word in words[:4])

    def normalize_course_code(code: str) -> str:
        code = re.sub(r"\s+", "", code)
        code = re.sub(r"-+", "-", code)
        return code.upper()

    def is_likely_course_code(code: str) -> bool:
        normalized = normalize_course_code(code)
        pieces = re.split(r"[-/&]", normalized)
        if not pieces:
            return False

        for piece in pieces:
            if not piece:
                return False
            if piece in season_words:
                return False
            if re.fullmatch(r"CCN\d+", piece):
                return False
            if re.fullmatch(r"PAGE\d+", piece):
                return False
            if not re.fullmatch(r"[A-Z]{2,12}\d{1,3}[A-Z]{0,2}", piece):
                return False
        return True

    def looks_like_title(title: str) -> bool:
        lowered = title.lower()
        if len(title) < 4:
            return False
        banned_phrases = [
            "page ",
            "last revised",
            "units",
            "ccn",
            "class times",
            "office hours",
            "course information",
            "course description",
        ]
        return not any(phrase in lowered for phrase in banned_phrases)

    def clean_title_value(title: str) -> str:
        title = clean_line(title)
        title = re.sub(r"\b(Spring|Summer|Fall|Winter)\s+20\d{2}\b", "", title, flags=re.I)
        title = re.sub(r"\bPage\s+\d+\s+of\s+\d+\b", "", title, flags=re.I)
        title = re.sub(r"\|", " ", title)
        title = re.sub(r"\s+", " ", title).strip(" -|:")
        return title

    def format_result(code: Optional[str], title: Optional[str] = None) -> str:
        cleaned_title = clean_title_value(title) if title else None
        if code and cleaned_title and looks_like_title(cleaned_title):
            return f"{normalize_course_code(code)} — {cleaned_title[:50]}"
        if code:
            return normalize_course_code(code)
        if cleaned_title:
            return cleaned_title[:60]
        return "Course"

    subject_number_re = re.compile(r"\b([A-Za-z][A-Za-z& ]{1,40})\s+([A-Z]?\d{1,3}[A-Z]{0,2})\b")
    compact_code_re = re.compile(r"\b([A-Za-z]{2,12}\s*\d{1,3}[A-Za-z]{0,2}(?:\s*[-/&]\s*[A-Za-z]{2,12}\s*\d{1,3}[A-Za-z]{0,2})*)\b")

    best_code = None
    best_title = None

    for index, raw_line in enumerate(search_lines):
        line = clean_line(raw_line)
        if not line:
            continue

        lowered = line.lower()
        if any(phrase in lowered for phrase in admin_phrases):
            continue

        if line.lower().startswith("syllabus:"):
            syllabus_value = clean_title_value(line.split(":", 1)[1])
            compact_match = compact_code_re.search(syllabus_value)
            if compact_match and is_likely_course_code(compact_match.group(1)):
                code = normalize_course_code(compact_match.group(1))
                title = syllabus_value.replace(compact_match.group(0), "", 1).strip(" -|:")
                if looks_like_title(title):
                    return format_result(code, title)
                return format_result(code)

        subject_match = subject_number_re.search(line)
        if subject_match:
            subject = subject_match.group(1)
            number = subject_match.group(2)
            subject_abbrev = subject_to_abbrev(subject)
            if subject_abbrev:
                code = normalize_course_code(f"{subject_abbrev}{number}")
                if is_likely_course_code(code):
                    next_line = ""
                    if index + 1 < len(search_lines):
                        next_line = clean_title_value(search_lines[index + 1])
                    if looks_like_title(next_line) and next_line.upper() == next_line:
                        return format_result(code, next_line.title())
                    best_code = best_code or code

        compact_match = compact_code_re.search(line)
        if compact_match and is_likely_course_code(compact_match.group(1)):
            code = normalize_course_code(compact_match.group(1))
            tail = clean_title_value(line.replace(compact_match.group(0), "", 1))
            if looks_like_title(tail):
                return format_result(code, tail)
            best_code = best_code or code

        if best_code and best_title is None:
            candidate_line = clean_title_value(line)
            if looks_like_title(candidate_line) and candidate_line.upper() == candidate_line and not re.search(r"\d", candidate_line):
                best_title = candidate_line.title()

    if best_code and best_title:
        return format_result(best_code, best_title)
    if best_code:
        return best_code

    for raw_line in search_lines:
        line = clean_line(raw_line)
        if not line:
            continue
        if line.lower().startswith("syllabus:"):
            return clean_title_value(line.split(":", 1)[1])[:60]

    return "Course"


# Helper: Extract just the class code from a class name string
def class_code_only(class_name: str) -> str:
    match = re.match(r"^([A-Z]{2,12}\d{1,3}[A-Z]{0,2}(?:[-/&][A-Z]{2,12}\d{1,3}[A-Z]{0,2})*)", class_name)
    if match:
        return match.group(1)
    return class_name


def extract_year(text: str) -> int:
    match = re.search(r"\b(20\d{2})\b", text)
    if match:
        return int(match.group(1))
    return DEFAULT_YEAR


def parse_date(line: str, year: int) -> Optional[str]:
    month_name_match = DATE_RE.search(line)
    if month_name_match:
        month_str = month_name_match.group(1).lower()
        day = int(month_name_match.group(2))
        month = MONTH_MAP[month_str]
        return datetime(year, month, day).strftime("%Y-%m-%d")

    numeric_match = NUMERIC_DATE_RE.search(line)
    if numeric_match:
        month = int(numeric_match.group(1))
        day = int(numeric_match.group(2))
        raw_year = numeric_match.group(3)
        parsed_year = year
        if raw_year:
            if len(raw_year) == 2:
                parsed_year = 2000 + int(raw_year)
            else:
                parsed_year = int(raw_year)
        return datetime(parsed_year, month, day).strftime("%Y-%m-%d")

    return None

def parse_time_range(line: str):
    matches = list(TIME_RE.finditer(line))
    if not matches:
        return None, None

    def to_24_hour(match):
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        ampm = match.group(3).lower()
        if "p" in ampm and hour != 12:
            hour += 12
        if "a" in ampm and hour == 12:
            hour = 0
        return f"{hour:02d}:{minute:02d}"

    start_time = to_24_hour(matches[0])
    end_time = to_24_hour(matches[1]) if len(matches) > 1 else None
    return start_time, end_time

def categorize(line: str):
    lower = line.lower()
    if "midterm" in lower or "exam" in lower or "final" in lower:
        return "exam"
    if "quiz" in lower:
        return "quiz"
    if "due" in lower or "ps" in lower or "proposal" in lower or "bibliography" in lower or "paper" in lower or "project" in lower:
        return "assignment"
    if "no class" in lower or "holiday" in lower or "recess" in lower or "reading week" in lower:
        return "holiday"
    if "lecture" in lower:
        return "lecture"
    if "talk:" in lower or "discussion:" in lower:
        return "other"
    return "other"

def useful_line(line: str):
    lower = line.lower()
    if any(bad in lower for bad in BAD_KEYWORDS):
        return False
    if not any(good in lower for good in GOOD_KEYWORDS):
        return False
    if not (DATE_RE.search(line) or NUMERIC_DATE_RE.search(line) or DATE_RANGE_RE.search(line)):
        return False
    return True

def normalize_title(line: str):
    return re.sub(r"\s+", " ", line.strip().lower())

def extract_location(line: str) -> Optional[str]:
    location_match = re.search(r"\b\d+\s+[A-Za-z][A-Za-z\s]+", line)
    if location_match:
        return location_match.group(0).strip()
    return None


def clean_title(line: str, class_name: str):
    lower = line.lower()

    if "annotated bibliography" in lower:
        return f"Annotated Bibliography — {class_name}"
    if "proposal" in lower:
        return f"Research Proposal — {class_name}"
    if "completed paper" in lower or "final project" in lower:
        return f"Final Project — {class_name}"
    if "revised research paper" in lower:
        return f"Revised Research Paper — {class_name}"
    if "midterm" in lower and "review" not in lower:
        midterm_number = re.search(r"midterm\s*(i{1,3}|\d+|first|second|third)", lower)
        if midterm_number:
            value = midterm_number.group(1).upper()
            ordinal_map = {"FIRST": "1", "SECOND": "2", "THIRD": "3"}
            value = ordinal_map.get(value, value)
            return f"Midterm {value} — {class_name}"
        return f"Midterm — {class_name}"
    if "final exam" in lower or "final examination" in lower:
        return f"Final Exam — {class_name}"
    if "problem set" in lower and "due" in lower:
        ps_match = re.search(r"problem set\s*(\d+)", lower)
        if ps_match:
            return f"Problem Set {ps_match.group(1)} Due — {class_name}"
        return f"Problem Set Due — {class_name}"
    if "ps" in lower and "due" in lower:
        ps_match = re.search(r"ps\s*(\d+)", lower)
        if ps_match:
            return f"PS {ps_match.group(1)} Due — {class_name}"
        return f"Problem Set Due — {class_name}"
    if "quiz" in lower:
        quiz_match = re.search(r"week\s*(\d+)", lower)
        if quiz_match:
            return f"Quiz {quiz_match.group(1)} — {class_name}"
        return f"Quiz — {class_name}"
    if "paper due" in lower:
        return f"Paper Due — {class_name}"
    if "term papers due" in lower or "term paper due" in lower:
        return f"Term Paper Due — {class_name}"
    if "field trip" in lower and "due" in lower:
        trip_match = re.search(r"field trip\s*#?(\d+)", lower)
        if trip_match:
            return f"Field Trip #{trip_match.group(1)} Due — {class_name}"
        return f"Field Trip Due — {class_name}"
    if "topic due" in lower:
        return f"Topic Due — {class_name}"
    if "sketch due" in lower:
        return f"Sketch Due — {class_name}"
    if "spring recess" in lower:
        return f"Spring Recess — {class_name}"
    if "reading week" in lower:
        return f"Reading Week — {class_name}"
    if "no class" in lower:
        return f"No Class — {class_name}"
    if "talk:" in lower or "discussion:" in lower or "lecture" in lower:
        trimmed = re.sub(r"\s+", " ", line).strip()
        return trimmed[:80]
    if "due" in lower:
        cleaned = re.sub(r"\s+", " ", line).strip()
        return f"{cleaned[:50]} — {class_name}"
    return re.sub(r"\s+", " ", line).strip()[:80]

def parse_syllabus_pdf(file_bytes: bytes) -> List[Dict]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    events = []
    seen = set()

    full_text_parts = []
    page_lines = []
    for page in doc:
        text = page.get_text()
        full_text_parts.append(text)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        page_lines.append(lines)

    full_text = "\n".join(full_text_parts)
    class_name = extract_class_name(full_text)
    short_class_name = class_code_only(class_name)
    year = extract_year(full_text)

    for page_num, lines in enumerate(page_lines, start=1):
        for line in lines:
            if not useful_line(line):
                continue

            date = parse_date(line, year)
            if not date:
                continue

            title = clean_title(line, short_class_name)
            title_key = normalize_title(f"{title}|{date}")
            if title_key in seen:
                continue
            seen.add(title_key)

            start_time, end_time = parse_time_range(line)
            location = extract_location(line)

            confidence = 0.78
            if page_num >= max(len(page_lines) - 1, 1):
                confidence = 0.93
            elif page_num >= 4:
                confidence = 0.88

            notes_parts = [f"Source line: {line}"]
            if location:
                notes_parts.append(f"Location: {location}")

            events.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "date": date,
                "startTime": start_time,
                "endTime": end_time,
                "category": categorize(line),
                "confidence": confidence,
                "sourceSnippet": f"Page {page_num}: {line}",
                "notes": " | ".join(notes_parts),
            })

    return events
