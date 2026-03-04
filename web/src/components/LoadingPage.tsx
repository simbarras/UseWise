export default function LoadingPage() {
  return (
    <div className="h-full w-full flex flex-col items-center justify-center bg-[var(--bg)] gap-6">

      {/* Spinner */}
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-4 border-white/10" />
        <div
          className="absolute inset-0 rounded-full border-4 border-transparent border-t-[var(--secondary)]"
          style={{ animation: 'spin 0.9s linear infinite' }}
        />
      </div>

      {/* Text */}
      <div className="flex flex-col items-center gap-1">
        <p className="text-sm font-bold text-[var(--text)]">Analyzing your policy…</p>
        <p className="text-[10px] text-slate-500">This usually takes a few seconds</p>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}