/** @type {import('tailwindcss').Config} */

// Семантические токены завязаны на CSS-переменные (каналы RGB в index.css),
// поэтому работает и прозрачность: bg-surface/80, text-fg/60 и т.п.
// Значение <alpha-value> подставляет Tailwind под каждый модификатор /NN.
const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: token("canvas"),               // фон страницы
        surface: token("surface"),             // карточки, навбар, поля, модалки
        "surface-muted": token("surface-muted"),   // подложки, плейсхолдер картинки
        "surface-accent": token("surface-accent"), // чипы, бейджи, hover-фон
        edge: token("edge"),                   // рамки
        "edge-strong": token("edge-strong"),   // рамки/наведение сильнее
        fg: token("fg"),                       // заголовки, основной текст
        "fg-muted": token("fg-muted"),         // вторичный текст
        "fg-subtle": token("fg-subtle"),       // подписи, подсказки
        "fg-faint": token("fg-faint"),         // очень тусклый (зачёркнутая цена)
        link: token("link"),                   // ссылки, цены на поверхности
        accent: token("accent"),               // светлый бренд-акцент (лейблы)
        sale: token("sale"),                   // цена со скидкой, текст бейджа
        "sale-bg": token("sale-bg"),           // фон бейджа скидки
        danger: token("danger"),               // заголовок ошибки
        "danger-body": token("danger-body"),   // текст ошибки
        "danger-bg": token("danger-bg"),
        "danger-edge": token("danger-edge"),
        warn: token("warn"),                   // заголовок предупреждения (лимит)
        "warn-body": token("warn-body"),
        "warn-bg": token("warn-bg"),
        "warn-edge": token("warn-edge"),
      },
    },
  },
  plugins: [],
};
