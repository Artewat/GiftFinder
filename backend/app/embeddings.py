from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.config import settings


@lru_cache(maxsize=1)
def _get_model() -> SentenceTransformer:
    # грузится при первом вызове, НЕ при импорте модуля
    return SentenceTransformer(settings.embedding_model, device="cpu")


def _embed(text: str) -> list[float]:
    return _get_model().encode(text, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    return _embed(f"query: {text}")


def embed_passage(text: str) -> list[float]:
    return _embed(f"passage: {text}")


def embed_passages(texts: list[str]) -> list[list[float]]:
    prefixed = [f"passage: {t}" for t in texts]
    vectors = _get_model().encode(prefixed, normalize_embeddings=True, batch_size=64)
    return [v.tolist() for v in vectors]
