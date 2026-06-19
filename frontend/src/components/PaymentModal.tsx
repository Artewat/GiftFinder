import { useEffect, useState } from "react";

type Props = {
  /** Сумма к оплате, для подписи кнопки. */
  amountLabel: string;
  /** Закрыть модалку. */
  onClose: () => void;
  /** Реальное оформление (апгрейд тарифа) после «успешной оплаты». */
  onConfirm: () => Promise<void>;
};

type Field = "number" | "expiry" | "cvc" | "name";

function formatCardNumber(v: string): string {
  return v.replace(/\D/g, "").slice(0, 16).replace(/(.{4})(?=.)/g, "$1 ");
}

function formatExpiry(v: string): string {
  const d = v.replace(/\D/g, "").slice(0, 4);
  return d.length <= 2 ? d : `${d.slice(0, 2)}/${d.slice(2)}`;
}

/** Определение платёжной системы по префиксу — мелкая деталь для реалистичности. */
function cardBrand(digits: string): string | null {
  if (/^4/.test(digits)) return "VISA";
  if (/^220[0-4]/.test(digits)) return "МИР"; // 2200–2204 — проверяем до Mastercard
  if (/^(5[1-5]|22[2-9]|2[3-7])/.test(digits)) return "Mastercard";
  return null;
}

/** Алгоритм Луна — отсекает «невозможные» номера карт. */
function luhnValid(digits: string): boolean {
  let sum = 0;
  let alt = false;
  for (let i = digits.length - 1; i >= 0; i--) {
    let n = Number(digits[i]);
    if (alt) {
      n *= 2;
      if (n > 9) n -= 9;
    }
    sum += n;
    alt = !alt;
  }
  return sum % 10 === 0;
}

// --- Валидаторы полей: null = ошибок нет ---

function numberError(digits: string): string | null {
  if (digits.length < 16) return "Введите 16 цифр номера карты";
  if (!luhnValid(digits)) return "Проверьте номер карты — такого не существует";
  return null;
}

function expiryError(expiry: string): string | null {
  if (!/^\d{2}\/\d{2}$/.test(expiry)) return "Укажите срок в формате ММ/ГГ";
  const month = Number(expiry.slice(0, 2));
  const year = 2000 + Number(expiry.slice(3, 5));
  if (month < 1 || month > 12) return "Такого месяца не бывает (01–12)";
  // последний день месяца окончания действия
  const expEnd = new Date(year, month, 1);
  const now = new Date();
  const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  if (expEnd <= monthStart) return "Срок действия карты истёк";
  return null;
}

function cvcError(cvc: string): string | null {
  if (cvc.length < 3) return "CVC — это 3 цифры на обороте карты";
  return null;
}

function nameError(name: string): string | null {
  if (name.trim().length < 2) return "Укажите имя как на карте";
  return null;
}

