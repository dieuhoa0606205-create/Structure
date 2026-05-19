
"""应用配置管理：保存/加载用户偏好设置"""
import json, os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.json')

DEFAULT_CONFIG = {
    "mode": "basic",
    "last_used_params": {},
    "cache_max_age_hours": 1,
    "log_level": "INFO"
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return {**DEFAULT_CONFIG, **json.load(f)}
        except:
            pass
    return DEFAULT_CONFIG.copy()

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_setting(key, default=None):
    config = load_config()
    return config.get(key, default)
