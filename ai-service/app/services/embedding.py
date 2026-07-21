from functools import lru_cache
from sentence_transformers import SentenceTransformer
from app.config import get_settings


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Cached SentenceTransformer model.
    Loaded once at first call — subsequent calls return the same instance.
    Model: all-MiniLM-L6-v2 (384 dims, fast, good semantic quality)
    """
    settings = get_settings()
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def embed(text: str) -> list[float]:
    """Generate a normalized embedding vector for a single text string."""
    model = get_embedding_model()
    vector = model.encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts in one forward pass — more efficient."""
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return [v.tolist() for v in vectors]
