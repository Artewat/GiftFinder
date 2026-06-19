import { Link } from "react-router-dom";
import { useAuth } from "../AuthContext";
import NavBar from "../components/NavBar";

const STEPS = [
  {
    n: "1",
    title: "Опишите получателя",
    text: "Кому подарок, по какому поводу, какие увлечения и бюджет — простыми словами, как другу.",
  },
  {
    n: "2",
    title: "ИИ понимает запрос",
    text: "Ассистент выделяет повод, интересы и бюджет и ищет в каталоге по смыслу, а не по точным словам.",
  },
  {
    n: "3",
    title: "Выбираете и покупаете",
    text: "Получаете карточки с ценой, ссылкой на магазин и объяснением, почему это удачный подарок.",
  },
];

const FEATURES = [
  {
    icon: "🤖",
    title: "Понимает по смыслу",
    text: "Не просто поиск по словам — ассистент учитывает повод, интересы и бюджет получателя.",
  },
  {
    icon: "💬",
    title: "Объясняет выбор",
    text: "Каждая идея сопровождается коротким обоснованием, почему она подойдёт именно этому человеку.",
  },
  {
    icon: "🛍️",
    title: "Из разных источников",
    text: "Каталог собирается из подключаемых магазинов и обновляется автоматически каждую неделю.",
  },
  {
    icon: "💸",
    title: "Уважает бюджет",
    text: "Укажите вилку цены — и в подборку попадут только варианты, которые в неё укладываются.",
  },
  {
    icon: "❤️",
    title: "Избранное под рукой",
    text: "Сохраняйте понравившиеся идеи в список желаемого — они остаются, даже если товар ушёл из продажи.",
  },
  {
    icon: "⚡",
    title: "Быстрый результат",
    text: "Опишите задачу одной фразой — и сразу получите готовые идеи с обоснованием и ценой.",
  },
];

const STATS = [
  { value: "1 фраза", label: "вместо часов поиска по магазинам" },
  { value: "до 12", label: "идей с обоснованием за один запрос" },
  { value: "5 / день", label: "бесплатных подборов без оплаты" },
  { value: "24/7", label: "ассистент всегда на связи" },
];

const OCCASIONS = [
  "День рождения",
  "Новый год",
  "8 Марта",
  "23 Февраля",
  "Юбилей",
  "Свадьба",
  "Новоселье",
  "Повышение",
  "Годовщина",
  "Просто так",
];

const EXAMPLES = [
  "Папе-рыбаку до 3000 ₽",
  "Подруге, которая любит готовить, 1000–3500 ₽",
  "Коллеге на Новый год недорого",
  "Настольная игра для компании друзей",
  "Маме на юбилей, что-то для уюта",
  "Подростку, увлекается музыкой",
];

const FAQ = [
  {
    q: "Это бесплатно?",
    a: "Да. На бесплатном тарифе доступно 5 подборов в день. Если нужно больше — есть premium с безлимитным поиском.",
  },
  {
    q: "Откуда берутся товары?",
    a: "Каталог собирается из подключаемых магазинов-источников и автоматически обновляется по расписанию, поэтому идеи остаются актуальными.",
  },
  {
    q: "Как ассистент понимает, что я хочу?",
    a: "Он анализирует повод, интересы и бюджет из вашего описания, ищет подходящие товары по смыслу и объясняет, почему каждый из них подойдёт.",
  },
  {
    q: "Нужна ли регистрация?",
    a: "Для подбора — да, регистрация быстрая, по email. Так мы храним ваше избранное и считаем дневной лимит подборов.",
  },
];

