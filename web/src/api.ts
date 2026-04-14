// ─── Types matching router.py exactly ────────────────────────────────────────

export interface Summaries {
  flash: string;
  value: boolean | string;
  user_count: number;
  user_estimation: boolean | null;
  user_percentage: number;
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
  user_risk_count: number;
  user_risk_average: number | null;
}

export interface FeedbackRequest {
  session_key: string;
  policy_fingerprint: string;
  question: string;
  user_value: number; // 0 = false, 1 = true
}

export interface FeedbackRiskRequest {
  session_key: string;
  policy_fingerprint: string;
  user_value: number; // 1-5 scale
}

export interface FeedbackRiskResponse {
  user_count: number;
  user_average: number | null;
}

// ─── Derived type used by the frontend ───────────────────────────────────────

export type RiskLevel = "Low" | "Medium" | "High";

export function getRiskLevel(risk_level: number): RiskLevel {
  if (risk_level <= 2) return "Low";
  if (risk_level <= 3) return "Medium";
  return "High";
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
  user_percentage: number;
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

// ─── POST /feedback/risk/ ─────────────────────────────────────────────────────

export async function submitRiskFeedback(
  req: FeedbackRiskRequest,
): Promise<FeedbackRiskResponse> {
  const response = await fetch(`${API_BASE}/feedback/risk/`, {
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