export default function PaymentModal({ amountLabel, onClose, onConfirm }: Props) {
  const [number, setNumber] = useState("");
  const [expiry, setExpiry] = useState("");
  const [cvc, setCvc] = useState("");
  const [name, setName] = useState("");
  const [touched, setTouched] = useState<Record<Field, boolean>>({
    number: false, expiry: false, cvc: false, name: false,
  });
  const [submitted, setSubmitted] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Esc закрывает (но не во время «оплаты»)
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !processing) onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, processing]);

  const digits = number.replace(/\D/g, "");
  const brand = cardBrand(digits);

  const errors: Record<Field, string | null> = {
    number: numberError(digits),
    expiry: expiryError(expiry),
    cvc: cvcError(cvc),
    name: nameError(name),
  };
  const formValid = Object.values(errors).every((e) => e === null);

  // показываем ошибку поля только после касания или попытки оплаты
  const show = (f: Field): string | null =>
    (touched[f] || submitted) ? errors[f] : null;
  const blur = (f: Field) => setTouched((t) => ({ ...t, [f]: true }));

  function inputCls(f: Field, extra = ""): string {
    const bad = show(f) !== null;
    return (
      `w-full rounded-lg border px-3 py-2.5 outline-none focus:ring-2 ${extra} ` +
      (bad
        ? "border-rose-400 focus:border-rose-400 focus:ring-rose-200"
        : "border-violet-200 focus:border-violet-400 focus:ring-violet-200")
    );
  }

  async function pay(e: React.FormEvent) {
    e.preventDefault();
    if (processing) return;
    setSubmitted(true);
    setError(null);
    if (!formValid) return; // ошибки подсветятся под полями
    setProcessing(true);
    try {
      // имитация обращения к платёжному шлюзу
      await new Promise((r) => setTimeout(r, 1200));
      await onConfirm();
      // при успехе onConfirm уводит на /search, модалка размонтируется
    } catch {
      setError("Не удалось оформить подписку. Попробуйте ещё раз.");
      setProcessing(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="pay-title"
    >
      <button
        type="button"
        aria-label="Закрыть"
        onClick={() => !processing && onClose()}
        className="absolute inset-0 cursor-default bg-violet-950/40 backdrop-blur-sm"
      />
      <div className="relative w-full max-w-md rounded-t-2xl bg-white p-6 shadow-xl sm:rounded-2xl">
        <div className="flex items-start justify-between">
          <div>
            <h2 id="pay-title" className="text-xl font-bold text-violet-950">
              Оформление Premium
            </h2>
            <p className="mt-1 text-sm text-slate-500">
              Безлимитный поиск · {amountLabel}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={processing}
            aria-label="Закрыть"
            className="-mr-1 -mt-1 inline-flex h-9 w-9 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-violet-50 hover:text-violet-700 disabled:opacity-40"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
              <line x1="6" y1="6" x2="18" y2="18" />
              <line x1="18" y1="6" x2="6" y2="18" />
            </svg>
          </button>
        </div>

        <div className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-700">
          Демо-оплата: данные карты никуда не отправляются. Введите любые цифры —
          например, 4111 1111 1111 1111.
        </div>

        <form onSubmit={pay} noValidate className="mt-4 space-y-3">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-violet-950">Номер карты</span>
            <div className="relative">
              <input
                inputMode="numeric"
                autoComplete="cc-number"
                placeholder="0000 0000 0000 0000"
                value={number}
                onChange={(e) => setNumber(formatCardNumber(e.target.value))}
                onBlur={() => blur("number")}
                aria-invalid={show("number") !== null}
                className={inputCls("number", "pr-16")}
              />
              {brand && (
                <span className="pointer-events-none absolute right-3 top-[1.35rem] -translate-y-1/2 text-xs font-semibold text-violet-500">
                  {brand}
                </span>
              )}
            </div>
            {show("number") && (
              <p className="mt-1 text-xs text-rose-600">{show("number")}</p>
            )}
          </label>

          <div className="flex gap-3">
            <label className="block flex-1">
              <span className="mb-1 block text-sm font-medium text-violet-950">Срок</span>
              <input
                inputMode="numeric"
                autoComplete="cc-exp"
                placeholder="ММ/ГГ"
                value={expiry}
                onChange={(e) => setExpiry(formatExpiry(e.target.value))}
                onBlur={() => blur("expiry")}
                aria-invalid={show("expiry") !== null}
                className={inputCls("expiry")}
              />
              {show("expiry") && (
                <p className="mt-1 text-xs text-rose-600">{show("expiry")}</p>
              )}
            </label>
            <label className="block w-24">
              <span className="mb-1 block text-sm font-medium text-violet-950">CVC</span>
              <input
                inputMode="numeric"
                autoComplete="cc-csc"
                placeholder="123"
                value={cvc}
                onChange={(e) => setCvc(e.target.value.replace(/\D/g, "").slice(0, 4))}
                onBlur={() => blur("cvc")}
                aria-invalid={show("cvc") !== null}
                className={inputCls("cvc")}
              />
            </label>
          </div>
          {show("cvc") && (
            <p className="-mt-1 text-xs text-rose-600">{show("cvc")}</p>
          )}

          <label className="block">
            <span className="mb-1 block text-sm font-medium text-violet-950">Имя на карте</span>
            <input
              autoComplete="cc-name"
              placeholder="IVAN IVANOV"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onBlur={() => blur("name")}
              aria-invalid={show("name") !== null}
              className={inputCls("name", "uppercase placeholder:normal-case")}
            />
            {show("name") && (
              <p className="mt-1 text-xs text-rose-600">{show("name")}</p>
            )}
          </label>

          {error && (
            <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>
          )}

          <button
            type="submit"
            disabled={processing}
            className="mt-1 w-full rounded-full bg-violet-600 py-3 font-medium text-white transition-colors hover:bg-violet-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {processing ? "Обработка платежа…" : `Оплатить ${amountLabel}`}
          </button>
          <p className="text-center text-xs text-slate-400">🔒 Демонстрационная оплата, реальное списание не производится</p>
        </form>
      </div>
    </div>
  );
}
