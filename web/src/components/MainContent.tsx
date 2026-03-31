import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import HowItWorksModal from './HowItWorksModal';

export default function MainContent() {
  const navigate = useNavigate();
  const [inputText, setInputText] = useState('');
  const [pdfContent, setPdfContent] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [showHowItWorks, setShowHowItWorks] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleAnalyze = () => {
    navigate('/loading', { state: { policyText: pdfContent ?? inputText ?? null } });
  };

  const loadFile = (file: File) => {
    if (file.type === 'application/pdf' || file.name.endsWith('.pdf')) {
      const reader = new FileReader();
      reader.onload = (ev) => {
        setPdfContent(ev.target?.result as string);
        setInputText(`📄 ${file.name}`);
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

      <div className="h-full w-full flex items-center justify-center bg-[var(--bg)]">
        <div className="max-w-6xl w-full grid grid-cols-1 lg:grid-cols-2 gap-12 items-center px-12">

          {/* COLONNE GAUCHE */}
          <div className="space-y-6">
            <div className="space-y-4">
              <h1 className="text-5xl font-serif text-[var(--text)] leading-tight">
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
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed p-8 flex flex-col gap-6 cursor-pointer transition-all duration-200 ${
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
              <div className="flex flex-col items-start gap-1">
                <h3 className="font-bold text-[var(--text)] text-sm">
                  {isDragging ? '📂 Drop the file here…' : 'Drag & Drop your Privacy Policy here'}
                </h3>
                <p className="text-slate-400 text-[10px]">Or paste URL or text below</p>
              </div>

              <textarea
                value={inputText}
                onChange={(e) => { e.stopPropagation(); setInputText(e.target.value); setPdfContent(null); }}
                onClick={(e) => e.stopPropagation()}
                placeholder="Paste your privacy policy text or URL here..."
                className="w-full h-20 bg-white/60 border border-slate-200 rounded text-[10px] text-slate-600 p-2 resize-none focus:outline-none focus:border-[var(--secondary)] placeholder:text-slate-300"
              />

              <div className="flex items-center gap-6">
                <button
                  onClick={(e) => { e.stopPropagation(); handleAnalyze(); }}
                  className="bg-[var(--secondary)] text-white px-6 py-2 rounded-md font-bold text-xs shadow-md hover:brightness-110 transition-all active:scale-95"
                >
                  Analyze with UseWise
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setShowHowItWorks(true); }}
                  className="text-[var(--secondary)] font-bold text-xs hover:underline"
                >
                  How it Works
                </button>
              </div>
            </div>
          </div>

          {/* COLONNE DROITE */}
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