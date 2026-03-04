import { useNavigate } from 'react-router-dom';

const GOALS = [
  {
    icon: '🔍',
    title: 'Instant Clarity',
    description:
      'Privacy policies average 4,000 words and take 20+ minutes to read. UseWise distills them into a 30-second flash summary anyone can understand.',
  },
  {
    icon: '⚖️',
    title: 'GDPR Alignment',
    description:
      'We cross-reference every policy against key GDPR articles to flag non-compliant clauses and highlight your rights as a data subject.',
  },
  {
    icon: '🤖',
    title: 'AI-Powered Analysis',
    description:
      'Our engine uses large language models to detect data sharing, retention periods, third-party involvement, and opt-out mechanisms automatically.',
  },
  {
    icon: '🛡️',
    title: 'Privacy for Everyone',
    description:
      'No legal background required. UseWise is built for everyday users who deserve to know what they agree to before clicking "Accept".',
  },
];

const TEAM = [
  { name: 'Member 1', role: 'AI & Backend' },
  { name: 'Member 2', role: 'Frontend & UX' },
  { name: 'Member 3', role: 'Legal & GDPR Research' },
];

export default function AboutPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-full bg-[var(--bg)] px-10 py-8">
      <div className="max-w-4xl mx-auto flex flex-col gap-10">

        {/* ── Header ── */}
        <div>
          <button
            onClick={() => navigate('/')}
            className="text-[9px] font-bold text-slate-500 uppercase tracking-[2px] hover:text-[var(--secondary)] transition-colors flex items-center gap-1 mb-3"
          >
            ← Back
          </button>
          <h1 className="text-4xl font-serif text-[var(--text)] leading-tight">
            About <span className="text-[var(--secondary)] italic">UseWise</span>
          </h1>
          <p className="text-slate-500 text-sm mt-3 max-w-xl leading-relaxed">
            A student project built to make digital privacy accessible — because understanding
            what you sign up for shouldn't require a law degree.
          </p>
        </div>

        {/* ── Goals grid ── */}
        <div>
          <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[2px] mb-5">
            Our Goals
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {GOALS.map((g) => (
              <div
                key={g.title}
                className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 flex flex-col gap-3 hover:-translate-y-0.5 hover:shadow-md transition-all duration-200"
              >
                <span className="text-2xl">{g.icon}</span>
                <h3 className="text-sm font-bold text-slate-800">{g.title}</h3>
                <p className="text-[11px] text-slate-500 leading-relaxed">{g.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* ── Report download ── */}
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-7 flex items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-[var(--secondary)]/10 flex items-center justify-center shrink-0">
              <span className="text-2xl">📄</span>
            </div>
            <div>
              <p className="text-sm font-bold text-slate-800">Project Report</p>
              <p className="text-[10px] text-slate-400 mt-0.5">
                Full research report — methodology, analysis & conclusions
              </p>
              <p className="text-[9px] text-slate-300 mt-1 italic">PDF · Available soon</p>
            </div>
          </div>
          <button
            disabled
            className="shrink-0 flex items-center gap-2 border-2 border-dashed border-slate-200 text-slate-300 text-[10px] font-bold uppercase tracking-[1px] px-5 py-2.5 rounded-xl cursor-not-allowed"
          >
            <span>⬇</span> Download
          </button>
        </div>

        {/* ── Team ── */}
        <div>
          <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[2px] mb-5">
            The Team
          </p>
          <div className="flex gap-4 flex-wrap">
            {TEAM.map((m) => (
              <div
                key={m.name}
                className="bg-white rounded-xl border border-slate-100 shadow-sm px-5 py-4 flex items-center gap-3"
              >
                <div className="w-8 h-8 rounded-full bg-[var(--secondary)]/15 flex items-center justify-center">
                  <span className="text-[var(--secondary)] text-xs font-bold">
                    {m.name.split(' ')[1]}
                  </span>
                </div>
                <div>
                  <p className="text-[11px] font-bold text-slate-700">{m.name}</p>
                  <p className="text-[9px] text-slate-400">{m.role}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}