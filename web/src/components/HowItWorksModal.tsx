import { useEffect } from 'react';
import { createPortal } from 'react-dom';

const STEPS = [
  {
    number: '01',
    icon: '📋',
    title: 'Paste or Drop',
    description:
      'Upload your privacy policy as a file, paste the raw text, or drop a URL. UseWise accepts any format.',
  },
  {
    number: '02',
    icon: '🤖',
    title: 'AI Analysis',
    description:
      'Our engine reads the entire document and cross-references it against GDPR articles to detect risky clauses.',
  },
  {
    number: '03',
    icon: '⚡',
    title: 'Flash Summary',
    description:
      'You get an instant breakdown — data sharing, retention, deletion rights, and a global risk score.',
  },
  {
    number: '04',
    icon: '💬',
    title: 'Ask Questions',
    description:
      'Not sure about something? Ask the Policy Assistant directly and get plain-English answers in seconds.',
  },
];

interface Props {
  onClose: () => void;
}

export default function HowItWorksModal({ onClose }: Props) {
  // Prevent background scroll
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; };
  }, []);

  return createPortal(
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center px-6"
      style={{ background: 'rgba(0,0,0,0.5)', backdropFilter: 'blur(4px)' }}
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-8 flex flex-col gap-6 relative"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close — top RIGHT */}
        <button
          onClick={onClose}
          className="absolute top-4 right-5 text-slate-300 hover:text-slate-500 transition-colors text-lg leading-none"
        >
          ✕
        </button>

        {/* Header */}
        <div>
          <p className="text-[9px] font-bold text-[var(--secondary)] uppercase tracking-[2px] mb-1">
            UseWise
          </p>
          <h2 className="text-2xl font-serif text-slate-800">How it Works</h2>
          <p className="text-[11px] text-slate-400 mt-1">
            From raw legal text to clear answers — in under 30 seconds.
          </p>
        </div>

        {/* Steps */}
        <div className="flex flex-col gap-4">
          {STEPS.map((step, i) => (
            <div key={step.number} className="flex items-start gap-4">
              <div className="flex flex-col items-center shrink-0">
                <div
                  className="w-8 h-8 rounded-full flex items-center justify-center text-[10px] font-bold text-white"
                  style={{ background: 'var(--secondary)' }}
                >
                  {step.number}
                </div>
                {i < STEPS.length - 1 && (
                  <div className="w-px mt-1" style={{ height: 24, background: 'rgba(56,189,248,0.2)' }} />
                )}
              </div>
              <div className="pb-2">
                <div className="flex items-center gap-2 mb-0.5">
                  <span>{step.icon}</span>
                  <p className="text-sm font-bold text-slate-800">{step.title}</p>
                </div>
                <p className="text-[11px] text-slate-500 leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={onClose}
          className="w-full py-2.5 rounded-xl text-white text-xs font-bold uppercase tracking-[1px] hover:brightness-110 active:scale-[0.98] transition-all"
          style={{ background: 'var(--secondary)' }}
        >
          Got it — Let's Analyze
        </button>
      </div>
    </div>,
    document.body
  );
}