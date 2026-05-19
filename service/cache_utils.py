
"""多层缓存：内存LRU + 磁盘持久化 + 统计"""
import hashlib, json, os, time, functools
from collections import OrderedDict

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.cache')
_MEM_CACHE = OrderedDict()
_MEM_CACHE_MAXSIZE = 32

def _make_key(func_name, args, kwargs):
    raw = json.dumps({'f': func_name, 'a': args, 'k': kwargs}, sort_keys=True, default=str)
    return hashlib.md5(raw.encode()).hexdigest()

def disk_cache(max_age_sec=3600):
    """磁盘+内存缓存装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = _make_key(func.__name__, args, kwargs)
            if key in _MEM_CACHE:
                return _MEM_CACHE[key]
            os.makedirs(CACHE_DIR, exist_ok=True)
            cache_file = os.path.join(CACHE_DIR, f"{key}.json")
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'r') as f:
                        data = json.load(f)
                    if time.time() - data['t'] < max_age_sec:
                        _MEM_CACHE[key] = data['res']
                        if len(_MEM_CACHE) > _MEM_CACHE_MAXSIZE:
                            _MEM_CACHE.popitem(last=False)
                        return data['res']
                except:
                    pass
            result = func(*args, **kwargs)
            try:
                with open(cache_file, 'w') as f:
                    json.dump({'t': time.time(), 'res': result}, f, default=str)
            except:
                pass
            _MEM_CACHE[key] = result
            if len(_MEM_CACHE) > _MEM_CACHE_MAXSIZE:
                _MEM_CACHE.popitem(last=False)
            return result
        return wrapper
    return decorator

def clear_all_cache():
    import shutil
    _MEM_CACHE.clear()
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
        os.makedirs(CACHE_DIR)

def cache_stats():
    disk_count = len(os.listdir(CACHE_DIR)) if os.path.exists(CACHE_DIR) else 0
    return {'memory_entries': len(_MEM_CACHE), 'disk_files': disk_count}
