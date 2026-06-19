import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { resendVerification } from "./api";

export default function RegisterPage() {
  const { register } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password.length < 6) { setError("Пароль не короче 6 символов"); return; }
    setBusy(true);
    try { await register(email, password); setSent(true); }
    catch (err) { setError(err instanceof Error ? err.message : "Ошибка"); }
    finally { setBusy(false); }
  }

  if (sent) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F5F3FA] px-4">
        <div className="w-full max-w-sm rounded-2xl border border-violet-100 bg-white p-6 text-center shadow-sm">
          <h1 className="mb-3 text-xl font-semibold text-violet-950">Проверьте почту</h1>
          <p className="text-sm text-slate-600">
            Мы отправили письмо на <b>{email}</b>. Перейдите по ссылке, чтобы подтвердить аккаунт.
          </p>
          <p className="mt-2 text-xs text-slate-400">
            В dev-режиме ссылка печатается в логах backend.
          </p>
          <button onClick={() => resendVerification(email)}
            className="mt-4 w-full rounded-full border border-violet-200 py-2.5 text-violet-700 hover:bg-violet-50">
            Отправить письмо повторно
          </button>
          <Link to="/login" className="mt-3 inline-block text-sm text-violet-700 hover:underline">
            Перейти ко входу
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F5F3FA] px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-2xl border border-violet-100 bg-white p-6 shadow-sm">
        <h1 className="mb-5 text-xl font-semibold text-violet-950">Регистрация</h1>
        {error && <p className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <input type="email" required placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)}
          className="mb-3 w-full rounded-lg border border-violet-200 px-3 py-2.5 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-200" />
        <input type="password" required placeholder="Пароль (минимум 6 символов)" value={password} onChange={(e) => setPassword(e.target.value)}
          className="mb-4 w-full rounded-lg border border-violet-200 px-3 py-2.5 outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-200" />
        <button type="submit" disabled={busy}
          className="w-full rounded-full bg-violet-600 py-2.5 font-medium text-white hover:bg-violet-700 disabled:opacity-60">
          {busy ? "Создаём…" : "Зарегистрироваться"}
        </button>
        <p className="mt-4 text-center text-sm text-slate-600">
          Уже есть аккаунт? <Link to="/login" className="text-violet-700 hover:underline">Войти</Link>
        </p>
      </form>
    </div>
  );
}
