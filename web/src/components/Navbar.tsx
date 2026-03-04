import { useNavigate, useLocation } from 'react-router-dom';

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { label: 'Home', path: '/' },
    { label: 'Analysis Tool', path: '/results' },
  ];

  return (
    <header className="h-12 bg-[var(--nav-bg)] flex items-center px-6 gap-10 shrink-0">
      {/* Logo */}
      <div
        className="flex items-center gap-3 cursor-pointer shrink-0"
        onClick={() => navigate('/')}
      >
        <img src="/logo.png" alt="UseWise Logo" className="w-15 h-15 object-contain" />
        <span className="text-white font-bold text-lg tracking-tight">UseWise</span>
      </div>

      {/* Nav links */}
      <div className="flex-1 flex items-center justify-center gap-80 text-[10px] font-bold text-white/50 uppercase tracking-[2px]">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <button
              key={item.label}
              onClick={() => navigate(item.path)}
              className={`transition-colors hover:text-white ${isActive ? 'text-[var(--secondary)]' : ''}`}
            >
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
}