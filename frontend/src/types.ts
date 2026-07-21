// Контракт ответа backend: POST /api/search -> { results: GiftCard[] }

export interface GiftCard {
  id: number;
  title: string;
  price: number | null;      // основная (старая) цена
  discount_percent: number;  // 0 — скидки нет
  currency: string;
  image_url: string | null;
  product_url: string;
  source: string;
  reason: string | null;
}

export interface SearchResponse {
  results: GiftCard[];
}
