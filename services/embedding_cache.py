import time
import gc

_TTL = 300

class EmbeddingCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache = {}
        self._max_size = 200

    def get(self, key):
        entry = self._cache.get(key)
        if entry is not None:
            entry['last_access'] = time.time()
            return entry['embedding']
        return None

    def put(self, key, embedding):
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v['created'] > _TTL]
        for k in expired:
            del self._cache[k]
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k]['last_access'])
            del self._cache[oldest]
        self._cache[key] = {
            'embedding': embedding,
            'last_access': now,
            'created': now
        }

    def clear(self):
        self._cache.clear()
        gc.collect()

    def size(self):
        return len(self._cache)
