
"""
载荷计算模块
根据总体参数计算根部设计弯矩、剪力及气动扭矩
"""

import math


def compute_design_loads(WTO, kL, nvtol, fs, b, r_env, D_rotor, delta,
                         cw, rho, V_cruise, Cm0, W_payload, W_cargo_width):
    """
    计算根部设计载荷（中心线截面）

    Args:
        WTO: 起飞重量 (N)
        kL: 气囊浮力占比 (0~1)
        nvtol: 垂飞过载系数
        fs: 安全系数
        b: 机翼总展长，两气囊内侧距离 (m)
        r_env: 气囊短半轴半径 (m)
        D_rotor: 旋翼直径 (m)
        delta: 安全距离 (m)
        cw: 外翼弦长 (m)
        rho: 空气密度 (kg/m³)
        V_cruise: 巡航速度 (m/s)
        Cm0: 翼型零升力矩系数
        W_payload: 载货仓预期载重 (N)
        W_cargo_width: 载货仓展向宽度 (m)

    Returns:
        dict: 包含以下键值
            - M_root: 根部设计弯矩 (N·m)
            - V_root: 根部设计剪力 (N)
            - T_aero: 气动扭矩 (N·m)
            - yR: 旋翼展向位置 (m)
            - q_cruise: 巡航动压 (Pa)
    """
    yR = b/2 + r_env + D_rotor/2 + delta
    M_env = (kL * WTO / 2) * (b / 2)
    M_rotor = -((1 - kL) * WTO / 2) * yR
    M_payload = -(W_payload / 2) * (W_cargo_width / 2)
    M_root = nvtol * fs * abs(M_env + M_rotor + M_payload)
    V_root = nvtol * fs * WTO / 2
    S_wing = b * cw
    q_cruise = 0.5 * rho * V_cruise**2
    T_aero = q_cruise * S_wing * cw * abs(Cm0)
    return {
        'M_root': M_root,
        'V_root': V_root,
        'T_aero': T_aero,
        'yR': yR,
        'q_cruise': q_cruise
    }
