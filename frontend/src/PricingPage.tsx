import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthContext";
import { upgradeToPremium, downgradeToFree } from "./api";
import NavBar from "./components/NavBar";
import PaymentModal from "./components/PaymentModal";

export default function PricingPage() {
  const { user, refresh } = useAuth();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);
  const [checkout, setCheckout] = useState(false);
  const isPremium = user?.tier === "premium";

  // вызывается модалкой после «успешной оплаты»
  async function onPaid() {
    await upgradeToPremium();
    await refresh();
    navigate("/search");
  }
  async function onDowngrade() {
    setBusy(true);
    try { await downgradeToFree(); await refresh(); }
    finally { setBusy(false); }
  }

  return (
    <div className="min-h-screen bg-[#F5F3FA]">
      <NavBar active="pricing" />
      <div className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="mb-2 text-center text-3xl font-bold text-violet-950">Тарифы</h1>
        <p className="mb-8 text-center text-slate-600">Подбор подарков с ИИ — выберите план</p>
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="rounded-2xl border border-violet-100 bg-white p-6">
            <h2 className="text-lg font-semibold text-violet-950">Free</h2>
            <p className="mt-1 text-slate-600">До 5 поисков в день</p>
            <p className="mt-4 text-2xl font-bold text-violet-700">0 ₽</p>
            {!isPremium && <p className="mt-4 text-sm text-slate-500">Ваш текущий тариф</p>}
            {isPremium && (
              <button onClick={onDowngrade} disabled={busy}
                className="mt-4 w-full rounded-full border border-violet-200 py-2.5 text-violet-700 hover:bg-violet-50 disabled:opacity-60">
                Вернуться на Free
              </button>
            )}
          </div>
          <div className="rounded-2xl border-2 border-violet-400 bg-white p-6">
            <h2 className="text-lg font-semibold text-violet-950">Premium</h2>
            <p className="mt-1 text-slate-600">Безлимитный поиск</p>
            <p className="mt-4 text-2xl font-bold text-violet-700">299 ₽/мес</p>
            {isPremium ? (
              <p className="mt-4 text-sm font-medium text-violet-700">Ваш текущий тариф</p>
            ) : (
              <button onClick={() => setCheckout(true)}
                className="mt-4 w-full rounded-full bg-violet-600 py-2.5 font-medium text-white hover:bg-violet-700">
                Оформить premium
              </button>
            )}
          </div>
        </div>
        <p className="mt-6 text-center text-xs text-slate-400">
          Оплата — демонстрационная заглушка. Подключение платёжного шлюза — точка расширения.
        </p>
      </div>

      {checkout && (
        <PaymentModal
          amountLabel="299 ₽"
          onClose={() => setCheckout(false)}
          onConfirm={onPaid}
        />
      )}
    </div>
  );
}
