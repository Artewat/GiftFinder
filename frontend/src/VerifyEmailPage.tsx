import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { resendVerification } from "./api";

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const email = params.get("email") ?? "";
  const { verifyCode } = useAuth();
  const navigate = useNavigate();
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [resent, setResent] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await verifyCode(email, code.trim());
      navigate("/search");   // код верный → бэк уже залогинил
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка");
    } finally {
      setBusy(false);
    }
  }

  // прямой заход без email — некуда слать код
  if (!email) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F5F3FA] px-4">
        <div className="w-full max-w-sm rounded-2xl border border-violet-100 bg-white p-6 text-center shadow-sm">
          <h1 className="mb-2 text-xl font-semibold text-violet-950">Подтверждение почты</h1>
          <p className="text-sm text-slate-600">Начните с регистрации или входа.</p>
          <Link to="/login" className="mt-4 inline-block text-sm text-violet-700 hover:underline">
            Перейти ко входу
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F5F3FA] px-4">
      <form onSubmit={onSubmit} className="w-full max-w-sm rounded-2xl border border-violet-100 bg-white p-6 shadow-sm">
        <h1 className="mb-2 text-xl font-semibold text-violet-950">Подтверждение почты</h1>
        <p className="mb-4 text-sm text-slate-600">
          Мы отправили код на <b>{email}</b>. Введите его ниже.
        </p>
        {error && <p className="mb-3 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
        <input
          inputMode="numeric"
          autoFocus
          placeholder="Код из письма"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          className="mb-4 w-full rounded-lg border border-violet-200 px-3 py-2.5 text-center text-lg tracking-[0.4em] outline-none focus:border-violet-400 focus:ring-2 focus:ring-violet-200"
        />
        <button type="submit" disabled={busy || code.length < 6}
          className="w-full rounded-full bg-violet-600 py-2.5 font-medium text-white hover:bg-violet-700 disabled:opacity-60">
          {busy ? "Проверяем…" : "Подтвердить"}
        </button>
        <button type="button"
          onClick={async () => { await resendVerification(email); setResent(true); }}
          className="mt-3 w-full text-sm text-violet-700 hover:underline">
          {resent ? "Код отправлен повторно" : "Отправить код ещё раз"}
        </button>
        <p className="mt-2 text-center text-xs text-slate-400">
          В dev-режиме код печатается в логах backend.
        </p>
      </form>
    </div>
  );
}
