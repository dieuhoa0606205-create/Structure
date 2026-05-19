
"""预加载与预热：导入库、预热核心函数"""
import importlib, time
from service.logger import get_logger

_log = get_logger()

def preload_modules():
    modules = ['numpy', 'pandas', 'matplotlib', 'openpyxl']
    for m in modules:
        try:
            importlib.import_module(m)
            _log.debug(f"预加载成功: {m}")
        except ImportError as e:
            _log.warning(f"预加载失败 {m}: {e}")

def warmup_compute():
    try:
        from logic.loads import compute_design_loads
        _ = compute_design_loads(98, 0.35, 1.3, 1.25, 1.2, 0.4, 0.15, 0.05,
                                 1.2, 1.225, 10, -0.05, 10, 0.2)
        _log.debug("计算函数预热完成")
    except Exception as e:
        _log.warning(f"预热计算函数时发生异常: {e}")

def run_all_preload():
    preload_modules()
    warmup_compute()