export default function HomePage() {
  const { user } = useAuth();
  // Залогинен — сразу к подбору; иначе сначала регистрация.
  const ctaTarget = user ? "/search" : "/register";

  return (
    <div className="min-h-screen bg-[#F5F3FA] text-violet-950">
      {/* Навигация */}
      <NavBar active="home" />

      {/* Hero */}
      <header className="relative overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-x-0 -top-24 mx-auto h-72 max-w-3xl rounded-full bg-gradient-to-br from-violet-300 via-fuchsia-200 to-rose-200 opacity-50 blur-3xl"
        />
        <div className="relative mx-auto max-w-3xl px-4 pb-16 pt-12 text-center sm:pb-20 sm:pt-20">
          <p className="mb-3 inline-block rounded-full border border-violet-200 bg-white/70 px-4 py-1 text-sm font-medium text-violet-600 backdrop-blur">
            Подарок за пару минут — с ИИ-ассистентом
          </p>
          <h1 className="text-4xl font-bold leading-tight tracking-tight sm:text-6xl">
            Никогда не знаете,
            <br />
            <span className="bg-gradient-to-r from-violet-600 to-fuchsia-500 bg-clip-text text-transparent">
              что подарить?
            </span>
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-lg text-slate-600">
            Опишите получателя, повод и бюджет — умный ассистент подберёт идеи
            подарков, объяснит выбор и покажет, где их купить.
          </p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              to={ctaTarget}
              className="w-full rounded-full bg-violet-600 px-8 py-4 text-center text-base font-semibold text-white shadow-lg shadow-violet-200 transition-all hover:-translate-y-0.5 hover:bg-violet-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600 motion-reduce:transform-none sm:w-auto"
            >
              Начать подбор
            </Link>
            <span className="text-sm text-slate-500">
              Бесплатно — 5 подборов в день
            </span>
          </div>
        </div>
      </header>

      {/* Полоса статистики */}
      <section className="mx-auto -mt-4 max-w-5xl px-4 pb-4">
        <div className="grid grid-cols-2 gap-3 rounded-3xl border border-violet-100 bg-white/70 p-6 backdrop-blur sm:grid-cols-4 sm:gap-6">
          {STATS.map((s) => (
            <div key={s.label} className="text-center">
              <div className="text-2xl font-bold text-violet-700 sm:text-3xl">
                {s.value}
              </div>
              <div className="mt-1 text-xs leading-snug text-slate-500 sm:text-sm">
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Как это работает */}
      <section className="mx-auto max-w-5xl px-4 py-12 sm:py-16">
        <h2 className="text-center text-2xl font-bold tracking-tight sm:text-3xl">
          Как это работает
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
          Три простых шага — от свободного описания до готового списка идей.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {STEPS.map((s) => (
            <div
              key={s.n}
              className="rounded-2xl border border-violet-100 bg-white p-6 shadow-sm"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-violet-600 text-lg font-bold text-white">
                {s.n}
              </div>
              <h3 className="mt-4 text-lg font-semibold text-violet-950">
                {s.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {s.text}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Преимущества */}
      <section className="mx-auto max-w-5xl px-4 pb-12 sm:pb-16">
        <h2 className="text-center text-2xl font-bold tracking-tight sm:text-3xl">
          Почему GiftFinder
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
          Не каталог с фильтрами, а ассистент, который думает о подарке вместе с
          вами.
        </p>
        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-violet-100 bg-white p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-violet-50 text-2xl">
                {f.icon}
              </div>
              <h3 className="mt-4 text-base font-semibold text-violet-950">
                {f.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-slate-600">
                {f.text}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Поводы */}
      <section className="mx-auto max-w-5xl px-4 pb-12 sm:pb-16">
        <div className="rounded-3xl border border-violet-100 bg-white/60 px-6 py-10 sm:px-10">
          <h2 className="text-center text-2xl font-bold tracking-tight sm:text-3xl">
            Подойдёт для любого повода
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
            День рождения, праздник или просто хочется порадовать близкого — опишите
            ситуацию своими словами.
          </p>
          <div className="mt-7 flex flex-wrap justify-center gap-2.5">
            {OCCASIONS.map((o) => (
              <span
                key={o}
                className="rounded-full border border-violet-200 bg-white px-4 py-1.5 text-sm font-medium text-violet-700"
              >
                {o}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Примеры запросов */}
      <section className="mx-auto max-w-5xl px-4 pb-12 sm:pb-16">
        <h2 className="text-center text-2xl font-bold tracking-tight sm:text-3xl">
          Примеры запросов
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-center text-slate-600">
          Пишите так, как рассказали бы другу — ассистент поймёт.
        </p>
        <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {EXAMPLES.map((ex) => (
            <Link
              key={ex}
              to={ctaTarget}
              className="group flex items-center gap-3 rounded-2xl border border-violet-100 bg-white p-4 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-violet-300 hover:shadow-md focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-violet-600 motion-reduce:transform-none"
            >
              <span className="text-lg">🔍</span>
              <span className="text-sm text-violet-950">«{ex}»</span>
              <span className="ml-auto text-violet-400 transition-transform group-hover:translate-x-0.5">
                →
              </span>
            </Link>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-3xl px-4 pb-12 sm:pb-16">
        <h2 className="text-center text-2xl font-bold tracking-tight sm:text-3xl">
          Частые вопросы
        </h2>
        <div className="mt-8 space-y-3">
          {FAQ.map((item) => (
            <details
              key={item.q}
              className="group rounded-2xl border border-violet-100 bg-white p-5 shadow-sm [&_summary::-webkit-details-marker]:hidden"
            >
              <summary className="flex cursor-pointer items-center justify-between gap-4 font-medium text-violet-950">
                {item.q}
                <span className="text-violet-400 transition-transform group-open:rotate-45">
                  +
                </span>
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-slate-600">
                {item.a}
              </p>
            </details>
          ))}
        </div>
      </section>

      {/* CTA-полоса */}
      <section className="mx-auto max-w-5xl px-4 pb-16">
        <div className="rounded-3xl bg-gradient-to-br from-violet-600 to-fuchsia-600 px-6 py-12 text-center text-white sm:py-16">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Готовы найти идеальный подарок?
          </h2>
          <p className="mx-auto mt-3 max-w-md text-violet-100">
            Один запрос — и список идей под вашего получателя уже готов.
          </p>
          <Link
            to={ctaTarget}
            className="mt-7 inline-block rounded-full bg-white px-8 py-4 text-base font-semibold text-violet-700 shadow-lg transition-transform hover:-translate-y-0.5 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white motion-reduce:transform-none"
          >
            Начать подбор
          </Link>
        </div>
      </section>

      {/* Футер */}
      <footer className="border-t border-violet-100 py-8">
        <div className="mx-auto max-w-5xl px-4 text-center text-sm text-slate-500">
          <span className="font-medium text-violet-700">🎁 GiftFinder</span>
          {" — "}умный подбор подарков с ИИ-ассистентом · MVP
        </div>
      </footer>
    </div>
  );
}
