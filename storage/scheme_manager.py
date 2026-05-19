
"""
增强版方案管理模块 (稳定版)
提供方案保存/加载、对比、导出、批量处理、差异报告等功能
"""

import json
import os
import time
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any
import streamlit as st
import pandas as pd

DEFAULT_EXPORT_DIR = "exported_schemes"

def create_export_folder(folder_name: str = DEFAULT_EXPORT_DIR) -> str:
    """在程序所在目录创建导出子文件夹，返回文件夹路径"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(base_dir)
    export_dir = os.path.join(project_root, folder_name)
    os.makedirs(export_dir, exist_ok=True)
    return export_dir

def save_scheme(params: Dict[str, Any], filename: Optional[str] = None) -> str:
    """将参数字典保存为 JSON 文件，返回文件路径"""
    export_dir = create_export_folder()
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scheme_{timestamp}.json"
    filepath = os.path.join(export_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(params, f, indent=2, ensure_ascii=False)
    return filepath

def load_scheme(filepath: str) -> Optional[Dict[str, Any]]:
    """从 JSON 文件加载方案，返回参数字典"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"加载方案失败: {e}")
        return None

def load_scheme_from_uploaded(file) -> Optional[Dict[str, Any]]:
    """从上传的文件对象加载方案"""
    try:
        content = file.read().decode('utf-8')
        return json.loads(content)
    except Exception as e:
        st.error(f"方案文件解析失败: {e}")
        return None

def apply_scheme(params):
    """将方案参数写入临时文件，触发页面重新运行以更新控件"""
    import tempfile, json
    tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    json.dump(params, tmp)
    tmp.close()
    st.session_state['_pending_scheme_file'] = tmp.name
    st.success("方案已加载，页面即将刷新。")
    st.rerun()

def export_scheme_to_folder(scheme: Dict[str, Any], folder_path: str, prefix: str = ""):
    """将单个方案导出为 JSON 和 Excel 报告到指定文件夹"""
    json_name = f"{prefix}scheme.json" if prefix else "scheme.json"
    json_path = os.path.join(folder_path, json_name)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(scheme, f, indent=2, ensure_ascii=False)

    if 'components' in scheme:
        try:
            df = pd.DataFrame({
                '部件': list(scheme['components'].keys()),
                '重量 (N)': list(scheme['components'].values()),
                '重量 (kg)': [w / 9.81 for w in scheme['components'].values()],
                '占比 (%)': [w / scheme.get('W_struct', 1) * 100 for w in scheme['components'].values()]
            })
            xlsx_name = f"{prefix}report.xlsx" if prefix else "report.xlsx"
            xlsx_path = os.path.join(folder_path, xlsx_name)
            df.to_excel(xlsx_path, index=False)
        except Exception as e:
            st.warning(f"生成 Excel 报告失败: {e}")

