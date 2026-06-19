import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

type Active = "home" | "search" | "wishlist" | "pricing";

const LINKS: { key: Active; to: string; label: string }[] = [
  { key: "search", to: "/search", label: "Подбор" },
  { key: "wishlist", to: "/wishlist", label: "Избранное" },
  { key: "pricing", to: "/pricing", label: "Тарифы" },
];

function TierBadge({ tier }: { tier: string }) {
  const premium = tier === "premium";
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${
        premium ? "bg-violet-600 text-white" : "bg-violet-100 text-violet-700"
      }`}
    >
      {premium ? "Premium" : "Free"}
    </span>
  );
}

export default function NavBar({ active }: { active?: Active }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  async function handleLogout() {
    setOpen(false);
    // Сначала уходим с защищённого роута, потом сбрасываем сессию —
    // иначе ProtectedRoute успевает редиректнуть на /login.
    navigate("/");
    await logout();
  }

  // активную страницу не дублируем ссылкой
  const links = LINKS.filter((l) => l.key !== active);

  return (
    <nav className="sticky top-0 z-30 border-b border-violet-100 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link
          to="/"
          className="flex items-center gap-2 font-semibold text-violet-700 transition-colors hover:text-violet-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
        >
          <span className="text-xl">🎁</span>
          <span>GiftFinder</span>
        </Link>

        {/* Десктоп */}
        <div className="hidden items-center gap-2 sm:flex">
          {user ? (
            <>
              <TierBadge tier={user.tier} />
              <span className="hidden text-sm text-slate-500 lg:inline">
                {user.email}
              </span>
              {links.map((l) => (
                <Link
                  key={l.key}
                  to={l.to}
                  className="rounded-full px-3.5 py-1.5 text-sm font-medium text-violet-700 transition-colors hover:bg-violet-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
                >
                  {l.label}
                </Link>
              ))}
              <button
                onClick={handleLogout}
                className="rounded-full px-3 py-1.5 text-sm font-medium text-slate-500 transition-colors hover:bg-violet-100 hover:text-violet-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
              >
                Выйти
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="rounded-full px-4 py-1.5 text-sm font-medium text-violet-700 transition-colors hover:bg-violet-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
              >
                Войти
              </Link>
              <Link
                to="/register"
                className="rounded-full bg-violet-600 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-violet-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
              >
                Регистрация
              </Link>
            </>
          )}
        </div>

        {/* Бургер (моб.) */}
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          aria-label={open ? "Закрыть меню" : "Открыть меню"}
          aria-expanded={open}
          aria-controls="mobile-menu"
          className="inline-flex h-10 w-10 items-center justify-center rounded-lg text-violet-700 transition-colors hover:bg-violet-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600 sm:hidden"
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            aria-hidden="true"
          >
            {open ? (
              <>
                <line x1="6" y1="6" x2="18" y2="18" />
                <line x1="18" y1="6" x2="6" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* Выпадающая панель (моб.) */}
      {open && (
        <div
          id="mobile-menu"
          className="border-t border-violet-100 bg-white px-4 py-3 sm:hidden"
        >
          {user ? (
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2 px-1 pb-2">
                <TierBadge tier={user.tier} />
                <span className="truncate text-sm text-slate-500">
                  {user.email}
                </span>
              </div>
              {links.map((l) => (
                <Link
                  key={l.key}
                  to={l.to}
                  onClick={() => setOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-violet-700 transition-colors hover:bg-violet-100"
                >
                  {l.label}
                </Link>
              ))}
              <button
                onClick={handleLogout}
                className="rounded-lg px-3 py-2.5 text-left text-sm font-medium text-slate-500 transition-colors hover:bg-violet-100 hover:text-violet-700"
              >
                Выйти
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <Link
                to="/login"
                onClick={() => setOpen(false)}
                className="rounded-lg px-3 py-2.5 text-sm font-medium text-violet-700 transition-colors hover:bg-violet-100"
              >
                Войти
              </Link>
              <Link
                to="/register"
                onClick={() => setOpen(false)}
                className="rounded-full bg-violet-600 px-3 py-2.5 text-center text-sm font-medium text-white transition-colors hover:bg-violet-700"
              >
                Регистрация
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  );
}
