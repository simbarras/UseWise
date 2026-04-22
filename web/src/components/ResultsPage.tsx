import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  getRiskLevel,
  submitFeedback,
  deleteFeedback,
  submitRiskFeedback,
  deleteRiskFeedback,
  submitTimeFeedback,
  deleteTimeFeedback,
  TIME_BUCKETS,
  type FeedbackResponse,
  type PPSummary,
} from "../api";

const riskConfig = {
  Low: { color: "#10b981", trackBg: "rgba(16,185,129,0.12)" },
  Medium: { color: "#f59e0b", trackBg: "rgba(245,158,11,0.12)" },
  High: { color: "#ef4444", trackBg: "rgba(239,68,68,0.12)" },
};

function SummaryRow({
  flash,
  value,
  userCount,
  userEstimation,
  userPercentage,
  userTimeBucket,
  userTimeCount,
  userTimePercentage,
  llmTimeBucket,
  sessionKey,
  policyFingerprint,
}: {
  flash: string;
  value: boolean | string;
  userCount: number;
  userEstimation: boolean | null;
  userPercentage: number;
  userTimeBucket: number | null;
  userTimeCount: number;
  userTimePercentage: number;
  llmTimeBucket: number | null;
  sessionKey: string;
  policyFingerprint: string;
}) {
  const isTimeQuestion = typeof value === "string";
  const isTrue = value === true;

  const bg = isTimeQuestion
    ? "rgba(99,102,241,0.12)"
    : isTrue
      ? "rgba(16,185,129,0.12)"
      : "rgba(239,68,68,0.12)";
  const color = isTimeQuestion ? "#6366f1" : isTrue ? "#10b981" : "#ef4444";
  const symbol = isTimeQuestion ? "…" : isTrue ? "✓" : "✕";

  // FLAG state
  const [userVote, setUserVote] = useState<boolean | null>(null);
  const [voting, setVoting] = useState(false);
  const [liveCount, setLiveCount] = useState<number>(userCount);
  const [liveEstimation, setLiveEstimation] = useState<boolean | null>(
    userEstimation,
  );
  const [livePercentage, setLivePercentage] = useState<number>(userPercentage);

  // TIME state
  const [selectedBucket, setSelectedBucket] = useState<number | null>(null);
  const [timeVoting, setTimeVoting] = useState(false);
  const [liveTimeBucket, setLiveTimeBucket] = useState<number | null>(userTimeBucket);
  const [liveTimeCount, setLiveTimeCount] = useState<number>(userTimeCount);
  const [liveTimePercentage, setLiveTimePercentage] = useState<number>(userTimePercentage);

  const [expanded, setExpanded] = useState(false);

  const handleVote = async (vote: boolean) => {
    if (voting) return;
    setVoting(true);
    const isDeselect = userVote === vote;
    setUserVote(isDeselect ? null : vote);
    try {
      const result: FeedbackResponse = isDeselect
        ? await deleteFeedback({
            session_key: sessionKey,
            policy_fingerprint: policyFingerprint,
            question: flash,
          })
        : await submitFeedback({
            session_key: sessionKey,
            policy_fingerprint: policyFingerprint,
            question: flash,
            user_value: vote ? 1 : 0,
          });
      setLiveCount(result.user_count);
      setLiveEstimation(result.user_estimation);
      setLivePercentage(result.user_percentage);
    } catch {
      setUserVote(isDeselect ? vote : null);
    } finally {
      setVoting(false);
    }
  };

  const handleTimeBucket = async (bucketIndex: number) => {
    if (timeVoting) return;
    setTimeVoting(true);
    const isDeselect = selectedBucket === bucketIndex;
    setSelectedBucket(isDeselect ? null : bucketIndex);
    try {
      const result = isDeselect
        ? await deleteTimeFeedback({
            session_key: sessionKey,
            policy_fingerprint: policyFingerprint,
            question: flash,
          })
        : await submitTimeFeedback({
            session_key: sessionKey,
            policy_fingerprint: policyFingerprint,
            question: flash,
            user_value: bucketIndex,
          });
      setLiveTimeBucket(result.user_time_bucket);
      setLiveTimeCount(result.user_count);
      setLiveTimePercentage(result.user_time_percentage);
    } catch {
      setSelectedBucket(isDeselect ? bucketIndex : null);
    } finally {
      setTimeVoting(false);
    }
  };

  const hasFlagDivergence =
    !isTimeQuestion &&
    liveCount > 0 &&
    liveEstimation !== null &&
    liveEstimation !== value;

  const hasTimeDivergence =
    isTimeQuestion &&
    liveTimeCount > 0 &&
    liveTimeBucket !== null &&
    llmTimeBucket !== null &&
    liveTimeBucket !== llmTimeBucket;

  return (
    <div className="flex flex-col py-3 border-b border-slate-100 last:border-0 gap-1.5">
      {/* Primary row */}
      <div
        className="flex items-center gap-3 cursor-pointer select-none"
        onClick={() => setExpanded((e) => !e)}
      >
        <span
          className="shrink-0 rounded-full flex items-center justify-center font-bold"
          style={{
            background: bg,
            color,
            minWidth: isTimeQuestion ? "auto" : "1.25rem",
            height: isTimeQuestion ? "auto" : "1.25rem",
            fontSize: "10px",
            padding: isTimeQuestion ? "2px 6px" : undefined,
            borderRadius: isTimeQuestion ? "9999px" : undefined,
            whiteSpace: "nowrap",
          }}
        >
          {isTimeQuestion
            ? llmTimeBucket !== null
              ? TIME_BUCKETS[llmTimeBucket]
              : (value as string)
            : symbol}
        </span>
        <span className="text-[11px] text-slate-500 leading-relaxed flex-1">
          {flash}
        </span>
        {(hasFlagDivergence || hasTimeDivergence) && (
          <span
            className="shrink-0 text-[11px] text-amber-500 cursor-help"
            title="Response differs from the majority of user feedback"
          >
            ⚠
          </span>
        )}
        <span className="shrink-0 text-base text-slate-400 leading-none">
          {expanded ? "▴" : "▾"}
        </span>
      </div>

      {/* Expanded: FLAG question */}
      {!isTimeQuestion && expanded && (
        <div className="flex flex-col gap-1 pl-8 text-[10px] text-slate-500">
          {liveCount > 0 && liveEstimation !== null ? (
            <span>
              {livePercentage}% of the {liveCount}{" "}
              {liveCount === 1 ? "user" : "users"} vote:{" "}
              <strong>{liveEstimation ? "yes" : "no"}</strong>
            </span>
          ) : (
            <span className="italic text-slate-400">
              No community votes yet
            </span>
          )}
          <div className="flex items-center gap-2">
            <span>Add your vote:</span>
            <button
              onClick={() => handleVote(true)}
              disabled={voting}
              className="px-2.5 py-0.5 rounded-full border transition-all disabled:opacity-50"
              style={{
                borderColor: userVote === true ? "#10b981" : "#e2e8f0",
                color: userVote === true ? "#10b981" : "#94a3b8",
                fontWeight: userVote === true ? "bold" : "normal",
                background:
                  userVote === true ? "rgba(16,185,129,0.08)" : "transparent",
              }}
            >
              yes
            </button>
            <button
              onClick={() => handleVote(false)}
              disabled={voting}
              className="px-2.5 py-0.5 rounded-full border transition-all disabled:opacity-50"
              style={{
                borderColor: userVote === false ? "#ef4444" : "#e2e8f0",
                color: userVote === false ? "#ef4444" : "#94a3b8",
                fontWeight: userVote === false ? "bold" : "normal",
                background:
                  userVote === false ? "rgba(239,68,68,0.08)" : "transparent",
              }}
            >
              no
            </button>
          </div>
        </div>
      )}

      {/* Expanded: TIME question */}
      {isTimeQuestion && expanded && (
        <div className="flex flex-col gap-2 pl-8 text-[10px] text-slate-500">
          {liveTimeCount > 0 && liveTimeBucket !== null ? (
            <span>
              {liveTimePercentage}% of the {liveTimeCount}{" "}
              {liveTimeCount === 1 ? "user" : "users"} vote:{" "}
              <strong className="text-indigo-600">
                {TIME_BUCKETS[liveTimeBucket]}
              </strong>
            </span>
          ) : (
            <span className="italic text-slate-400">
              No community votes yet
            </span>
          )}
          <span className="text-slate-400">
            How long do you think data is kept?
          </span>
          <div className="flex flex-wrap gap-1.5">
            {TIME_BUCKETS.map((label, i) => {
              const isSelected = selectedBucket === i;
              return (
                <button
                  key={i}
                  onClick={() => handleTimeBucket(i)}
                  disabled={timeVoting}
                  className="px-2 py-0.5 rounded-full border text-[10px] transition-all disabled:opacity-50"
                  style={{
                    borderColor: isSelected ? "#6366f1" : "#e2e8f0",
                    color: isSelected ? "#6366f1" : "#94a3b8",
                    fontWeight: isSelected ? "bold" : "normal",
                    background: isSelected ? "rgba(99,102,241,0.1)" : "transparent",
                  }}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

export default function ResultsPage() {
  const navigate = useNavigate();
  const { state } = useLocation();

  const policyText: string | null = state?.policyText ?? null;

  const data: PPSummary = state?.result ?? {
    risk_level: 1,
    summaries: [],
    ai: [],
    session_key: "",
    policy_fingerprint: "",
  };

  const [showPolicy, setShowPolicy] = useState(false);

  // Risk feedback state
  const [riskExpanded, setRiskExpanded] = useState(false);
  const [riskSlider, setRiskSlider] = useState(0); // 0 = no vote
  const [riskVoting, setRiskVoting] = useState(false);
  const [liveRiskCount, setLiveRiskCount] = useState(data.user_risk_count);
  const [liveRiskAverage, setLiveRiskAverage] = useState<number | null>(
    data.user_risk_average,
  );

  // LLM risk is already on 1-5 scale
  const llmRisk = data.risk_level;
  // Combined display value (average of LLM 1-5 and user average 1-5)
  const combinedRisk =
    liveRiskAverage !== null ? (llmRisk + liveRiskAverage) / 2 : llmRisk;
  const riskLabel = getRiskLevel(combinedRisk);
  const risk = riskConfig[getRiskLevel(combinedRisk)];
  // Convert a 1-5 value to a 0-100% bar position
  const toBarPct = (v: number) => Math.round(((v - 1) / 4) * 100);

  const handleRiskFeedback = async (value: number) => {
    if (riskVoting) return;
    setRiskVoting(true);
    try {
      const result =
        value === 0
          ? await deleteRiskFeedback({
              session_key: data.session_key,
              policy_fingerprint: data.policy_fingerprint,
            })
          : await submitRiskFeedback({
              session_key: data.session_key,
              policy_fingerprint: data.policy_fingerprint,
              user_value: value,
            });
      setLiveRiskCount(result.user_count);
      setLiveRiskAverage(result.user_average);
    } finally {
      setRiskVoting(false);
    }
  };

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
    <div className="h-full w-full flex items-start justify-center bg-[var(--bg)] px-10 py-8 overflow-y-auto">
      {/* Policy modal */}
      {showPolicy && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          onClick={() => setShowPolicy(false)}
        >
          <div
            className="bg-white rounded-2xl shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <p className="text-sm font-bold text-slate-800">Original Policy</p>
              <button
                onClick={() => setShowPolicy(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors text-lg leading-none"
              >
                ✕
              </button>
            </div>
            <div className="overflow-y-auto px-6 py-4">
              {policyText ? (
                <pre className="text-[10px] text-slate-600 leading-relaxed whitespace-pre-wrap font-sans">
                  {policyText}
                </pre>
              ) : (
                <p className="text-[11px] text-slate-400 italic text-center py-8">
                  No policy text available.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

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
          {policyText && (
            <button
              onClick={() => setShowPolicy(true)}
              className="border border-[var(--secondary)]/50 text-[var(--secondary)] text-[9px] font-bold uppercase tracking-[1px] px-4 py-2 rounded hover:bg-[var(--secondary)] hover:text-white transition-all"
            >
              View Policy
            </button>
          )}
        </div>

        {/* Two panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
          {/* LEFT: Flash Summary */}
          <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-7 flex flex-col">
            <p className="text-base font-bold text-slate-800 mb-2">
              Flash Summary
            </p>
            <div className="flex-1">
              {data.summaries.map((s, i) => (
                <SummaryRow
                  key={i}
                  flash={s.flash}
                  value={s.value}
                  userCount={s.user_count}
                  userEstimation={s.user_estimation}
                  userPercentage={s.user_percentage}
                  userTimeBucket={s.user_time_bucket}
                  userTimeCount={s.user_time_count}
                  userTimePercentage={s.user_time_percentage}
                  llmTimeBucket={s.llm_time_bucket}
                  sessionKey={data.session_key}
                  policyFingerprint={data.policy_fingerprint}
                />
              ))}
            </div>

            {/* Risk bar */}
            <div className="mt-6">
              {/* Header row — clickable to expand */}
              <div
                className="flex items-center gap-2 mb-2 cursor-pointer select-none"
                onClick={() => setRiskExpanded((e) => !e)}
              >
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
                  ({combinedRisk.toFixed(1)}/5)
                </span>
                <span className="ml-auto text-base text-slate-400 leading-none">
                  {riskExpanded ? "▴" : "▾"}
                </span>
              </div>

              {/* Bar with LLM + user markers */}
              <div
                className="relative w-full h-3 rounded-full"
                style={{ background: risk.trackBg }}
              >
                {/* Filled portion to combined value */}
                <div
                  className="absolute inset-y-0 left-0 rounded-full transition-all duration-700"
                  style={{
                    width: `${toBarPct(combinedRisk)}%`,
                    background: risk.color,
                  }}
                />
                {/* LLM marker (vertical tick) */}
                <div
                  className="absolute top-1/2 w-[3px] h-5 rounded-sm opacity-70"
                  style={{
                    left: `${toBarPct(llmRisk)}%`,
                    transform: "translate(-50%, -50%)",
                    background: risk.color,
                  }}
                  title={`LLM estimate: ${llmRisk.toFixed(1)}/5`}
                />
                {/* User marker (vertical tick, indigo) */}
                {liveRiskAverage !== null && (
                  <div
                    className="absolute top-1/2 w-[3px] h-5 rounded-sm opacity-80"
                    style={{
                      left: `${toBarPct(liveRiskAverage)}%`,
                      transform: "translate(-50%, -50%)",
                      background: "#6366f1",
                    }}
                    title={`User average: ${liveRiskAverage.toFixed(1)}/5`}
                  />
                )}
              </div>

              <div className="flex justify-between mt-1">
                <span className="text-[8px] text-slate-400">Safe (1)</span>
                <span className="text-[8px] text-slate-400">Dangerous (5)</span>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-3 mt-1">
                <div className="flex items-center gap-1">
                  <div
                    className="w-2 h-3 rounded-sm opacity-70"
                    style={{ background: risk.color }}
                  />
                  <span className="text-[8px] text-slate-400">LLM</span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="w-2 h-3 rounded-sm bg-indigo-400 opacity-80" />
                  <span className="text-[8px] text-slate-400">Users</span>
                </div>
                <div className="flex items-center gap-1">
                  <div
                    className="w-4 h-2 rounded-full opacity-80"
                    style={{ background: risk.color }}
                  />
                  <span className="text-[8px] text-slate-400">Combined</span>
                </div>
              </div>

              {/* Expanded: slider */}
              {riskExpanded && (
                <div className="mt-3 flex flex-col gap-1.5 pl-1">
                  <span className="text-[10px] text-slate-500">
                    Your risk rating:{" "}
                    {riskSlider === 0 ? (
                      <strong className="text-slate-400">No vote</strong>
                    ) : (
                      <strong className="text-slate-700">{riskSlider}/5</strong>
                    )}
                    {liveRiskCount > 0 && (
                      <span className="text-slate-400 font-normal ml-2">
                        · {liveRiskCount}{" "}
                        {liveRiskCount === 1 ? "user" : "users"} voted
                      </span>
                    )}
                    {riskVoting && (
                      <span className="text-slate-400 font-normal ml-2 italic">
                        saving…
                      </span>
                    )}
                  </span>

                  {/* Custom white-track slider */}
                  <div className="relative h-5 flex items-center">
                    {/* Track */}
                    <div className="relative w-full h-2 rounded-full bg-white border border-slate-200">
                      {/* Fill — only shown when value > 0 */}
                      {riskSlider > 0 && (
                        <div
                          className="absolute inset-y-0 left-0 rounded-full transition-all"
                          style={{
                            width: `${(riskSlider / 5) * 100}%`,
                            background: "var(--secondary)",
                          }}
                        />
                      )}
                      {/* Thumb */}
                      <div
                        className="absolute top-1/2 w-4 h-4 rounded-full border-2 border-white shadow-md -translate-y-1/2 -translate-x-1/2 transition-all pointer-events-none"
                        style={{
                          left: `${(riskSlider / 5) * 100}%`,
                          background:
                            riskSlider === 0
                              ? "#cbd5e1"
                              : "var(--secondary)",
                        }}
                      />
                    </div>
                    {/* Invisible native input for interaction */}
                    <input
                      type="range"
                      min={0}
                      max={5}
                      step={1}
                      value={riskSlider}
                      onChange={(e) => setRiskSlider(Number(e.target.value))}
                      onMouseUp={(e) =>
                        handleRiskFeedback(
                          Number((e.target as HTMLInputElement).value),
                        )
                      }
                      onTouchEnd={(e) =>
                        handleRiskFeedback(
                          Number((e.target as HTMLInputElement).value),
                        )
                      }
                      className="absolute inset-0 w-full opacity-0 cursor-pointer"
                      style={{ margin: 0 }}
                    />
                  </div>

                  <div className="flex justify-between text-[8px] text-slate-400 px-0.5">
                    {["–", 1, 2, 3, 4, 5].map((n) => (
                      <span key={n}>{n}</span>
                    ))}
                  </div>
                </div>
              )}
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
