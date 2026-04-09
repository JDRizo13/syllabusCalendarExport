from typing import List, Dict, Optional
from dataclasses import dataclass
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
DAY_MONTH_RE = re.compile(r"\b(\d{1,2})\s+(Jan|January|Feb|February|Mar|March|Apr|April|May|Jun|June|Jul|July|Aug|August|Sep|Sept|September|Oct|October|Nov|November|Dec|December)\b", re.I)
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


@dataclass
class ParsedCandidate:
    raw_text: str
    page_num: int
    section: str
    kind: str
    date: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    location: Optional[str]
    confidence: float


@dataclass
class RecurringRule:
    raw_text: str
    page_num: int
    days: List[str]
    time: Optional[str]
    section: str

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

    day_month_match = DAY_MONTH_RE.search(line)
    if day_month_match:
        day = int(day_month_match.group(1))
        month_str = day_month_match.group(2).lower()
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


# New helper functions for recurring rules and candidate building
def parse_recurring_rule(line: str, page_num: int, section: str) -> Optional[RecurringRule]:
    lower = line.lower()
    recurring_days = []

    day_map = {
        "monday": "MO",
        "tuesday": "TU",
        "wednesday": "WE",
        "thursday": "TH",
        "friday": "FR",
        "saturday": "SA",
        "sunday": "SU",
    }

    for day_name, day_code in day_map.items():
        plural_pattern = rf"\b{day_name}s\b"
        singular_pattern = rf"\b{day_name}\b"
        if re.search(plural_pattern, lower) or re.search(singular_pattern, lower):
            recurring_days.append(day_code)

    if not recurring_days:
        return None

    start_time, _ = parse_time_range(line)
    return RecurringRule(
        raw_text=line,
        page_num=page_num,
        days=recurring_days,
        time=start_time,
        section=section,
    )


def compute_confidence(line: str, section: str, kind: str, has_date: bool, has_time: bool) -> float:
    lower = line.lower()
    confidence = 0.15

    if has_date:
        confidence += 0.35
    if has_time:
        confidence += 0.10
    if section in {"assignments", "schedule"}:
        confidence += 0.20
    if kind in {"assignment_due", "exam", "quiz", "holiday", "required_event"}:
        confidence += 0.15
    if any(word in lower for word in ["due", "required", "midterm", "final", "quiz"]):
        confidence += 0.10
    if any(noise in lower for noise in ["page ", "last revised", "course description", "office hours"]):
        confidence -= 0.25
    if kind == "lecture" and "due" not in lower and "exam" not in lower:
        confidence -= 0.10

    return max(0.05, min(0.99, round(confidence, 2)))


def build_candidate(line: str, page_num: int, section: str, year: int) -> Optional[ParsedCandidate]:
    if not useful_line(line):
        return None
    
    date = parse_date(line, year)
    if not date:
        return None

    start_time, end_time = parse_time_range(line)
    kind = infer_event_kind(line, section)
    if kind == "other":
        return None
    location = extract_location(line)
    confidence = compute_confidence(
        line=line,
        section=section,
        kind=kind,
        has_date=date is not None,
        has_time=start_time is not None,
    )

    return ParsedCandidate(
        raw_text=line,
        page_num=page_num,
        section=section,
        kind=kind,
        date=date,
        start_time=start_time,
        end_time=end_time,
        location=location,
        confidence=confidence,
    )

def useful_line(line: str):
    lower = line.lower()
    if any(bad in lower for bad in BAD_KEYWORDS):
        return False
    if not any(good in lower for good in GOOD_KEYWORDS):
        return False
    if not (DATE_RE.search(line) or DAY_MONTH_RE.search(line) or NUMERIC_DATE_RE.search(line) or DATE_RANGE_RE.search(line)):
        return False
    return True

def normalize_title(line: str):
    return re.sub(r"\s+", " ", line.strip().lower())

def extract_location(line: str) -> Optional[str]:
    location_match = re.search(r"\b\d+\s+[A-Za-z][A-Za-z\s]+", line)
    if location_match:
        return location_match.group(0).strip()
    return None


