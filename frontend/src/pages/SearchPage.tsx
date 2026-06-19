import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  searchGifts, getUsage, SearchLimitError, type Usage,
  getWishlistIds, addToWishlist, removeFromWishlistByProduct,
} from "../api";
import type { GiftCard as GiftCardType } from "../types";
import GiftCard from "../components/GiftCard";
import NavBar from "../components/NavBar";

type Status = "idle" | "loading" | "done" | "error";

const EXAMPLES = [
  "Подарок папе-рыбаку до 3000 ₽",
  "Настольная игра для компании друзей",
  "Что подарить любителю готовить, 1000–3500 ₽",
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [results, setResults] = useState<GiftCardType[]>([]);
  const [lastQuery, setLastQuery] = useState("");
  const [usage, setUsage] = useState<Usage | null>(null);
  const [limitReached, setLimitReached] = useState(false);
  const [wishlistIds, setWishlistIds] = useState<Set<number>>(new Set());

  async function loadUsage() {
    try { setUsage(await getUsage()); } catch { /* не критично */ }
  }
  useEffect(() => { loadUsage(); }, []);

  useEffect(() => {
    getWishlistIds().then((ids) => setWishlistIds(new Set(ids))).catch(() => {});
  }, []);

  async function toggleWishlist(productId: number) {
    const inList = wishlistIds.has(productId);
    // оптимистичное обновление множества
    setWishlistIds((prev) => {
      const next = new Set(prev);
      if (inList) next.delete(productId);
      else next.add(productId);
      return next;
    });
    try {
      if (inList) await removeFromWishlistByProduct(productId);
      else await addToWishlist(productId);
    } catch {
      // откат при ошибке
      setWishlistIds((prev) => {
        const next = new Set(prev);
        if (inList) next.add(productId);
        else next.delete(productId);
        return next;
      });
    }
  }

  async function run(q: string) {
    const trimmed = q.trim();
    if (!trimmed) return;
    setStatus("loading");
    setLimitReached(false);
    setLastQuery(trimmed);
    try {
      const cards = await searchGifts(trimmed);
      setResults(cards);
      setStatus("done");
      loadUsage();                       // обновить «осталось N»
    } catch (e) {
      if (e instanceof SearchLimitError) {
        setLimitReached(true);
        setStatus("idle");
        loadUsage();                     // показать remaining:0
      } else {
        setStatus("error");
      }
    }
  }

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    run(query);
  }

  return (
    <div className="min-h-screen bg-[#F5F3FA] text-violet-950">
      {/* Навигация */}
      <NavBar active="search" />

      <div className="mx-auto max-w-5xl px-4 py-10 sm:py-14">
        {/* Шапка + поиск */}
        <header className="mx-auto max-w-2xl text-center">
          <p className="mb-2 text-sm font-medium uppercase tracking-widest text-violet-500">
            Умный подбор подарков
          </p>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">
            Опишите, кому и по какому поводу
          </h1>
          <p className="mt-3 text-slate-600">
            Подберём идеи под получателя, повод и бюджет — и покажем, где купить.
          </p>

          <form onSubmit={onSubmit} className="mt-7">
            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Например: подарок маме на юбилей до 5000 ₽"
                className="w-full rounded-full border border-violet-200 bg-white px-5 py-3.5 text-base shadow-sm outline-none placeholder:text-slate-400 focus:border-violet-400 focus:ring-2 focus:ring-violet-200"
              />
              <button
                type="submit"
                disabled={status === "loading"}
                className="shrink-0 rounded-full bg-violet-600 px-7 py-3.5 font-medium text-white shadow-sm transition-colors hover:bg-violet-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600 disabled:opacity-60"
              >
                {status === "loading" ? "Ищем…" : "Найти подарки"}
              </button>
            </div>
          </form>

          {usage && usage.tier === "free" && (
            <p className="mt-3 text-center text-sm text-slate-500">
              Осталось поисков сегодня: {usage.remaining} из {usage.limit}
            </p>
          )}

          {limitReached && (
            <div className="mx-auto mt-6 max-w-md rounded-2xl border border-amber-200 bg-amber-50 p-5 text-center">
              <p className="font-medium text-amber-800">Дневной лимит поисков исчерпан</p>
              <p className="mt-1 text-sm text-amber-700">
                Оформите premium для безлимитного поиска.
              </p>
              <Link
                to="/pricing"
                className="mt-3 inline-block rounded-full bg-violet-600 px-5 py-2 text-sm font-medium text-white hover:bg-violet-700"
              >
                Перейти к тарифам
              </Link>
            </div>
          )}

          {status === "idle" && !limitReached && (
            <div className="mt-5 flex flex-wrap justify-center gap-2">
              {EXAMPLES.map((ex) => (
                <button
                  key={ex}
                  onClick={() => {
                    setQuery(ex);
                    run(ex);
                  }}
                  className="rounded-full border border-violet-200 bg-white px-4 py-1.5 text-sm text-violet-700 transition-colors hover:border-violet-300 hover:bg-violet-50"
                >
                  {ex}
                </button>
              ))}
            </div>
          )}
        </header>

        {/* Результаты / состояния */}
        <section className="mt-12">
          {status === "loading" && <SkeletonGrid />}

          {status === "error" && (
            <div className="mx-auto max-w-md rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center">
              <p className="font-medium text-rose-700">
                Не удалось выполнить поиск
              </p>
              <p className="mt-1 text-sm text-rose-600">
                Проверьте, что сервер запущен, и попробуйте ещё раз.
              </p>
              <button
                onClick={() => run(lastQuery)}
                className="mt-4 rounded-full bg-rose-600 px-5 py-2 text-sm font-medium text-white hover:bg-rose-700"
              >
                Повторить
              </button>
            </div>
          )}

          {status === "done" && results.length === 0 && (
            <div className="mx-auto max-w-md text-center text-slate-500">
              <p className="text-lg font-medium text-violet-950">
                Ничего не подобралось
              </p>
              <p className="mt-1 text-sm">
                Попробуйте описать получателя, его увлечения или повод другими
                словами.
              </p>
            </div>
          )}

          {status === "done" && results.length > 0 && (
            <>
              <p className="mb-5 text-sm text-slate-500">
                Идеи по запросу «{lastQuery}»
              </p>
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {results.map((card) => (
                  <GiftCard
                    key={card.id}
                    card={card}
                    inWishlist={wishlistIds.has(card.id)}
                    onToggleWishlist={() => toggleWishlist(card.id)}
                  />
                ))}
              </div>
            </>
          )}
        </section>
      </div>
    </div>
  );
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div
          key={i}
          className="overflow-hidden rounded-2xl border border-violet-100 bg-white"
        >
          <div className="aspect-[4/3] animate-pulse bg-violet-100 motion-reduce:animate-none" />
          <div className="space-y-3 p-4">
            <div className="h-4 w-3/4 animate-pulse rounded bg-violet-100 motion-reduce:animate-none" />
            <div className="h-3 w-full animate-pulse rounded bg-violet-50 motion-reduce:animate-none" />
            <div className="h-3 w-2/3 animate-pulse rounded bg-violet-50 motion-reduce:animate-none" />
          </div>
        </div>
      ))}
    </div>
  );
}
