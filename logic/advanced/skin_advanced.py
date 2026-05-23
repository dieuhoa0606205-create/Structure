
"""
高级蒙皮计算模块 (完整版)
- 加筋壁板整体与局部失稳
- 有效宽度法
"""

import math

def stiffened_panel_buckling(b, t, a, E, stringer_spacing):
    """加筋壁板压缩屈曲临界应力"""
    kc = 4.0
    sigma_cr_global = kc * math.pi**2 * E / (12 * (1 - 0.3**2)) * (t / b)**2
    sigma_cr_local = kc * math.pi**2 * E / (12 * (1 - 0.3**2)) * (t / stringer_spacing)**2
    return min(sigma_cr_global, sigma_cr_local)

def effective_width(b, t, sigma, E):
    """von Karman 有效宽度法"""
    sigma_cr = 3.62 * E * (t / b)**2
    if sigma >= sigma_cr:
        return b * math.sqrt(sigma_cr / sigma)
    return b

def compute_skin_advanced(b, cw, tmax, t_skin, rho_skin, E_skin, tau_allow, T, d_rib):
    """高级蒙皮计算：加筋壁板分析"""
    from logic.wing.skin import compute_skin as base_skin
    base = base_skin(b, cw, tmax, t_skin, rho_skin, E_skin, tau_allow, T, d_rib)

    # 加筋参数 (可调，此处使用默认值)
    stringer_spacing = 0.05  # m
    cr_stress = stiffened_panel_buckling(d_rib, t_skin, cw*0.6, E_skin, stringer_spacing)
    base['panel_buckling_stress'] = cr_stress
    base['effective_width_ratio'] = effective_width(d_rib, t_skin, cr_stress, E_skin) / d_rib
    return base
