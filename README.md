# syllabusCalendarExport
A full-stack web application that parses syllabus PDFs, extracts key academic events (assignments, exams, deadlines), and converts them into calendar-ready formats. Users can review and edit extracted events before exporting to .ics for seamless integration with Google Calendar or iOS.

# 📅 Syllabus Calendar Extractor

A full-stack web application that converts course syllabus PDFs into structured calendar events.

Upload a syllabus, automatically extract important dates (assignments, exams, deadlines), review and edit them, and export to an `.ics` file for seamless import into Google Calendar or Apple Calendar.

---

## 🚀 Features

- 📄 Upload syllabus PDFs
- 🧠 Extract key academic events (assignments, exams, deadlines)
- ✏️ Editable review table before export
- 📆 Export events as `.ics` (compatible with Google Calendar, Apple Calendar, Outlook)
- 🔍 Confidence scoring + source snippets for transparency

---

## Tech Stack

### Frontend
- Next.js (App Router)
- TypeScript
- Tailwind CSS

### Backend
- FastAPI (Python)
- PyMuPDF (PDF text extraction)
- Regex-based parsing (initial version)
- iCalendar (`.ics`) generation

---

## 📂 Project Structure
---
syllabus-calendar-extractor/
├── frontend/          # Next.js app
│   ├── app/
│   ├── components/
│   └── lib/
├── parser-service/    # FastAPI backend
│   ├── main.py
│   ├── sample_parser.py
│   └── requirements.txt

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/syllabus-calendar-extractor.git
cd syllabus-calendar-extractor 
```
### 2. Frontend Setup 
cd frontend
npm install
npm run dev
Will Run At: http://localhost:3000 (Copy and paste in browser)

### 2. Backend Setup 
cd parser-service

# Create virtual environment (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run server
python -m uvicorn main:app --reload
Will Run At: http://127.0.0.1:8000

# How It Works
	1.	User uploads a syllabus PDF
	2.	Backend extracts text using PyMuPDF
	3.	Parser identifies relevant lines (deadlines, exams, events)
	4.	Dates are normalized into structured event objects
	5.	Frontend displays an editable table
	6.	User exports events as .ics

# Current Limitations
	•	Rule-based parser (may miss complex syllabus formats)
	•	Limited time extraction accuracy
	•	Some duplicate or noisy text may appear
	•	English-only support

# Future Improvements
	•	NLP / LLM-based extraction for higher accuracy
	•	Automatic semester/year detection
	•	Table-aware parsing for structured syllabi
	•	Google Calendar API integration
	•	Improved deduplication and filtering
	•	Better UI (bulk edits, tagging, filters)

# Motivation
Students often spend time manually transferring syllabus deadlines into their calendars. This project automates that workflow, making it faster and less error-prone to stay organized throughout the semester.

# Author
Juan Rizo

