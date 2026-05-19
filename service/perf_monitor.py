
"""性能监控：累计统计与报告生成"""
import time, functools
from collections import defaultdict

_STATS = defaultdict(lambda: {'count': 0, 'total': 0.0, 'max': 0.0, 'min': float('inf')})

def timeit(func):
    """计时装饰器，记录每次调用"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        s = _STATS[func.__name__]
        s['count'] += 1
        s['total'] += elapsed
        s['max'] = max(s['max'], elapsed)
        s['min'] = min(s['min'], elapsed)
        return result
    return wrapper

def get_perf_report():
    if not _STATS:
        return "暂无性能数据"
    lines = ["函数性能统计：",
             "{:<25} {:>6} {:>10} {:>10} {:>10}".format("函数名", "次数", "总耗时(s)", "平均(s)", "最慢(s)")]
    for name, s in sorted(_STATS.items(), key=lambda x: x[1]['total'], reverse=True):
        avg = s['total'] / s['count'] if s['count'] else 0
        lines.append("{:<25} {:>6} {:>10.4f} {:>10.4f} {:>10.4f}".format(name, s['count'], s['total'], avg, s['max']))
    return '\n'.join(lines)

def reset_stats():
    _STATS.clear()
