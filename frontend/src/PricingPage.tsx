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
    <div className="min-h-screen bg-canvas">
      <NavBar active="pricing" />
      <div className="mx-auto max-w-3xl px-4 py-12">
        <h1 className="mb-2 text-center text-3xl font-bold text-fg">Тарифы</h1>
        <p className="mb-8 text-center text-fg-muted">Подбор подарков с ИИ — выберите план</p>
        <div className="grid gap-5 sm:grid-cols-2">
          <div className="rounded-2xl border border-edge bg-surface p-6">
            <h2 className="text-lg font-semibold text-fg">Free</h2>
            <p className="mt-1 text-fg-muted">До 5 поисков в день</p>
            <p className="mt-4 text-2xl font-bold text-link">0 ₽</p>
            {!isPremium && <p className="mt-4 text-sm text-fg-subtle">Ваш текущий тариф</p>}
            {isPremium && (
              <button onClick={onDowngrade} disabled={busy}
                className="mt-4 w-full rounded-full border border-edge-strong py-2.5 text-link hover:bg-surface-muted disabled:opacity-60">
                Вернуться на Free
              </button>
            )}
          </div>
          <div className="rounded-2xl border-2 border-violet-400 bg-surface p-6">
            <h2 className="text-lg font-semibold text-fg">Premium</h2>
            <p className="mt-1 text-fg-muted">Безлимитный поиск</p>
            <p className="mt-4 text-2xl font-bold text-link">299 ₽/мес</p>
            {isPremium ? (
              <p className="mt-4 text-sm font-medium text-link">Ваш текущий тариф</p>
            ) : (
              <button onClick={() => setCheckout(true)}
                className="mt-4 w-full rounded-full bg-violet-600 py-2.5 font-medium text-white hover:bg-violet-700">
                Оформить premium
              </button>
            )}
          </div>
        </div>
        <p className="mt-6 text-center text-xs text-fg-faint">
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
