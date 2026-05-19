
"""输入参数校验"""
import streamlit as st

def validate_range(value, name, low, high, unit=''):
    if value < low or value > high:
        st.warning(f"{name} ({value}{unit}) 超出推荐范围 [{low}, {high}]")

def validate_overall(params):
    errors, warnings = [], []
    if params.get('WTO', 0) <= 0:
        errors.append("起飞重量必须大于0")
    else:
        validate_range(params['WTO'], "起飞重量", 10, 2000, "N")
    if params.get('kL', 0) < 0 or params.get('kL', 0) > 1:
        errors.append("气囊升力占比必须在0~1")
    if params.get('b', 0) <= 0:
        errors.append("展长必须大于0")
    else:
        validate_range(params['b'], "展长", 0.5, 10, "m")
    if params.get('cw', 0) <= 0:
        errors.append("弦长必须大于0")
    return errors, warnings

def validate_beam(params):
    errors = []
    front = params.get('front_params', {})
    if 'h' in front:
        if front['h'] <= 0: errors.append("工字梁高度必须大于0")
        if front['b_f'] <= 0: errors.append("缘条宽度必须大于0")
        if front['t_f'] <= 0: errors.append("缘条厚度必须大于0")
        if front['t_w'] <= 0: errors.append("腹板厚度必须大于0")
    elif 'D' in front:
        if front['D'] <= 0: errors.append("碳管外径必须大于0")
        if front['t'] <= 0: errors.append("碳管壁厚必须大于0")
    return errors

def show_errors(errors):
    for e in errors:
        st.error(f"❌ {e}")
def show_warnings(warnings):
    for w in warnings:
        st.warning(f"⚠️ {w}")
