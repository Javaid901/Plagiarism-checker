import time

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
        self._max_size = 10000

    def get(self, key):
        if key in self._cache:
            entry = self._cache[key]
            entry['last_access'] = time.time()
            return entry['embedding']
        return None

    def put(self, key, embedding):
        if len(self._cache) >= self._max_size:
            oldest = min(self._cache.keys(), key=lambda k: self._cache[k]['last_access'])
            del self._cache[oldest]
        self._cache[key] = {
            'embedding': embedding,
            'last_access': time.time(),
            'created': time.time()
        }

    def clear(self):
        self._cache.clear()

    def size(self):
        return len(self._cache)

    def contains(self, key):
        return key in self._cache
