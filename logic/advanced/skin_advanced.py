
"""
高级蒙皮计算模块：
- 加筋壁板整体与局部失稳
- 有效宽度法
"""
import math

def stiffened_panel_buckling(b, t, a, E, stringer_area, stringer_spacing):
    """加筋壁板压缩屈曲临界应力 (简支)"""
    # 欧拉屈曲
    kc = 4.0
    sigma_cr_global = kc * math.pi**2 * E / (12 * (1 - 0.3**2)) * (t / b)**2
    # 格间屈曲
    sigma_cr_local = kc * math.pi**2 * E / (12 * (1 - 0.3**2)) * (t / stringer_spacing)**2
    return min(sigma_cr_global, sigma_cr_local)

def effective_width(b, t, sigma, E):
    """有效宽度法 (von Karman)"""
    sigma_cr = 3.62 * E * (t / b)**2
    if sigma >= sigma_cr:
        return b * math.sqrt(sigma_cr / sigma)
    return b

def compute_skin_advanced(b, cw, tmax, t_skin, rho_skin, E_skin, tau_allow, T, d_rib):
    """高级蒙皮计算：加筋壁板"""
    from logic.wing.skin import compute_skin as base_skin
    base = base_skin(b, cw, tmax, t_skin, rho_skin, E_skin, tau_allow, T, d_rib)
    # 假设加筋参数
    stringer_spacing = 0.05  # m
    stringer_area = 50e-6    # m²
    cr_stress = stiffened_panel_buckling(d_rib, t_skin, cw*0.6, E_skin, stringer_area, stringer_spacing)
    base['panel_buckling_stress'] = cr_stress
    base['effective_width_ratio'] = effective_width(d_rib, t_skin, cr_stress, E_skin) / d_rib
    return base
