import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  type User, fetchMe, login as apiLogin, logout as apiLogout,
  register as apiRegister, verifyEmailCode as apiVerifyCode,
} from "./api";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  verifyCode: (email: string, code: string) => Promise<void>;   // подтверждение кода → авто-вход
  logout: () => Promise<void>;
  refresh: () => Promise<void>;   // перечитать профиль (нужно после смены тарифа)
}

const Ctx = createContext<AuthCtx | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMe().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) { setUser(await apiLogin(email, password)); }
  // строгий гейтинг: register больше НЕ логинит — вход только после подтверждения email
  async function register(email: string, password: string) { await apiRegister(email, password); }
  // верный код → бэк ставит куку, возвращает профиль → сразу логинимся
  async function verifyCode(email: string, code: string) { setUser(await apiVerifyCode(email, code)); }
  async function logout() { await apiLogout(); setUser(null); }
  async function refresh() { setUser(await fetchMe()); }

  return (
    <Ctx.Provider value={{ user, loading, login, register, verifyCode, logout, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth должен использоваться внутри AuthProvider");
  return c;
}
