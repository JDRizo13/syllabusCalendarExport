"use client";

import { useState } from "react";
import ReviewTable from "@/components/ReviewTable";
import { ParsedEvent } from "@/lib/types";

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [events, setEvents] = useState<ParsedEvent[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;

    setError(null);
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("http://127.0.0.1:8000/upload-syllabus", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to parse syllabus.");
      }

      const data = await response.json();
      setEvents(data.events || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/export-ics", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events }),
      });

      if (!response.ok) {
        throw new Error("Failed to export ICS file.");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "syllabus-events.ics";
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <main className="min-h-screen overflow-x-hidden bg-[radial-gradient(circle_at_top_left,rgba(125,211,252,0.32),transparent_28%),radial-gradient(circle_at_top_right,rgba(253,224,71,0.24),transparent_24%),linear-gradient(180deg,#f8fbff_0%,#eef4ff_46%,#f8fafc_100%)] px-4 py-8 sm:px-6 sm:py-12">
      <div className="mx-auto max-w-6xl">
        <section className="relative overflow-hidden rounded-[2rem] border border-white/70 bg-[linear-gradient(135deg,rgba(255,255,255,0.96),rgba(236,245,255,0.9))] px-6 py-8 shadow-[0_28px_90px_rgba(15,23,42,0.16)] ring-1 ring-slate-900/5 sm:px-8 sm:py-10">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(14,165,233,0.18),transparent_26%),radial-gradient(circle_at_85%_12%,rgba(245,158,11,0.18),transparent_20%),linear-gradient(120deg,transparent_0%,rgba(255,255,255,0.45)_45%,transparent_100%)]" />

          <div className="relative grid gap-8 lg:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.95fr)] lg:items-end">
            <div className="min-w-0">
              <div className="inline-flex items-center rounded-full border border-slate-200 bg-white/85 px-4 py-1.5 text-[11px] font-semibold uppercase tracking-[0.26em] text-slate-500 shadow-[0_10px_30px_rgba(15,23,42,0.08)]">
                Syllabus to calendar
              </div>

              <h1 className="mt-5 max-w-3xl text-4xl font-black tracking-tight text-slate-950 sm:text-5xl">
                Turn a messy syllabus into a calendar that looks deliberate.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600 sm:text-lg">
                Upload the PDF, review the extracted events, and export a clean
                `.ics` file that feels polished instead of machine-made.
              </p>

              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border border-white/80 bg-white/78 px-4 py-4 shadow-[0_12px_36px_rgba(15,23,42,0.08)]">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                    Upload
                  </p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    Bring in the syllabus PDF
                  </p>
                </div>
                <div className="rounded-2xl border border-white/80 bg-white/78 px-4 py-4 shadow-[0_12px_36px_rgba(15,23,42,0.08)]">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                    Review
                  </p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    Refine every extracted event
                  </p>
                </div>
                <div className="rounded-2xl border border-white/80 bg-white/78 px-4 py-4 shadow-[0_12px_36px_rgba(15,23,42,0.08)]">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.22em] text-slate-400">
                    Export
                  </p>
                  <p className="mt-2 text-sm font-semibold text-slate-900">
                    Download an Apple-friendly `.ics`
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-[1.75rem] border border-white/15 bg-slate-950 px-5 py-5 text-white shadow-[0_24px_70px_rgba(15,23,42,0.28)]">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-sky-200/80">
                Workspace
              </p>
              <h2 className="mt-3 text-2xl font-bold tracking-tight">
                Review with less cleanup later.
              </h2>
              <p className="mt-3 text-sm leading-6 text-slate-300">
                The better this pass is, the more trustworthy the final
                calendar feels. You can edit every extracted field before
                export.
              </p>

              <div className="mt-6 space-y-3">
                <input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full min-w-0 cursor-pointer rounded-2xl border border-white/15 bg-white/8 px-4 py-3 text-sm text-slate-200 file:mr-4 file:rounded-xl file:border-0 file:bg-white file:px-4 file:py-2 file:text-sm file:font-semibold file:text-slate-950 hover:border-sky-300/40 focus:outline-none"
                />
                <button
                  onClick={handleUpload}
                  disabled={!file || isUploading}
                  className="inline-flex h-12 w-full items-center justify-center rounded-2xl bg-[linear-gradient(135deg,#38bdf8,#0f172a)] px-5 text-sm font-semibold text-white shadow-[0_18px_45px_rgba(56,189,248,0.28)] transition hover:-translate-y-0.5 hover:shadow-[0_22px_55px_rgba(56,189,248,0.34)] disabled:translate-y-0 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isUploading ? "Uploading..." : "Upload syllabus"}
                </button>
              </div>

              {file && (
                <p className="mt-4 break-words text-sm text-slate-300">
                  Selected file:{" "}
                  <span className="font-semibold text-white">{file.name}</span>
                </p>
              )}

              {error && (
                <p className="mt-4 rounded-2xl border border-rose-400/25 bg-rose-400/10 px-4 py-3 text-sm text-rose-100">
                  {error}
                </p>
              )}
            </div>
          </div>
        </section>

        <ReviewTable
          events={events}
          setEvents={setEvents}
          onExport={handleExport}
          isExporting={isExporting}
        />
      </div>
    </main>
  );
}
