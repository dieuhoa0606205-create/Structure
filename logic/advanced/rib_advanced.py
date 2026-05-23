
"""
高级翼肋计算模块 (完整版)
- 板元离散化
- 剪切屈曲、压缩屈曲、弯剪联合作用
- 减轻孔影响
"""

import math

def plate_shear_buckling(a, b, t, E, mu=0.3, boundary='ss'):
    """矩形板剪切屈曲临界应力"""
    if min(a, b) <= 0 or t <= 0:
        return float('inf')
    ks = 5.34 + 4.0 * (b/a)**2 if a >= b else 4.0 + 5.34 * (b/a)**2
    return ks * math.pi**2 * E / (12*(1 - mu**2)) * (t / b)**2

def plate_compression_buckling(a, b, t, E, mu=0.3, boundary='ss'):
    """矩形板压缩屈曲临界应力"""
    if b <= 0 or t <= 0:
        return float('inf')
    kc = 4.0 if boundary == 'ss' else 6.98
    return kc * math.pi**2 * E / (12*(1 - mu**2)) * (t / b)**2

def interaction_check(sigma, sigma_cr, tau, tau_cr):
    """弯剪联合作用校核 R = σ/σ_cr + (τ/τ_cr)² ≤ 1"""
    if sigma_cr <= 0 or tau_cr <= 0:
        return False
    return (sigma/sigma_cr + (tau/tau_cr)**2) <= 1.0

def hole_stress_factor(d_hole, b_panel):
    """减轻孔应力集中系数"""
    if b_panel <= d_hole:
        return 5.0
    return 2.0 + d_hole / b_panel

def compute_ribs_advanced(tmax, cw, n_rib, t_rib, fill_rib, rho_rib, E_rib,
                          n_rib_rein, t_rib_rein, fill_rib_rein, rho_rib_rein,
                          V_root, M_root, hole_diameter=0.0):
    """高级翼肋计算：板元法稳定性校核"""
    from logic.wing.rib import compute_ribs as base_ribs
    base = base_ribs(tmax, cw, n_rib, t_rib, fill_rib, rho_rib, E_rib,
                     n_rib_rein, t_rib_rein, fill_rib_rein, rho_rib_rein, V_root)

    rib_height = tmax * 0.7
    rib_width = cw * 0.6
    n_span, n_chord = 3, 2
    panel_w = rib_width / n_chord
    panel_h = rib_height / n_span

    n_total = n_rib + n_rib_rein
    tau_avg = V_root / (n_total * t_rib * rib_height) if n_total > 0 and t_rib > 0 else 0
    sigma_avg = M_root / (n_total * rib_height**2 * t_rib) if n_total > 0 and t_rib > 0 else 0

    kt = hole_stress_factor(hole_diameter, min(panel_w, panel_h)) if hole_diameter > 0 else 1.0
    tau_actual = tau_avg * kt
    sigma_actual = sigma_avg * kt

    tau_cr = plate_shear_buckling(panel_w, panel_h, t_rib, E_rib)
    sigma_cr = plate_compression_buckling(panel_w, panel_h, t_rib, E_rib)
    combined_ok = interaction_check(sigma_actual, sigma_cr, tau_actual, tau_cr)

    base['plate_shear_margin'] = (tau_cr - tau_actual) / tau_cr * 100 if tau_cr > 0 else -100
    base['plate_comp_margin'] = (sigma_cr - sigma_actual) / sigma_cr * 100 if sigma_cr > 0 else -100
    base['combined_ok'] = combined_ok
    base['n_panels'] = n_span * n_chord
    return base
