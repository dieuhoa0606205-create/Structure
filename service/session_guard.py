
"""
会话守护模块：自动超时退出、手动退出、清理缓存
"""
import time
import threading
import os
import sys
import streamlit as st
from service.cache_utils import clear_all_cache

# 时间戳文件路径（放在项目根目录下）
TIMESTAMP_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.last_activity')

# 默认超时时间（秒）
DEFAULT_TIMEOUT = 1800  # 30 分钟

def update_activity():
    """更新最后活动时间戳（每次脚本运行时调用）"""
    try:
        with open(TIMESTAMP_FILE, 'w') as f:
            f.write(str(time.time()))
    except:
        pass

def cleanup_and_exit():
    """清理缓存并退出进程"""
    clear_all_cache()
    # 删除时间戳文件
    try:
        os.remove(TIMESTAMP_FILE)
    except:
        pass
    # 尝试停止 Streamlit 服务器
    try:
        # 对于较新版本的 Streamlit，可以使用 runtime 模块
        from streamlit.runtime.scriptrunner import script_run_ctx
        ctx = script_run_ctx.get_script_run_ctx()
        if ctx:
            # 标记脚本应该停止
            ctx.stop()
    except:
        pass
    # 强制退出
    os._exit(0)

def _watchdog(timeout_seconds):
    """后台线程：定期检查最后活动时间，超时则退出"""
    while True:
        time.sleep(30)  # 每30秒检查一次
        try:
            if os.path.exists(TIMESTAMP_FILE):
                with open(TIMESTAMP_FILE, 'r') as f:
                    last = float(f.read().strip())
                if time.time() - last > timeout_seconds:
                    cleanup_and_exit()
        except:
            pass

def start_watchdog(timeout_seconds=DEFAULT_TIMEOUT):
    """启动守护线程（在 main.py 开头调用一次）"""
    t = threading.Thread(target=_watchdog, args=(timeout_seconds,), daemon=True)
    t.start()

def show_exit_button():
    """在侧边栏显示退出按钮"""
    if st.sidebar.button("🚪 退出程序并清理缓存"):
        cleanup_and_exit()
