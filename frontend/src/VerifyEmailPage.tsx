import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { verifyEmail } from "./api";

export default function VerifyEmailPage() {
  const [params] = useSearchParams();
  const [state, setState] = useState<"loading" | "ok" | "error">("loading");
  // токен одноразовый: гонимся один раз. Иначе StrictMode (dev) дёрнет
  // verify дважды и второй запрос упрётся в уже использованный токен.
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const token = params.get("token");
    if (!token) { setState("error"); return; }
    verifyEmail(token).then(() => setState("ok")).catch(() => setState("error"));
  }, [params]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F5F3FA] px-4">
      <div className="w-full max-w-sm rounded-2xl border border-violet-100 bg-white p-6 text-center shadow-sm">
        {state === "loading" && <p className="text-slate-500">Подтверждаем email…</p>}
        {state === "ok" && (
          <>
            <h1 className="mb-2 text-xl font-semibold text-violet-950">Email подтверждён</h1>
            <p className="text-sm text-slate-600">Теперь вы можете войти в аккаунт.</p>
            <Link to="/login" className="mt-4 inline-block rounded-full bg-violet-600 px-5 py-2 text-sm font-medium text-white hover:bg-violet-700">
              Войти
            </Link>
          </>
        )}
        {state === "error" && (
          <>
            <h1 className="mb-2 text-xl font-semibold text-violet-950">Ссылка недействительна</h1>
            <p className="text-sm text-slate-600">Возможно, она истекла или уже использована.</p>
            <Link to="/login" className="mt-4 inline-block text-sm text-violet-700 hover:underline">
              Запросить новое письмо при входе
            </Link>
          </>
        )}
      </div>
    </div>
  );
}
