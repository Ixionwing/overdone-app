from functools import lru_cache

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embed_model(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
) -> HuggingFaceEmbedding:
    return HuggingFaceEmbedding(model_name=model_name)


def embed_texts(
    texts: list[str], model_name: str = DEFAULT_EMBEDDING_MODEL
) -> list[list[float]]:
    model = get_embed_model(model_name)
    return [list(vec) for vec in model.get_text_embedding_batch(texts)]


def embed_query(text: str, model_name: str = DEFAULT_EMBEDDING_MODEL) -> list[float]:
    return list(get_embed_model(model_name).get_text_embedding(text))
