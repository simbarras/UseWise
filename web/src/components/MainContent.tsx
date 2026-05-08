import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import HowItWorksModal from './HowItWorksModal';

export default function MainContent() {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState('');
  const [pdfContent, setPdfContent] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAnalyze = () => {
    navigate('/loading', { state: { policyText: pdfContent ?? inputText ?? null } });
  };

  const loadFile = (file: File) => {
    setFileName(file.name);
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setPdfContent(ev.target?.result as string);
        setInputText('');
      };
      reader.readAsDataURL(file);
    } else {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setPdfContent(null);
        setInputText(ev.target?.result as string);
      };
      reader.readAsText(file);
    }
  };

  const clearFile = () => {
    setFileName(null);
    setPdfContent(null);
    setInputText('');
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) loadFile(file);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) loadFile(file);
  };

  return (
    <>
      {showHowItWorks && <HowItWorksModal onClose={() => setShowHowItWorks(false)} />}

      <div className="min-h-full w-full flex items-center justify-center bg-[var(--bg)] py-8">
        <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center px-4 sm:px-8 lg:px-12">

          {/* LEFT COLUMN */}
          <div className="space-y-6">
            <div className="space-y-4">
              <h1 className="text-4xl sm:text-5xl font-serif text-[var(--text)] leading-tight">
                Stop Scrolling.<br />
                Start <span className="text-[var(--secondary)] italic">Knowing.</span>
              </h1>
              <p className="text-slate-500 text-[11px] max-w-sm leading-relaxed">
                80% of users care about privacy, but nobody has 76 workdays to read fine print.
                UseWise uses AI to turn 50 pages of legal jargon into 30 seconds of clarity.
              </p>
            </div>

            {/* DROP ZONE */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`border-2 border-dashed p-6 sm:p-8 flex flex-col gap-5 transition-all duration-200 ${
                isDragging
                  ? 'border-[var(--secondary)] bg-[var(--secondary)]/10 scale-[1.01]'
                  : 'border-[var(--secondary)] bg-white/40'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.pdf,.doc,.docx"
                className="hidden"
                onChange={handleFileChange}
              />

              {/* Header */}
              <div className="flex flex-col items-start gap-1">
                <h3 className="font-bold text-[var(--text)] text-sm">
                  {isDragging ? '📂 Drop the file here…' : 'Upload your Privacy Policy'}
                </h3>
                <p className="text-slate-400 text-[10px] hidden sm:block">
                  Drag & drop, tap the button, or paste text below
                </p>
                <p className="text-slate-400 text-[10px] sm:hidden">
                  Choose a file from your device or paste text below
                </p>
              </div>

              {/* File upload button + selected file indicator */}
              <div className="flex flex-wrap items-center gap-3">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="flex items-center gap-2 bg-white border border-[var(--secondary)] text-[var(--secondary)] px-4 py-2 rounded-md font-bold text-xs shadow-sm hover:bg-[var(--secondary)] hover:text-white transition-all active:scale-95"
                >
                  {/* Upload icon */}
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="w-3.5 h-3.5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="17 8 12 3 7 8" />
                    <line x1="12" y1="3" x2="12" y2="15" />
                  </svg>
                  Choose a file
                </button>

                {fileName && (
                  <div className="flex items-center gap-1.5 bg-[var(--secondary)]/10 border border-[var(--secondary)]/30 rounded-md px-3 py-1.5 max-w-full">
                    <span className="text-[10px] text-[var(--secondary)] font-medium truncate max-w-[180px] sm:max-w-[260px]">
                      📄 {fileName}
                    </span>
                    <button
                      onClick={clearFile}
                      className="text-[var(--secondary)] opacity-60 hover:opacity-100 transition-opacity shrink-0 leading-none text-xs ml-1"
                      aria-label="Remove file"
                    >
                      ✕
                    </button>
                  </div>
                )}
              </div>

              {/* Divider */}
              <div className="flex items-center gap-3">
                <div className="flex-1 h-px bg-slate-200" />
                <span className="text-[10px] text-slate-400 shrink-0">or paste text</span>
                <div className="flex-1 h-px bg-slate-200" />
              </div>

              {/* Textarea */}
              <textarea
                value={inputText}
                onChange={(e) => { setInputText(e.target.value); setPdfContent(null); setFileName(null); }}
                placeholder="Paste your privacy policy text or URL here..."
                className="w-full h-20 bg-white/60 border border-slate-200 rounded text-[10px] text-slate-600 p-2 resize-none focus:outline-none focus:border-[var(--secondary)] placeholder:text-slate-300"
              />

              {/* Actions */}
              <div className="flex flex-wrap items-center gap-4">
                <button
                  onClick={handleAnalyze}
                  className="bg-[var(--secondary)] text-white px-6 py-2 rounded-md font-bold text-xs shadow-md hover:brightness-110 transition-all active:scale-95"
                >
                  Analyze with UseWise
                </button>
                <button
                  onClick={() => setShowHowItWorks(true)}
                  className="text-[var(--secondary)] font-bold text-xs hover:underline"
                >
                  How it Works
                </button>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="hidden lg:flex justify-center">
            <div className="relative w-full h-full flex items-center justify-center">
              <img
                src="/file_image_no_bg.png"
                alt="Legal Analysis Illustration"
                className="w-3/5 h-auto object-contain"
              />
            </div>
          </div>

        </div>
      </div>
    </>
  );
}
