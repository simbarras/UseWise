import { useNavigate } from 'react-router-dom';

const gdprArticles = [
  { id: 'Art. 6',  subject: 'Lawfulness of processing',          url: 'https://gdpr-info.eu/art-6-gdpr/'  },
  { id: 'Art. 13', subject: 'Info provided at collection',       url: 'https://gdpr-info.eu/art-13-gdpr/' },
  { id: 'Art. 15', subject: 'Right of access by the subject',    url: 'https://gdpr-info.eu/art-15-gdpr/' },
  { id: 'Art. 17', subject: 'Right to erasure ("be forgotten")', url: 'https://gdpr-info.eu/art-17-gdpr/' },
  { id: 'Art. 20', subject: 'Right to data portability',         url: 'https://gdpr-info.eu/art-20-gdpr/' },
  { id: 'Art. 25', subject: 'Privacy by design & default',       url: 'https://gdpr-info.eu/art-25-gdpr/' },
];

export default function Sidebar() {
  const navigate = useNavigate();

  return (
    <aside className="w-52 bg-primary text-slate-400 p-5 flex flex-col h-full border-r border-white/5 overflow-hidden">
      <nav className="flex flex-col mt-4 gap-4">

        {/* ── ABOUT ── */}
        <div>
          <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[2px] mb-2 px-1">
            About UseWise
          </p>
          <button
            onClick={() => navigate('/about')}
            className="w-full flex items-center gap-2 py-2 px-2 rounded-lg hover:bg-white/5 hover:text-white transition-all group text-left"
          >
            <span className="text-[10px] font-medium">Our Mission </span>
          </button>
        </div>

        {/* ── DIVIDER ── */}
        <div className="border-t border-white/5 -mx-5" />

        {/* ── GDPR ARTICLES ── */}
        <div>
          <p className="text-[9px] font-bold text-slate-500 uppercase tracking-[2px] mb-2 px-1">
            GDPR Articles
          </p>
          <div className="space-y-1">
            {gdprArticles.map((article) => (
              <a
                key={article.id}
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-start gap-2 py-2 px-2 rounded-lg hover:bg-white/5 hover:text-white transition-all group text-left"
              >
                <span className="text-[9px] font-bold text-[var(--secondary)] shrink-0 mt-0.5 w-10">
                  {article.id}
                </span>
                <span className="text-[10px] leading-tight text-slate-400 group-hover:text-white transition-colors">
                  {article.subject}
                </span>
              </a>
            ))}

            {/* Full GDPR link inline */}
            <a
              href="https://gdpr-info.eu/"
              target="_blank"
              rel="noopener noreferrer"
              className="w-full flex items-center gap-2 py-2 px-2 rounded-lg hover:bg-white/5 transition-all group text-left mt-1"
            >
              <span className="text-[10px] text-slate-400 group-hover:text-[var(--secondary)] transition-colors">
                Full GDPR text →
              </span>
            </a>
          </div>
        </div>

      </nav>
    </aside>
  );
}