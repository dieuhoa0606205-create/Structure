
"""增强日志：文件轮转 + 多级输出"""
import logging, os
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')

def setup_logger(name='AeroStruct', max_bytes=5*1024*1024, backup_count=3):
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    fh = RotatingFileHandler(os.path.join(LOG_DIR, 'app.log'), maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger

_logger = setup_logger()

def get_logger():
    return _logger

class StreamlitLogHandler(logging.Handler):
    """将日志同时发送到 Streamlit 界面"""
    def emit(self, record):
        try:
            import streamlit as st
            if 'log_messages' not in st.session_state:
                st.session_state['log_messages'] = []
            st.session_state['log_messages'].append(self.format(record))
        except:
            pass
