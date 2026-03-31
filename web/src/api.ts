// ─── Types matching router.py exactly ────────────────────────────────────────

export interface Summaries {
  flash: string;
  value: boolean | string;
  user_count: number;
  user_estimation: boolean | null;
}

export interface AiQuestion {
  question: string;
  response: string;
}

export interface PPSummary {
  risk_level: number;
  summaries: Summaries[];
  ai: AiQuestion[];
  session_key: string;
  policy_fingerprint: string;
}

export interface FeedbackRequest {
  session_key: string;
  policy_fingerprint: string;
  question: string;
  user_value: number; // 0 = false, 1 = true
}

// ─── Derived type used by the frontend ───────────────────────────────────────

export type RiskLevel = "Low" | "Medium" | "High";

export function getRiskLevel(risk_level: number): RiskLevel {
  if (risk_level <= 3) return "Low";
  if (risk_level <= 6) return "Medium";
  return "High";
}

export function getRiskScore(risk_level: number): number {
  // Convert 1-10 scale to 0-100 for the progress bar
  return Math.round((risk_level / 10) * 100);
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

// ─── POST /feedback/ ─────────────────────────────────────────────────────────

export interface FeedbackResponse {
  user_count: number;
  user_estimation: boolean | null;
}

export async function submitFeedback(
  req: FeedbackRequest,
): Promise<FeedbackResponse> {
  const response = await fetch(`${API_BASE}/feedback/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error?.detail ?? `Server error: ${response.status}`);
  }

  return response.json();
}
