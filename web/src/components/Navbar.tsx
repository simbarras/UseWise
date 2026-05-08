import { useNavigate } from "react-router-dom";

interface Props {
  onMenuToggle: () => void;
}

export default function Navbar({ onMenuToggle }: Props) {
  const navigate = useNavigate();

  return (
    <header className="h-12 bg-[var(--nav-bg)] flex items-center px-4 sm:px-6 gap-4 shrink-0">
      {/* Hamburger — mobile only */}
      <button
        onClick={onMenuToggle}
        className="md:hidden flex flex-col justify-center items-center gap-[5px] w-8 h-8 shrink-0"
        aria-label="Toggle menu"
      >
        <span className="block w-5 h-0.5 bg-white rounded-full" />
        <span className="block w-5 h-0.5 bg-white rounded-full" />
        <span className="block w-5 h-0.5 bg-white rounded-full" />
      </button>

      {/* Logo */}
      <div
        className="flex items-center gap-3 cursor-pointer shrink-0"
        onClick={() => navigate("/")}
      >
        <img
          src="/logo.png"
          alt="UseWise Logo"
          className="w-15 h-15 object-contain"
        />
        <span className="text-white font-bold text-lg tracking-tight">
          UseWise
        </span>
      </div>
    </header>
  );
}
