import json
import time

class Cache:

    def __init__(self, path, settings):
        self.settings = settings
        self.cache = dict()
        self.path = path
        try:
            with open(self.path) as f:
                self.cache.update(json.load(f))
        except FileNotFoundError:
            if self.settings.save_cache:
                self.save()

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self.cache, f, indent=4, sort_keys=True)

    def put_cache(self, cache_id, key, dikt):
        if cache_id not in self.cache:
            self.cache[cache_id] = dict()
        self.cache[cache_id][key] = dikt
        dikt['cache_time'] = time.time()
        if self.settings.save_cache:
                self.save()
    
    def get_cache(self, cache_id, key):
        if cache_id not in self.cache:
            return None
        if key in self.cache[cache_id]:
            cache = self.cache[cache_id][key]
            if time.time() - cache['cache_time'] > self.settings.cache_timeout:
                return None
            return cache
        return None
