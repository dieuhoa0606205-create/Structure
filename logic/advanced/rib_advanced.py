
"""
高级翼肋计算模块 (完整版)
- 板元离散化：将翼肋腹板划分为多个矩形板元
- 每个板元校核：剪切屈曲、压缩屈曲、弯剪联合作用
- 减轻孔影响：孔边应力集中系数
- 加强肋处理：等效厚度法
- 自动计算临界载荷并输出安全裕度
"""

import math
import numpy as np

G = 9.81

# ========== 1. 板元屈曲校核函数 ==========
def plate_shear_buckling(a, b, t, E, mu=0.3, boundary='ss'):
    """
    矩形板的剪切屈曲临界应力
    a, b: 板元长度和宽度 (m)
    t: 板厚 (m)
    boundary: 'ss' 四边简支, 'cc' 四边固支
    """
    if min(a, b) <= 0 or t <= 0:
        return float('inf')
    # 剪切屈曲系数 (简支)
    if boundary == 'ss':
        ks = 5.34 + 4.0 * (b / a)**2 if a >= b else 4.0 + 5.34 * (b / a)**2
    else:  # 固支
        ks = 8.98 + 5.6 * (b / a)**2 if a >= b else 5.6 + 8.98 * (b / a)**2
    return ks * math.pi**2 * E / (12 * (1 - mu**2)) * (t / b)**2

def plate_compression_buckling(a, b, t, E, mu=0.3, boundary='ss'):
    """
    矩形板的压缩屈曲临界应力
    """
    if b <= 0 or t <= 0:
        return float('inf')
    kc = 4.0 if boundary == 'ss' else 6.98
    return kc * math.pi**2 * E / (12 * (1 - mu**2)) * (t / b)**2

def interaction_check(sigma, sigma_cr, tau, tau_cr):
    """
    弯剪联合作用校核：R = σ/σ_cr + (τ/τ_cr)² ≤ 1
    """
    if sigma_cr <= 0 or tau_cr <= 0:
        return False
    R = sigma / sigma_cr + (tau / tau_cr)**2
    return R <= 1.0

# ========== 2. 减轻孔影响 ==========
def hole_stress_concentration(d_hole, b_panel):
    """
    圆孔应力集中系数 (近似)
    kt = 2.0 + (d_hole / b_panel)
    """
    if b_panel <= d_hole:
        return 5.0  # 孔太大，严重削弱
    return 2.0 + d_hole / b_panel

# ========== 3. 板元划分 ==========
def discretize_rib_panels(rib_height, rib_width, n_span=3, n_chord=2):
    """
    将翼肋腹板离散为 n_span × n_chord 个矩形板元
    返回每个板元的尺寸 [(a_i, b_i), ...]
    """
    panel_width = rib_width / n_chord
    panel_height = rib_height / n_span
    panels = []
    for i in range(n_span):
        for j in range(n_chord):
            panels.append((panel_width, panel_height))
    return panels

# ========== 4. 加强肋等效厚度 ==========
def equivalent_thickness(t_base, t_rein, A_rein, spacing):
    """
    加强肋的等效厚度 (按面积平均)
    """
    return t_base + A_rein / spacing

# ========== 5. 主计算函数 ==========
def compute_ribs_advanced(tmax, cw, n_rib, t_rib, fill_rib, rho_rib, E_rib,
                          n_rib_rein, t_rib_rein, fill_rib_rein, rho_rib_rein,
                          V_root, M_root, hole_diameter=0.0):
    """
    高级翼肋计算：板元法稳定性校核
    新增参数:
        M_root: 根部设计弯矩 (N·m)，用于估算翼肋平均压应力
        hole_diameter: 减轻孔直径 (m)，0 表示无孔
    """
    # 翼型轮廓面积
    A_airfoil = 0.68 * tmax * cw

    # ----- 普通翼肋 -----
    A_rib_net = A_airfoil * fill_rib
    W_ribs = rho_rib * A_rib_net * t_rib * n_rib * G

    # ----- 加强翼肋 -----
    A_rib_rein_net = A_airfoil * fill_rib_rein
    W_ribs_rein = rho_rib_rein * A_rib_rein_net * t_rib_rein * n_rib_rein * G
    W_ribs_total = W_ribs + W_ribs_rein

    # ----- 腹板几何估计 -----
    rib_height = tmax * 0.7      # 腹板有效高度
    rib_width = cw * 0.6         # 腹板弦向宽度 (主受力区域)

    # ----- 板元划分 -----
    panels = discretize_rib_panels(rib_height, rib_width, n_span=3, n_chord=2)

    # ----- 平均剪应力估算 -----
    n_total = n_rib + n_rib_rein
    if n_total > 0 and t_rib > 0 and rib_height > 0:
        tau_avg = V_root / (n_total * t_rib * rib_height)
    else:
        tau_avg = 0.0

    # ----- 平均压应力估算 (由弯矩引起) -----
    if n_total > 0 and t_rib > 0 and rib_height > 0:
        # 简化：翼肋承受的等效压应力来自机翼弯矩，假设均匀分摊
        sigma_avg = M_root / (n_total * rib_height**2 * t_rib) if rib_height > 0 else 0.0
    else:
        sigma_avg = 0.0

    # ----- 对每个板元进行稳定性校核 -----
    min_shear_margin = float('inf')
    min_comp_margin = float('inf')
    critical_panel = None

    for idx, (a, b) in enumerate(panels):
        # 剪切屈曲临界应力
        tau_cr = plate_shear_buckling(a, b, t_rib, E_rib)
        # 压缩屈曲临界应力
        sigma_cr = plate_compression_buckling(a, b, t_rib, E_rib)

        # 减轻孔影响
        kt = 1.0
        if hole_diameter > 0:
            kt = hole_stress_concentration(hole_diameter, min(a, b))

        tau_actual = tau_avg * kt
        sigma_actual = sigma_avg * kt

        # 联合作用
        combined_ok = interaction_check(sigma_actual, sigma_cr, tau_actual, tau_cr)

        # 裕度
        shear_margin = (tau_cr - tau_actual) / tau_cr * 100 if tau_cr > 0 else -100
        comp_margin = (sigma_cr - sigma_actual) / sigma_cr * 100 if sigma_cr > 0 else -100

        if shear_margin < min_shear_margin:
            min_shear_margin = shear_margin
        if comp_margin < min_comp_margin:
            min_comp_margin = comp_margin

        if not combined_ok and critical_panel is None:
            critical_panel = f"板元{idx}: (a={a*1000:.1f}mm, b={b*1000:.1f}mm)"

    # ----- 总体判断 -----
    overall_ok = min_shear_margin >= 0 and min_comp_margin >= 0

    return {
        'W_ribs': W_ribs,
        'W_ribs_rein': W_ribs_rein,
        'W_ribs_total': W_ribs_total,
        'A_airfoil': A_airfoil,
        'A_rib_net': A_rib_net,
        'A_rib_rein_net': A_rib_rein_net,
        'tau_avg': tau_avg,
        'sigma_avg': sigma_avg,
        'min_shear_margin': min_shear_margin,
        'min_comp_margin': min_comp_margin,
        'overall_ok': overall_ok,
        'critical_panel': critical_panel,
        'n_panels': len(panels)
    }
