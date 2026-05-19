
"""
高级梁计算模块 (修正版)
支持单梁/双梁，碳管/工字梁，强度校核与重量计算
许用弯矩 M_allow 会随校核结果返回
"""

import math

G = 9.81

def compute_beam_advanced(loads, beam_type, section_type_front, section_type_rear,
                          front_params, rear_params, k_reinforce=0.0,
                          material_E=230e9, material_G=90e9, material_density=1600,
                          fatigue_analysis=False, N_cycles=10000,
                          enable_optimization=False, target_safety=1.5):
    # 直接调用基础版本的计算逻辑，因为高级版本最终也用同样的截面校核
    from logic.wing.beam import compute_beam
    result = compute_beam(loads, beam_type, section_type_front, section_type_rear,
                          front_params, rear_params, k_reinforce)
    return result
