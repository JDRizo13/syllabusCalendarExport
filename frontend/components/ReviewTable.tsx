"use client";

import { Dispatch, SetStateAction } from "react";
import { ParsedEvent } from "@/lib/types";

type Props = {
  events: ParsedEvent[];
  setEvents: Dispatch<SetStateAction<ParsedEvent[]>>;
  onExport: () => void;
  isExporting: boolean;
};

const categoryStyles: Record<string, string> = {
  assignment:
    "border-sky-200 bg-sky-100/80 text-sky-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  exam: "border-rose-200 bg-rose-100/80 text-rose-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  project:
    "border-violet-200 bg-violet-100/80 text-violet-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  quiz: "border-amber-200 bg-amber-100/80 text-amber-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  lab: "border-teal-200 bg-teal-100/80 text-teal-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  holiday:
    "border-emerald-200 bg-emerald-100/80 text-emerald-950 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
  other:
    "border-slate-200 bg-slate-100/80 text-slate-900 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]",
};

function confidenceStyle(value: number) {
  if (value >= 0.9) {
    return "border-emerald-200 bg-emerald-100/80 text-emerald-950";
  }

  if (value >= 0.75) {
    return "border-amber-200 bg-amber-100/80 text-amber-950";
  }

  return "border-rose-200 bg-rose-100/80 text-rose-950";
}

function confidenceLabel(value: number) {
  if (value >= 0.9) return "Locked in";
  if (value >= 0.75) return "Worth a look";
  return "Needs review";
}

function categoryLabel(category: ParsedEvent["category"]) {
  switch (category) {
    case "assignment":
      return "Assignment";
    case "exam":
      return "Exam";
    case "project":
      return "Project";
    case "quiz":
      return "Quiz";
    case "lab":
      return "Lab";
    case "holiday":
      return "Holiday";
    default:
      return "Other";
  }
}

const fieldClassName =
  "block h-12 w-full min-w-0 rounded-2xl border border-white/70 bg-white/90 px-4 text-sm font-medium text-slate-900 shadow-[0_8px_30px_rgba(15,23,42,0.06)] outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-400/20";

const textAreaClassName =
  "block min-h-[112px] w-full min-w-0 resize-y rounded-2xl border border-white/70 bg-white/90 px-4 py-3 text-sm font-medium text-slate-900 shadow-[0_8px_30px_rgba(15,23,42,0.06)] outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:bg-white focus:ring-2 focus:ring-sky-400/20";