def batch_export_schemes(schemes: List[Dict[str, Any]], folder_name: str = "batch_export"):
    """批量导出多个方案到以时间戳命名的文件夹中"""
    export_dir = create_export_folder(folder_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_folder = os.path.join(export_dir, f"batch_{timestamp}")
    os.makedirs(batch_folder, exist_ok=True)
    for i, scheme in enumerate(schemes):
        prefix = f"scheme_{i+1}_"
        export_scheme_to_folder(scheme, batch_folder, prefix)
    summary_data = []
    for i, scheme in enumerate(schemes):
        summary_data.append({
            '方案编号': i + 1,
            '起飞重量 (N)': scheme.get('WTO', ''),
            '结构总重 (N)': scheme.get('W_struct', ''),
            '结构占比 (%)': scheme.get('W_struct', 0) / scheme.get('WTO', 1) * 100 if scheme.get('WTO') else '',
            '弯曲通过': scheme.get('beam', {}).get('bend_ok', ''),
            '剪切通过': scheme.get('beam', {}).get('shear_ok', ''),
            '蒙皮通过': scheme.get('skin', {}).get('shear_ok', '')
        })
    summary_df = pd.DataFrame(summary_data)
    summary_path = os.path.join(batch_folder, "summary.xlsx")
    summary_df.to_excel(summary_path, index=False)
    return batch_folder

def compare_schemes_detailed(current, loaded):
    """精简对比报告：只展示总体重量、重量分布、强度校核"""
    lines = ["## 方案对比报告", ""]
    lines.append(f"**当前方案** vs **加载方案**")
    lines.append("")

    # 1. 总体参数对比（只选取最重要的几个）
    key_params = ['WTO', 'kL', 'b', 'cw', 'V_cruise', 'k_sec']
    lines.append("### 总体参数")
    lines.append("| 参数 | 当前方案 | 加载方案 |")
    lines.append("|------|----------|----------|")
    for key in key_params:
        v1 = current.get(key, 'N/A')
        v2 = loaded.get(key, 'N/A')
        lines.append(f"| {key} | {v1} | {v2} |")

    # 2. 重量汇总对比
    lines.append("")
    lines.append("### 重量汇总")
    lines.append("| 项目 | 当前方案 | 加载方案 |")
    lines.append("|------|----------|----------|")
    for key in ['W_struct', 'W_wing', 'W_remain']:
        v1 = current.get(key, 'N/A')
        v2 = loaded.get(key, 'N/A')
        if isinstance(v1, float): v1 = f"{v1:.2f}"
        if isinstance(v2, float): v2 = f"{v2:.2f}"
        lines.append(f"| {key} | {v1} | {v2} |")

    # 3. 重量分解对比（如果有）
    if 'components' in current and 'components' in loaded:
        lines.append("")
        lines.append("### 重量分解")
        lines.append("| 部件 | 当前方案 (kg) | 加载方案 (kg) |")
        lines.append("|------|---------------|---------------|")
        for ck in sorted(set(current['components'].keys()) | set(loaded['components'].keys())):
            w1 = current['components'].get(ck, 0) / 9.81
            w2 = loaded['components'].get(ck, 0) / 9.81
            lines.append(f"| {ck} | {w1:.3f} | {w2:.3f} |")
    elif 'components' in current:
        lines.append("")
        lines.append("### 重量分解 (仅当前方案)")
        lines.append("| 部件 | 当前方案 (kg) |")
        lines.append("|------|---------------|")
        for ck, w in current['components'].items():
            lines.append(f"| {ck} | {w/9.81:.3f} |")

    # 4. 强度校核对比（如果双方都有 beam 数据）
    beam_cur = current.get('beam', {})
    beam_load = loaded.get('beam', {})
    skin_cur = current.get('skin', {})
    skin_load = loaded.get('skin', {})
    if beam_cur or beam_load:
        lines.append("")
        lines.append("### 强度校核")
        lines.append("| 项目 | 当前方案 | 加载方案 |")
        lines.append("|------|----------|----------|")
        for item, cur_val, load_val in [
            ('主梁弯曲通过', beam_cur.get('bend_ok', 'N/A'), beam_load.get('bend_ok', 'N/A')),
            ('主梁剪切通过', beam_cur.get('shear_ok', 'N/A'), beam_load.get('shear_ok', 'N/A')),
            ('蒙皮剪切通过', skin_cur.get('shear_ok', 'N/A'), skin_load.get('shear_ok', 'N/A'))
        ]:
            lines.append(f"| {item} | {cur_val} | {load_val} |")

    return '\n'.join(lines)
def generate_summary_table(schemes: List[Dict[str, Any]]) -> pd.DataFrame:
    """从多个方案生成汇总对比 DataFrame"""
    data = []
    for i, s in enumerate(schemes):
        data.append({
            '方案编号': i + 1,
            '起飞重量 (N)': s.get('WTO', ''),
            '结构总重 (N)': s.get('W_struct', ''),
            '结构占比 (%)': s.get('W_struct', 0) / s.get('WTO', 1) * 100 if s.get('WTO') else '',
            '机翼重量 (N)': s.get('W_wing', ''),
            '弯曲通过': s.get('beam', {}).get('bend_ok', ''),
            '剪切通过': s.get('beam', {}).get('shear_ok', ''),
        })
    return pd.DataFrame(data)

def list_saved_schemes(folder_path: Optional[str] = None) -> List[str]:
    """列出导出文件夹中所有的方案 JSON 文件"""
    if folder_path is None:
        folder_path = create_export_folder()
    if not os.path.exists(folder_path):
        return []
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.json')]
    files.sort(key=os.path.getmtime, reverse=True)
    return files

def delete_scheme(filepath: str) -> bool:
    """删除指定方案文件"""
    try:
        os.remove(filepath)
        return True
    except Exception as e:
        st.error(f"删除失败: {e}")
        return False

def get_scheme_info(filepath: str) -> Dict[str, Any]:
    """获取方案文件的基本信息"""
    stat = os.stat(filepath)
    return {
        'name': os.path.basename(filepath),
        'size': stat.st_size,
        'mtime': datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    }
