import { BrowserRouter, Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { useEffect, useRef, useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import MainContent from './components/MainContent';
import ResultsPage from './components/ResultsPage';
import AboutPage from './components/AboutPage';
import LoadingPage from './components/LoadingPage';
import { analyzePolicy, type PPSummary } from './api';

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden font-sans">
      <Navbar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 bg-[var(--bg)] overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

// ─── Mock fallback ────────────────────────────────────────────────────────────
const MOCK_RESULT: PPSummary = {
  risk_level: 2,
  session_key: 'mock-session',
  policy_fingerprint: 'mock-fingerprint',
  user_risk_count: 0,
  user_risk_average: null,
  summaries: [
    { flash: 'Data is not shared with third parties.', value: true,        user_count: 0, user_estimation: null, user_percentage: 0 },
    { flash: 'Cookies and trackers are used.',         value: false,       user_count: 0, user_estimation: null, user_percentage: 0 },
    { flash: 'Data is retained for 24 months.',        value: '24 months', user_count: 0, user_estimation: null, user_percentage: 0 },
    { flash: 'Users can request data deletion.',       value: true,        user_count: 0, user_estimation: null, user_percentage: 0 },
    { flash: 'Policy can change without notice.',      value: false,       user_count: 0, user_estimation: null, user_percentage: 0 },
  ],
  ai: [
    { question: 'Who has my data?',               response: 'Your data is shared with internal teams and select infrastructure partners only.' },
    { question: 'Can I delete my account?',        response: 'Yes. You may request full deletion within 30 days.' },
    { question: 'Is my data sold to advertisers?', response: 'No. The policy explicitly states data is never sold to advertising partners.' },
    { question: 'How long is my data kept?',       response: 'Your data is retained for 24 months after your last activity.' },
  ],
};

// ─── Loading wrapper ──────────────────────────────────────────────────────────
function LoadingWrapper() {
  const navigate = useNavigate();
  const { state } = useLocation();
  const [error, setError] = useState<string | null>(null);
  const hasRun = useRef(false);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    const run = async () => {
      try {
        const content = state?.policyText;
        let result: PPSummary;

        if (content) {
          result = await analyzePolicy(content);
        } else {
          await new Promise((r) => setTimeout(r, 2000));
          result = MOCK_RESULT;
        }

        navigate('/results', { state: { result }, replace: true });
      } catch (err: any) {
        setError(err.message ?? 'Unknown error');
      }
    };

    run();
  }, []);

  if (error) {
    return (
      <div className="h-full flex flex-col items-center justify-center gap-4">
        <p className="text-red-400 font-bold text-sm">Analysis failed</p>
        <p className="text-slate-500 text-[11px] max-w-xs text-center">{error}</p>
        <button
          onClick={() => navigate('/')}
          className="text-[var(--secondary)] text-xs font-bold hover:underline"
        >
          ← Try again
        </button>
      </div>
    );
  }

  return <LoadingPage />;
}

// ─── App ──────────────────────────────────────────────────────────────────────
function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"        element={<Layout><MainContent /></Layout>} />
        <Route path="/loading" element={<Layout><LoadingWrapper /></Layout>} />
        <Route path="/results" element={<Layout><ResultsPage /></Layout>} />
        <Route path="/about"   element={<Layout><AboutPage /></Layout>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;