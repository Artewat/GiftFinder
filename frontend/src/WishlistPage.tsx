import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getWishlist, removeFromWishlistItem, type WishlistItem } from "./api";
import NavBar from "./components/NavBar";

function formatPrice(price: number | null, currency: string): string {
  if (price == null) return "Цена по запросу";
  const symbol = currency === "RUB" ? "₽" : currency;
  return `${new Intl.NumberFormat("ru-RU").format(price)} ${symbol}`;
}

export default function WishlistPage() {
  const [items, setItems] = useState<WishlistItem[] | null>(null);

  useEffect(() => { getWishlist().then(setItems).catch(() => setItems([])); }, []);

  async function remove(id: number) {
    await removeFromWishlistItem(id);
    setItems((prev) => (prev ? prev.filter((i) => i.id !== id) : prev));
  }

  return (
    <div className="min-h-screen bg-[#F5F3FA]">
      <NavBar active="wishlist" />
      <div className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="mb-6 text-2xl font-bold text-violet-950">Избранное</h1>

        {items === null && <p className="text-slate-500">Загрузка…</p>}

        {items !== null && items.length === 0 && (
          <div className="text-slate-500">
            <p>Здесь пока пусто.</p>
            <Link to="/search" className="text-violet-700 hover:underline">Перейти к поиску</Link>
          </div>
        )}

        {items !== null && items.length > 0 && (
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <article key={item.id}
                className={`flex flex-col overflow-hidden rounded-2xl border bg-white shadow-sm ${item.available ? "border-violet-100" : "border-slate-200 opacity-75"}`}>
                <div className="relative aspect-[4/3] bg-violet-50">
                  {item.image_url ? (
                    <img src={item.image_url} alt={item.title} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-violet-200 to-rose-200">
                      <span className="text-4xl font-semibold text-white/80">{item.title.charAt(0)}</span>
                    </div>
                  )}
                  {!item.available && (
                    <span className="absolute left-2 top-2 rounded-full bg-slate-700 px-2 py-1 text-xs font-medium text-white">
                      Больше недоступен
                    </span>
                  )}
                </div>
                <div className="flex flex-1 flex-col gap-3 p-4">
                  <h3 className="text-base font-semibold leading-snug text-violet-950">{item.title}</h3>
                  <div className="mt-auto flex items-center justify-between gap-3 pt-2">
                    <span className="text-lg font-bold text-violet-700">{formatPrice(item.price, item.currency)}</span>
                    {item.available ? (
                      <a href={item.product_url} target="_blank" rel="noopener noreferrer"
                        className="inline-flex items-center rounded-full bg-violet-600 px-4 py-2 text-sm font-medium text-white hover:bg-violet-700">
                        Купить
                      </a>
                    ) : (
                      <span className="inline-flex cursor-not-allowed items-center rounded-full bg-slate-200 px-4 py-2 text-sm font-medium text-slate-400">
                        Купить
                      </span>
                    )}
                  </div>
                  <button onClick={() => remove(item.id)}
                    className="text-sm text-slate-400 hover:text-rose-600">
                    Удалить из избранного
                  </button>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
