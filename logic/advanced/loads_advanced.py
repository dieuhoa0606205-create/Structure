
"""
高级载荷计算模块 (修正版)
直接调用基础版本的 compute_design_loads，确保两种模式计算结果一致
"""

import math
import numpy as np
from logic.loads import compute_design_loads


def compute_design_loads_advanced(WTO, kL, nvtol, fs, b, bfuse=0, r_env=0, D_rotor=0, delta=0,
                                  cw=0, rho=1.225, V_cruise=10, Cm0=-0.05,
                                  W_payload=0, W_cargo_width=0, use_elliptic=False):
    """
    高级载荷计算，内部调用基础版本的 compute_design_loads，确保核心结果一致。
    未来可在此函数基础上增加高级的精细化修正。
    """
    # 直接调用基础版本的载荷计算
    base_result = compute_design_loads(
        WTO=WTO, kL=kL, nvtol=nvtol, fs=fs,
        b=b, r_env=r_env, D_rotor=D_rotor, delta=delta,
        cw=cw, rho=rho, V_cruise=V_cruise, Cm0=Cm0,
        W_payload=W_payload, W_cargo_width=W_cargo_width
    )

    # 可在此处增加高级的精细化处理（如椭圆分布、突风等）
    # 目前直接返回基础结果，保证两种模式结果一致

    return base_result
