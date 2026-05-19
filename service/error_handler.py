
"""全局错误处理装饰器，自动捕获异常并记录日志"""
import functools, traceback
from service.logger import get_logger

_log = get_logger()

def safe_call(default_return=None, show_traceback=False):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                _log.error(f"函数 {func.__name__} 发生异常: {e}")
                if show_traceback:
                    _log.error(traceback.format_exc())
                return default_return
        return wrapper
    return decorator
