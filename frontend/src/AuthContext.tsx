import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { type User, fetchMe, login as apiLogin, logout as apiLogout, register as apiRegister } from "./api";

interface AuthCtx {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
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
  async function register(email: string, password: string) { setUser(await apiRegister(email, password)); }
  async function logout() { await apiLogout(); setUser(null); }
  async function refresh() { setUser(await fetchMe()); }

  return (
    <Ctx.Provider value={{ user, loading, login, register, logout, refresh }}>
      {children}
    </Ctx.Provider>
  );
}

export function useAuth(): AuthCtx {
  const c = useContext(Ctx);
  if (!c) throw new Error("useAuth должен использоваться внутри AuthProvider");
  return c;
}
