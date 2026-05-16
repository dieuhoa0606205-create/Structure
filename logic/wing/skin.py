
"""
蒙皮计算模块
重量计算与简单剪切稳定性校核
"""

import math

G = 9.81


def compute_skin(b, cw, tmax, t_skin, rho_skin, E_skin, tau_allow, T, d_rib):
    """
    计算蒙皮重量与剪切稳定性

    Args:
        b: 机翼展长 (m)
        cw: 弦长 (m)
        tmax: 翼型最大厚度 (m)
        t_skin: 蒙皮厚度 (m)
        rho_skin: 蒙皮材料密度 (kg/m³)
        E_skin: 蒙皮材料弹性模量 (Pa)
        tau_allow: 蒙皮许用剪应力 (Pa)
        T: 气动扭矩 (N·m)
        d_rib: 翼肋间距 (m)

    Returns:
        dict: 包含蒙皮重量、应力、临界应力及校核结果
    """
    S_airfoil = 2.0 * cw + 0.5 * tmax
    A_skin = S_airfoil * b
    W_skin = rho_skin * A_skin * t_skin * G
    Omega = 0.7 * cw * tmax
    tau_skin = T / (2 * Omega * t_skin) if Omega > 0 and t_skin > 0 else 0
    tau_cr = 5.0 * E_skin * (t_skin / d_rib) ** 2 if d_rib > 0 and t_skin > 0 else float('inf')
    shear_ok = tau_skin <= tau_allow and tau_skin <= tau_cr
    return {
        'W_skin': W_skin,
        'A_skin': A_skin,
        'S_airfoil': S_airfoil,
        'tau_skin': tau_skin,
        'tau_cr': tau_cr,
        'shear_ok': shear_ok
    }