# Section/kind logic block and categorize
def classify_section(line: str, current_section: str = "other") -> str:
    lower = line.lower()

    section_headers = {
        "grading": ["grading", "evaluation"],
        "assignments": ["assignments", "writing", "research portfolio", "written assignment", "midterm paper"],
        "policies": ["attendance", "late work", "honor code", "academic honesty", "special notes"],
        "schedule": ["content overview", "lecture outline", "week lecture description", "class schedule", "readings"],
        "course_info": ["course description", "course objectives", "course information and procedures"],
    }

    for section_name, markers in section_headers.items():
        if any(marker in lower for marker in markers):
            return section_name

    return current_section



def infer_event_kind(line: str, section: str) -> str:
    lower = line.lower()

    if "midterm" in lower or "final exam" in lower or "final examination" in lower or ("exam" in lower and "review" not in lower):
        return "exam"
    if "quiz" in lower:
        return "quiz"
    if "no class" in lower or "holiday" in lower or "recess" in lower or "reading week" in lower or "spring break" in lower:
        return "holiday"
    if "required" in lower and ("fair" in lower or "conference" in lower or "meeting" in lower):
        return "required_event"
    if "due" in lower or "proposal" in lower or "bibliography" in lower or "paper" in lower or "project" in lower or "ps" in lower or "problem set" in lower:
        return "assignment_due"
    return "other"



def categorize(kind: str) -> str:
    if kind == "exam":
        return "exam"
    if kind == "quiz":
        return "quiz"
    if kind == "assignment_due":
        return "assignment"
    if kind == "holiday":
        return "holiday"
    return "other"


# New clean_title version
def clean_title(line: str, class_name: str, kind: str = "other"):
    lower = line.lower()

    if "annotated bibliography" in lower:
        return f"Annotated Bibliography — {class_name}"
    if "proposal" in lower:
        return f"Research Proposal — {class_name}"
    if "completed paper" in lower or "final project" in lower:
        return f"Final Project — {class_name}"
    if "research paper and portfolio due" in lower:
        return f"Research Paper & Portfolio Due — {class_name}"
    if "reflection due" in lower:
        return f"Reflection Due — {class_name}"
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
    if "spring recess" in lower or "spring break" in lower:
        return f"Spring Recess — {class_name}"
    if "reading week" in lower:
        return f"Reading Week — {class_name}"
    if "no class" in lower:
        return f"No Class — {class_name}"
    if kind == "required_event":
        cleaned = re.sub(r"\s+", " ", line).strip()
        return f"{cleaned[:55]} — {class_name}"
    if "due" in lower or kind == "assignment_due":
        cleaned = re.sub(r"\s+", " ", line).strip()
        return f"{cleaned[:50]} — {class_name}"
    return re.sub(r"\s+", " ", line).strip()[:80]

def parse_syllabus_pdf(file_bytes: bytes) -> List[Dict]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    events = []
    seen = set()
    recurring_rules: List[RecurringRule] = []

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

    current_section = "other"

    for page_num, lines in enumerate(page_lines, start=1):
        for line in lines:
            current_section = classify_section(line, current_section)

            recurring_rule = parse_recurring_rule(line, page_num, current_section)
            if recurring_rule is not None:
                recurring_rules.append(recurring_rule)

            candidate = build_candidate(line, page_num, current_section, year)
            if candidate is None:
                continue

            title = clean_title(candidate.raw_text, short_class_name, candidate.kind)
            title_key = normalize_title(f"{title}|{candidate.date}|{candidate.kind}")
            if title_key in seen:
                continue
            seen.add(title_key)

            notes_parts = [
                f"Source line: {candidate.raw_text}",
                f"Section: {candidate.section}",
                f"Kind: {candidate.kind}",
            ]
            if candidate.location:
                notes_parts.append(f"Location: {candidate.location}")

            matching_rules = [rule for rule in recurring_rules if rule.page_num == page_num and rule.section == candidate.section]
            if matching_rules:
                rule = matching_rules[-1]
                notes_parts.append(f"Recurring rule context: days={','.join(rule.days)} time={rule.time or 'unspecified'}")

            events.append({
                "id": str(uuid.uuid4()),
                "title": title,
                "date": candidate.date,
                "startTime": candidate.start_time,
                "endTime": candidate.end_time,
                "category": categorize(candidate.kind),
                "confidence": candidate.confidence,
                "sourceSnippet": f"Page {candidate.page_num}: {candidate.raw_text}",
                "notes": " | ".join(notes_parts),
            })

    return events
