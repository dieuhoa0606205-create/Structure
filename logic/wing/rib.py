
"""
翼肋计算模块
包含普通翼肋与加强翼肋的重量计算、简单稳定性校核
"""

import math

G = 9.81


def compute_ribs(tmax, cw, n_rib, t_rib, fill_rib, rho_rib, E_rib,
                 n_rib_rein, t_rib_rein, fill_rib_rein, rho_rib_rein,
                 V_root):
    """
    计算翼肋总重与腹板剪切稳定性

    Args:
        tmax: 翼型最大厚度 (m)
        cw: 外翼弦长 (m)
        n_rib: 普通翼肋数量
        t_rib: 普通翼肋厚度 (m)
        fill_rib: 普通翼肋填充系数
        rho_rib: 普通翼肋材料密度 (kg/m³)
        E_rib: 普通翼肋材料弹性模量 (Pa)
        n_rib_rein: 加强翼肋数量
        t_rib_rein: 加强翼肋厚度 (m)
        fill_rib_rein: 加强翼肋填充系数
        rho_rib_rein: 加强翼肋材料密度 (kg/m³)
        V_root: 根部设计剪力 (N)

    Returns:
        dict: 包含各项重量、截面积及稳定性校核结果
    """
    A_airfoil = 0.68 * tmax * cw
    A_rib_net = A_airfoil * fill_rib
    W_ribs = rho_rib * A_rib_net * t_rib * n_rib * G
    A_rib_rein_net = A_airfoil * fill_rib_rein
    W_ribs_rein = rho_rib_rein * A_rib_rein_net * t_rib_rein * n_rib_rein * G
    W_ribs_total = W_ribs + W_ribs_rein

    n_total = n_rib + n_rib_rein
    t_avg = (n_rib * t_rib + n_rib_rein * t_rib_rein) / n_total if n_total > 0 else 0
    tau_rib = V_root / (n_total * t_avg * tmax) if n_total > 0 and t_avg > 0 else 0
    tau_cr_rib = 5.0 * E_rib * (t_avg / tmax) ** 2 if t_avg > 0 and tmax > 0 else float('inf')
    rib_shear_ok = tau_rib <= tau_cr_rib

    return {
        'W_ribs': W_ribs,
        'W_ribs_rein': W_ribs_rein,
        'W_ribs_total': W_ribs_total,
        'A_airfoil': A_airfoil,
        'A_rib_net': A_rib_net,
        'A_rib_rein_net': A_rib_rein_net,
        'tau_rib': tau_rib,
        'tau_cr_rib': tau_cr_rib,
        'rib_shear_ok': rib_shear_ok
    }
