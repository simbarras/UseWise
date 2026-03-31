import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { getRiskLevel, getRiskScore, type PPSummary } from "../api";
import { exportToPdf } from "../exportPdf";

const riskConfig = {
  Low: { color: "#10b981", trackBg: "rgba(16,185,129,0.12)" },
  Medium: { color: "#f59e0b", trackBg: "rgba(245,158,11,0.12)" },
  High: { color: "#ef4444", trackBg: "rgba(239,68,68,0.12)" },
};

function SummaryRow({
  flash,
  value,
}: {
  flash: string;
  value: boolean | string;
}) {
  const isString = typeof value === "string";
  const isTrue = value === true;

  const bg = isString
    ? "rgba(99,102,241,0.12)"
    : isTrue
      ? "rgba(16,185,129,0.12)"
      : "rgba(239,68,68,0.12)";
  const color = isString ? "#6366f1" : isTrue ? "#10b981" : "#ef4444";
  const symbol = isString ? "…" : isTrue ? "✓" : "✕";

  return (
    <div className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0">
      <span
        className="shrink-0 mt-0.5 rounded-full flex items-center justify-center font-bold"
        style={{
          background: bg,
          color,
          minWidth: isString ? "auto" : "1.25rem",
          height: isString ? "auto" : "1.25rem",
          fontSize: isString ? "10px" : "10px",
          padding: isString ? "2px 6px" : undefined,
          borderRadius: isString ? "9999px" : undefined,
          whiteSpace: "nowrap",
        }}
      >
        {isString ? value : symbol}
      </span>
      <span className="text-[11px] text-slate-500 leading-relaxed">
        {flash}
      </span>
    </div>
  );
}

export default function ResultsPage() {
  const navigate = useNavigate();
  const { state } = useLocation();

  const data: PPSummary = state?.result ?? {
    risk_level: 1,
    summaries: [],
    ai: [],
  };

  const riskLabel = getRiskLevel(data.risk_level);
  const riskScore = getRiskScore(data.risk_level);
  const risk = riskConfig[riskLabel];

  const [messages, setMessages] = useState<
    { from: "user" | "ai"; text: string }[]
  >([]);
  const [hasAsked, setHasAsked] = useState(false);

  const askQuestion = (question: string) => {
    const match = data.ai.find(
      (a) => a.question.toLowerCase() === question.toLowerCase(),
    );
    const answer =
      match?.response ??
      "I don't have a specific answer for that in this policy.";
    setMessages((prev) => [
      ...prev,
      { from: "user", text: question },
      { from: "ai", text: answer },
    ]);
    setHasAsked(true);
  };

  const suggestedQuestions = data.ai.map((a) => a.question);

  return (
    <div className="h-full w-full flex items-center justify-center bg-[var(--bg)] px-10 py-8">
      <div className="w-full max-w-5xl flex flex-col gap-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => navigate("/")}
              className="text-[9px] font-bold text-slate-500 uppercase tracking-[2px] hover:text-[var(--secondary)] transition-colors flex items-center gap-1 mb-1"
            >
              ← New Analysis
            </button>
            <h2 className="text-xl font-serif text-[var(--text)]">Results</h2>
          </div>
          <button
            onClick={() => exportToPdf(data, messages)}
            className="border border-[var(--secondary)]/50 text-[var(--secondary)] text-[9px] font-bold uppercase tracking-[1px] px-4 py-2 rounded hover:bg-[var(--secondary)] hover:text-white transition-all"
          >
            Export PDF
          </button>
        </div>

        {/* Two panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LEFT: Flash Summary */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-7 flex flex-col">
            <p className="text-base font-bold text-slate-800 mb-2">
              Flash Summary
            </p>
            <div className="flex-1">
              {data.summaries.map((s, i) => (
                <SummaryRow key={i} {...s} />
              ))}
            </div>

            {/* Risk bar */}
            <div className="mt-6">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-[11px] font-bold text-slate-700">
                  Risk Level:
                </span>
                <span
                  className="text-[11px] font-bold"
                  style={{ color: risk.color }}
                >
                  {riskLabel}
                </span>
                <span className="text-[10px] text-slate-400 ml-1">
                  ({data.risk_level}/10)
                </span>
              </div>
              <div
                className="w-full h-2 rounded-full overflow-hidden"
                style={{ background: risk.trackBg }}
              >
                <div
                  className="h-full rounded-full transition-all duration-1000"
                  style={{ width: `${riskScore}%`, background: risk.color }}
                />
              </div>
              <div className="flex justify-between mt-1">
                <span className="text-[8px] text-slate-400">Safe</span>
                <span className="text-[8px] text-slate-400">Dangerous</span>
              </div>
            </div>
          </div>

          {/* RIGHT: AI Assistant */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-7 flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                style={{ background: "var(--secondary)" }}
              >
                <span className="text-white text-sm font-bold">AI</span>
              </div>
              <div>
                <p className="text-sm font-bold text-slate-800">
                  Policy Assistant
                </p>
                <p className="text-[10px] text-slate-400">
                  Based on the policy, what would you like to know?
                </p>
              </div>
            </div>

            <div className="flex-1 max-h-[200px] overflow-y-auto flex flex-col gap-3 pr-1">
              {messages.length === 0 ? (
                <p className="text-[11px] text-slate-400 text-center mt-4">
                  Select a question below or type your own.
                </p>
              ) : (
                messages.map((m, i) => (
                  <div
                    key={i}
                    className={`flex ${m.from === "user" ? "justify-end" : "justify-start"}`}
                  >
                    <div
                      className={`max-w-[82%] rounded-xl px-3 py-2 text-[10px] leading-relaxed ${m.from === "user" ? "text-white rounded-br-sm" : "bg-slate-100 text-slate-700 rounded-bl-sm"}`}
                      style={
                        m.from === "user"
                          ? { background: "var(--secondary)" }
                          : {}
                      }
                    >
                      {m.text}
                    </div>
                  </div>
                ))
              )}
            </div>

            {!hasAsked && suggestedQuestions.length > 0 && (
              <div className="flex flex-col gap-2">
                {suggestedQuestions.map((q) => (
                  <button
                    key={q}
                    onClick={() => askQuestion(q)}
                    className="w-full text-left text-[11px] font-semibold text-white hover:brightness-110 active:scale-[0.98] transition-all px-4 py-2.5 rounded-lg"
                    style={{ background: "var(--secondary)" }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            )}

            {hasAsked && (
              <button
                onClick={() => {
                  setMessages([]);
                  setHasAsked(false);
                }}
                className="text-[9px] text-slate-400 hover:text-slate-600 transition-colors text-center"
              >
                ↺ Ask another question
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
