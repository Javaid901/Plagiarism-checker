import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

try:
    from sentence_transformers import SentenceTransformer
    _HAS_TRANSFORMERS = True
except ImportError:
    _HAS_TRANSFORMERS = False

from .embedding_cache import EmbeddingCache

class SemanticSimilarity:
    _instance = None

    def __new__(cls, model_name='all-MiniLM-L6-v2'):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_name='all-MiniLM-L6-v2'):
        if self._initialized:
            return
        self._initialized = True
        self._model_name = model_name
        self._model = None
        self.cache = EmbeddingCache()

    @property
    def model(self):
        if self._model is None and _HAS_TRANSFORMERS:
            try:
                self._model = SentenceTransformer(self._model_name)
            except Exception:
                pass
        return self._model

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        if self.model is None:
            return None
        to_encode = []
        indices = []
        results = [None] * len(texts)
        for i, t in enumerate(texts):
            cached = self.cache.get(t)
            if cached is not None:
                results[i] = cached
            else:
                to_encode.append(t)
                indices.append(i)
        if to_encode:
            try:
                encoded = self.model.encode(to_encode, show_progress_bar=False, normalize_embeddings=True)
                for idx, t, emb in zip(indices, to_encode, encoded):
                    self.cache.put(t, emb)
                    results[idx] = emb
            except Exception:
                return None
        return np.array(results) if any(r is not None for r in results) else None

    def cosine_similarity(self, emb1, emb2):
        if emb1 is None or emb2 is None:
            return None
        emb1 = np.array(emb1).reshape(1, -1)
        emb2 = np.array(emb2).reshape(1, -1)
        return float(cosine_similarity(emb1, emb2)[0][0])

    def sentence_similarity(self, sent1, sent2):
        embs = self.encode([sent1, sent2])
        if embs is None:
            return None
        return self.cosine_similarity(embs[0], embs[1])

    def batch_similarity_matrix(self, sents_a, sents_b):
        embs_a = self.encode(sents_a)
        embs_b = self.encode(sents_b)
        if embs_a is None or embs_b is None:
            return None
        return cosine_similarity(embs_a, embs_b)

    def cleanup(self):
        self.cache.clear()
