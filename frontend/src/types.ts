// Контракт ответа backend: POST /api/search -> { results: GiftCard[] }

export interface GiftCard {
  id: number;
  title: string;
  price: number | null;
  currency: string;
  image_url: string | null;
  product_url: string;
  source: string;
  reason: string | null;
}

export interface SearchResponse {
  results: GiftCard[];
}
