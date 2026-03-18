// ─── Types matching router.py exactly ────────────────────────────────────────

export interface Summaries {
  flash: string;
  present: boolean;
}

export interface AiQuestion {
  question: string;
  response: string;
}

export interface PPSummary {
  risk_level: number; // 1-5 scale from backend
  summaries: Summaries[];
  ai: AiQuestion[];
}

// ─── Derived type used by the frontend ───────────────────────────────────────

export type RiskLevel = "Low" | "Medium" | "High";

export function getRiskLevel(risk_level: number): RiskLevel {
  if (risk_level <= 2) return "Low";
  if (risk_level <= 3) return "Medium";
  return "High";
}

export function getRiskScore(risk_level: number): number {
  // Convert 1-5 scale to 0-100 for the progress bar
  return Math.round((risk_level / 5) * 100);
}

// ─── Config ───────────────────────────────────────────────────────────────────

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// ─── POST /summary/ ───────────────────────────────────────────────────────────

export async function analyzePolicy(content: string): Promise<PPSummary> {
  const body = { content: content };
  const response = await fetch(`${API_BASE}/summary/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  console.log("API response:", response);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error?.detail ?? `Server error: ${response.status}`);
  }

  return response.json();
}