export default function ReviewTable({
  events,
  setEvents,
  onExport,
  isExporting,
}: Props) {
  const updateField = <K extends keyof ParsedEvent>(
    id: string,
    field: K,
    value: ParsedEvent[K]
  ) => {
    setEvents((prev) =>
      prev.map((event) =>
        event.id === id ? { ...event, [field]: value } : event
      )
    );
  };

  if (events.length === 0) return null;

  return (
    <section className="mt-8 overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.95),rgba(241,245,249,0.92))] shadow-[0_24px_80px_rgba(15,23,42,0.14)] ring-1 ring-slate-900/5">
      <div className="relative overflow-hidden border-b border-slate-200/80 px-5 py-6 sm:px-7 sm:py-8">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(14,165,233,0.16),transparent_32%),radial-gradient(circle_at_top_right,rgba(251,191,36,0.18),transparent_28%)]" />

        <div className="relative flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="min-w-0">
            <div className="mb-4 flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center rounded-full border border-slate-200 bg-white/85 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500 backdrop-blur">
                Final review
              </span>
              <span className="inline-flex max-w-full items-center rounded-full border border-sky-200 bg-sky-100/80 px-3 py-1 text-center text-xs font-semibold text-sky-950 whitespace-normal break-words">
                {events.length} extracted {events.length === 1 ? "event" : "events"}
              </span>
            </div>

            <h2 className="max-w-2xl text-3xl font-black tracking-tight text-slate-950 sm:text-4xl">
              Give each event a final polish.
            </h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
              Tighten titles, dates, and categories so the export feels curated,
              clear, and genuinely ready to drop into a real calendar. (Always double check important info, lectures/discussions not included)
            </p>
          </div>

          <button
            onClick={onExport}
            disabled={isExporting}
            className="inline-flex h-12 shrink-0 items-center justify-center rounded-2xl bg-slate-950 px-6 text-sm font-semibold text-white shadow-[0_16px_40px_rgba(15,23,42,0.28)] transition hover:-translate-y-0.5 hover:bg-slate-800 disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isExporting ? "Exporting..." : "Export .ics"}
          </button>
        </div>
      </div>

      <div className="space-y-5 px-4 py-5 sm:px-6 sm:py-6">
        {events.map((event, index) => (
          <article
            key={event.id}
            className="overflow-hidden rounded-[1.75rem] border border-white/70 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.92))] shadow-[0_18px_60px_rgba(15,23,42,0.10)] ring-1 ring-slate-900/5"
          >
            <div className="border-b border-slate-200/70 bg-[linear-gradient(90deg,rgba(15,23,42,0.03),rgba(14,165,233,0.08),rgba(251,191,36,0.06))] px-5 py-4 sm:px-6">
              <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="mb-3 flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center rounded-full border border-slate-200 bg-white/85 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-500">
                      Event {index + 1}
                    </span>
                    <span
                      className={`inline-flex max-w-full items-center rounded-full border px-3 py-1 text-center text-xs font-semibold whitespace-normal break-words ${categoryStyles[event.category || "other"]}`}
                    >
                      {categoryLabel(event.category)}
                    </span>
                    <span
                      className={`inline-flex max-w-full items-center rounded-full border px-3 py-1 text-center text-xs font-semibold whitespace-normal break-words ${confidenceStyle(
                        event.confidence
                      )}`}
                    >
                      {confidenceLabel(event.confidence)}{" "}
                      {Math.round(event.confidence * 100)}%
                    </span>
                  </div>

                  <p className="overflow-hidden break-words text-xl font-bold tracking-tight text-slate-950">
                    {event.title}
                  </p>

                  {event.sourceSnippet && (
                    <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200/80 bg-white/80 px-4 py-3 text-sm leading-6 text-slate-600 break-words">
                      <span className="mr-2 font-semibold text-slate-950">
                        From syllabus:
                      </span>
                      {event.sourceSnippet}
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 xl:min-w-[300px] xl:grid-cols-1">
                  <div className="min-w-0 rounded-2xl border border-white/80 bg-white/80 px-4 py-3 shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                      Date
                    </p>
                    <p className="mt-1 break-words text-sm font-semibold text-slate-900">
                      {event.date || "Not set"}
                    </p>
                  </div>

                  <div className="min-w-0 rounded-2xl border border-white/80 bg-white/80 px-4 py-3 shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                      Start
                    </p>
                    <p className="mt-1 break-words text-sm font-semibold text-slate-900">
                      {event.startTime || "TBD"}
                    </p>
                  </div>

                  <div className="min-w-0 rounded-2xl border border-white/80 bg-white/80 px-4 py-3 shadow-[0_8px_30px_rgba(15,23,42,0.06)]">
                    <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                      End
                    </p>
                    <p className="mt-1 break-words text-sm font-semibold text-slate-900">
                      {event.endTime || "TBD"}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <div className="px-5 py-5 sm:px-6 sm:py-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
                <div className="min-w-0 md:col-span-2 xl:col-span-2">
                  <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                    Title
                  </label>
                  <textarea
                    value={event.title}
                    onChange={(e) => updateField(event.id, "title", e.target.value)}
                    className={textAreaClassName}
                  />
                </div>

                <div className="min-w-0">
                  <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                    Date
                  </label>
                  <input
                    type="date"
                    value={event.date}
                    onChange={(e) => updateField(event.id, "date", e.target.value)}
                    className={fieldClassName}
                  />
                </div>

                <div className="min-w-0">
                  <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                    Start
                  </label>
                  <input
                    type="time"
                    value={event.startTime || ""}
                    onChange={(e) =>
                      updateField(event.id, "startTime", e.target.value || undefined)
                    }
                    className={fieldClassName}
                  />
                </div>

                <div className="min-w-0">
                  <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                    End
                  </label>
                  <input
                    type="time"
                    value={event.endTime || ""}
                    onChange={(e) =>
                      updateField(event.id, "endTime", e.target.value || undefined)
                    }
                    className={fieldClassName}
                  />
                </div>

                <div className="min-w-0 md:col-span-2 xl:col-span-2">
                  <label className="mb-2 block text-[11px] font-semibold uppercase tracking-[0.24em] text-slate-500">
                    Category
                  </label>
                  <select
                    value={event.category || "other"}
                    onChange={(e) =>
                      updateField(
                        event.id,
                        "category",
                        e.target.value as ParsedEvent["category"]
                      )
                    }
                    className={`${fieldClassName} cursor-pointer font-semibold ${categoryStyles[
                      event.category || "other"
                    ]}`}
                  >
                    <option value="assignment">Assignment</option>
                    <option value="exam">Exam</option>
                    <option value="project">Project</option>
                    <option value="quiz">Quiz</option>
                    <option value="lab">Lab</option>
                    <option value="holiday">Holiday</option>
                    <option value="other">Other</option>
                  </select>
                </div>
              </div>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
