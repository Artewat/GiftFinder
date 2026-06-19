import type { GiftCard, SearchResponse } from "./types";

// Базовый адрес бэкенда. Можно переопределить через .env (VITE_API_BASE),
// иначе используется локальный FastAPI на :8000.
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// Единая точка: credentials:"include" — чтобы httpOnly-кука ходила на каждый запрос.
// ВАЖНО: используй localhost и на фронте, и на бэке (не мешай с 127.0.0.1) — иначе кука не отправится.
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
}

export interface User {
  id: number;
  email: string;
  tier: string;
  created_at: string;
}

async function jsonOrThrow(res: Response, fallback: string) {
  if (res.ok) return res.json();
  let detail = fallback;
  try { detail = (await res.json()).detail ?? fallback; } catch { /* ignore */ }
  throw new Error(detail);
}

export async function register(email: string, password: string): Promise<User> {
  const res = await apiFetch("/api/auth/register", {
    method: "POST", body: JSON.stringify({ email, password }),
  });
  return jsonOrThrow(res, "Ошибка регистрации");
}

export async function login(email: string, password: string): Promise<User> {
  const res = await apiFetch("/api/auth/login", {
    method: "POST", body: JSON.stringify({ email, password }),
  });
  return jsonOrThrow(res, "Неверный email или пароль");
}

export async function logout(): Promise<void> {
  await apiFetch("/api/auth/logout", { method: "POST" });
}

export async function fetchMe(): Promise<User | null> {
  const res = await apiFetch("/api/auth/me");
  if (res.status === 401) return null;       // не залогинен — это норма, не ошибка
  return jsonOrThrow(res, "Ошибка профиля");
}

export interface Usage {
  tier: string;
  limit: number | null;
  used: number;
  remaining: number | null;
}

// Спец-ошибка для исчерпанного лимита — UI ловит её отдельно от обычных ошибок.
export class SearchLimitError extends Error {
  used: number;
  limit: number;
  constructor(used: number, limit: number) {
    super("Лимит поисков исчерпан");
    this.name = "SearchLimitError";
    this.used = used;
    this.limit = limit;
  }
}

export async function getUsage(): Promise<Usage> {
  const res = await apiFetch("/api/usage");
  return jsonOrThrow(res, "Не удалось получить лимит");
}

export async function upgradeToPremium(): Promise<User> {
  const res = await apiFetch("/api/billing/upgrade", { method: "POST" });
  return jsonOrThrow(res, "Не удалось оформить premium");
}

export async function downgradeToFree(): Promise<User> {
  const res = await apiFetch("/api/billing/downgrade", { method: "POST" });
  return jsonOrThrow(res, "Не удалось сменить тариф");
}

export interface WishlistItem {
  id: number;
  product_id: number | null;
  available: boolean;
  title: string;
  price: number | null;
  currency: string;
  image_url: string | null;
  product_url: string;
  added_at: string;
}

export async function getWishlist(): Promise<WishlistItem[]> {
  const res = await apiFetch("/api/wishlist");
  return jsonOrThrow(res, "Не удалось загрузить избранное");
}

export async function getWishlistIds(): Promise<number[]> {
  const res = await apiFetch("/api/wishlist/ids");
  return jsonOrThrow(res, "Ошибка избранного");
}

export async function addToWishlist(productId: number): Promise<WishlistItem> {
  const res = await apiFetch("/api/wishlist", {
    method: "POST", body: JSON.stringify({ product_id: productId }),
  });
  return jsonOrThrow(res, "Не удалось добавить в избранное");
}

export async function removeFromWishlistByProduct(productId: number): Promise<void> {
  await apiFetch(`/api/wishlist/by-product/${productId}`, { method: "DELETE" });
}

export async function removeFromWishlistItem(itemId: number): Promise<void> {
  await apiFetch(`/api/wishlist/${itemId}`, { method: "DELETE" });
}

export async function searchGifts(query: string): Promise<GiftCard[]> {
  const res = await apiFetch("/api/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });

  if (res.status === 429) {
    const d = (await res.json().catch(() => ({}))).detail ?? {};
    throw new SearchLimitError(d.used ?? 0, d.limit ?? 5);
  }
  if (!res.ok) {
    throw new Error(`Поиск не выполнен (HTTP ${res.status})`);
  }

  const data: SearchResponse = await res.json();
  return data.results ?? [];
}
