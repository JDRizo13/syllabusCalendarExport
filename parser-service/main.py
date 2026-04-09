from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from icalendar import Calendar, Event
from datetime import datetime
from sample_parser import parse_syllabus_pdf

# from sample_parser import mock_parse_syllabus

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://syllabus-calendar-export.vercel.app",
    ],
    allow_origin_regex=r"https://.*vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ParsedEvent(BaseModel):
    id: str
    title: str
    date: str
    startTime: Optional[str] = None
    endTime: Optional[str] = None
    category: Optional[str] = "other"
    confidence: float
    sourceSnippet: Optional[str] = None
    notes: Optional[str] = None

class ExportRequest(BaseModel):
    events: List[ParsedEvent]

@app.get("/health")
def health_check():
    return {"ok": True}

@app.post("/upload-syllabus")
async def upload_syllabus(file: UploadFile = File(...)):
    contents = await file.read()
    events = parse_syllabus_pdf(contents)
    return {"events": events}

@app.post("/export-ics")
def export_ics(payload: ExportRequest):
    cal = Calendar()
    cal.add("prodid", "-//Syllabus Calendar Extractor//")
    cal.add("version", "2.0")

    for item in payload.events:
        event = Event()
        event.add("summary", item.title)

        if item.startTime:
            start_dt = datetime.fromisoformat(f"{item.date}T{item.startTime}")
        else:
            start_dt = datetime.fromisoformat(f"{item.date}T09:00")

        if item.endTime:
            end_dt = datetime.fromisoformat(f"{item.date}T{item.endTime}")
        else:
            end_dt = datetime.fromisoformat(f"{item.date}T10:00")

        event.add("dtstart", start_dt)
        event.add("dtend", end_dt)
        if item.notes:
            event.add("description", item.notes)
        cal.add_component(event)

    return Response(
        content=cal.to_ical(),
        media_type="text/calendar",
        headers={"Content-Disposition": "attachment; filename=syllabus-events.ics"},
    )