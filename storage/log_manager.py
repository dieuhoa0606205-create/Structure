
"""
简单的日志管理模块
支持记录信息、警告、错误到文件，并在控制台输出
"""

import datetime
import os

class Logger:
    def __init__(self, log_path='app.log', level='INFO'):
        self.log_path = log_path
        self.level = level

    def _write(self, msg, level):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}][{level}] {msg}"
        try:
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception:
            pass
        print(line)

    def info(self, msg):
        self._write(msg, 'INFO')

    def warning(self, msg):
        self._write(msg, 'WARNING')

    def error(self, msg):
        self._write(msg, 'ERROR')

# 全局默认日志记录器
_logger = Logger()
def get_logger():
    return _logger
