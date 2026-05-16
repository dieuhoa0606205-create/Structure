
"""
配置参数管理 (增强版)
支持保存/加载、版本标记、合并、校验
"""

import json
import os
import copy
import datetime

def save_params_to_json(params, filepath):
    """保存参数到 JSON 文件，自动添加时间戳和版本号"""
    data = {
        'version': '2.0',
        'saved_at': datetime.datetime.now().isoformat(),
        'params': copy.deepcopy(params)
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_params_from_json(filepath):
    """从 JSON 文件加载参数，返回 (params, metadata) 或 (None, {})"""
    if not os.path.exists(filepath):
        return None, {}
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('params', data), {'version': data.get('version'), 'saved_at': data.get('saved_at')}

def merge_params(base, override):
    """将 override 中的参数合并到 base 中，返回新字典"""
    merged = copy.deepcopy(base)
    merged.update(override)
    return merged

def validate_params(params):
    """简单的参数范围校验，返回错误列表"""
    errors = []
    if params.get('WTO', 0) <= 0:
        errors.append("起飞重量必须为正")
    if params.get('kL', 0) < 0 or params.get('kL', 0) > 1:
        errors.append("气囊升力占比必须在 0~1")
    if params.get('b', 0) <= 0:
        errors.append("展长必须为正")
    return errors
