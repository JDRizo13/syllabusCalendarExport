export type ParsedEvent = {
  id: string;
  title: string;
  date: string;
  startTime?: string;
  endTime?: string;
  category?: "exam" | "assignment" | "project" | "quiz" | "lab" | "holiday" | "other";
  confidence: number;
  sourceSnippet?: string;
  notes?: string;
};