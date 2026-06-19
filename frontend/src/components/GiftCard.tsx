import { useState } from "react";
import type { GiftCard as GiftCardType } from "../types";

function formatPrice(price: number | null, currency: string): string {
  if (price == null) return "Цена по запросу";
  const symbol = currency === "RUB" ? "₽" : currency;
  return `${new Intl.NumberFormat("ru-RU").format(price)} ${symbol}`;
}

// мягкие градиенты-плейсхолдеры на случай, если картинка не загрузилась
const PLACEHOLDERS = [
  "from-violet-200 to-rose-200",
  "from-amber-200 to-orange-200",
  "from-sky-200 to-indigo-200",
  "from-emerald-200 to-teal-200",
  "from-fuchsia-200 to-pink-200",
];

export default function GiftCard({
  card,
  inWishlist = false,
  onToggleWishlist,
}: {
  card: GiftCardType;
  inWishlist?: boolean;
  onToggleWishlist?: () => void;
}) {
  const [imgError, setImgError] = useState(false);
  const showImage = card.image_url && !imgError;
  const gradient = PLACEHOLDERS[card.id % PLACEHOLDERS.length];

  return (
    <article className="group flex flex-col overflow-hidden rounded-2xl border border-violet-100 bg-white shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-md motion-reduce:transform-none motion-reduce:transition-none">
      <div className="relative aspect-[4/3] overflow-hidden bg-violet-50">
        {onToggleWishlist && (
          <button
            onClick={onToggleWishlist}
            aria-label={inWishlist ? "Убрать из избранного" : "В избранное"}
            className="absolute right-2 top-2 z-10 flex h-9 w-9 items-center justify-center rounded-full bg-white/90 shadow-sm transition hover:bg-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
          >
            <svg
              viewBox="0 0 24 24"
              className="h-5 w-5"
              fill={inWishlist ? "#e11d48" : "none"}
              stroke={inWishlist ? "#e11d48" : "#64748b"}
              strokeWidth="2"
            >
              <path d="M12 21s-7-4.35-9.5-8.5C1 9 2.5 5.5 6 5.5c2 0 3.2 1.2 4 2.3.8-1.1 2-2.3 4-2.3 3.5 0 5 3.5 3.5 7-2.5 4.15-9.5 8.5-9.5 8.5z" />
            </svg>
          </button>
        )}
        {showImage ? (
          <img
            src={card.image_url!}
            alt={card.title}
            loading="lazy"
            onError={() => setImgError(true)}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105 motion-reduce:transform-none"
          />
        ) : (
          <div
            className={`flex h-full w-full items-center justify-center bg-gradient-to-br ${gradient}`}
          >
            <span className="select-none text-5xl font-semibold text-white/80">
              {card.title.charAt(0)}
            </span>
          </div>
        )}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-4">
        <h3 className="text-base font-semibold leading-snug text-violet-950">
          {card.title}
        </h3>

        {card.reason && (
          <p className="text-sm leading-relaxed text-slate-600">{card.reason}</p>
        )}

        <div className="mt-auto flex items-center justify-between gap-3 pt-2">
          <span className="text-lg font-bold text-violet-700">
            {formatPrice(card.price, card.currency)}
          </span>
          <a
            href={card.product_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center rounded-full bg-violet-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-violet-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600"
          >
            Купить
          </a>
        </div>
      </div>
    </article>
  );
}
