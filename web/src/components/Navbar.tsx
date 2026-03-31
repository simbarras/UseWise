import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <header className="h-12 bg-[var(--nav-bg)] flex items-center px-6 gap-10 shrink-0">
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
