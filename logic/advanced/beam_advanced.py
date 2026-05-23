
"""
高级梁计算模块 (完整版)
- 侧向扭转屈曲
- 腹板剪切屈曲
- 缘条局部屈曲
- 疲劳寿命估算
- 最小重量优化
"""

import math

G = 9.81

def lateral_torsional_buckling(Iy, J, L, E, G_mat):
    """简支梁侧向扭转屈曲临界弯矩"""
    return math.pi / L * math.sqrt(E * Iy * G_mat * J) if L > 0 else float('inf')

def web_shear_buckling(h, t, E, mu=0.3):
    """腹板剪切屈曲临界应力"""
    ks = 5.34
    return ks * math.pi**2 * E / (12 * (1 - mu**2)) * (t / h)**2 if h > 0 else float('inf')

def flange_local_buckling(b, t, E, mu=0.3, free_edge=True):
    """缘条局部屈曲临界应力"""
    k = 0.425 if free_edge else 4.0
    return k * math.pi**2 * E / (12 * (1 - mu**2)) * (t / b)**2 if b > 0 else float('inf')

def fatigue_life_estimation(sigma_max, sigma_min, N_cycles, material='aluminum'):
    """简化 S-N 疲劳估算"""
    if sigma_max <= 0:
        return float('inf')
    if material == 'aluminum':
        Sut, Sf, b = 450e6, 190e6, -0.12
    elif material == 'composite':
        Sut, Sf, b = 600e6, 250e6, -0.10
    else:
        Sut, Sf, b = 700e6, 300e6, -0.09
    sigma_a = (sigma_max - sigma_min) / 2
    sigma_m = (sigma_max + sigma_min) / 2
    sigma_eq = sigma_a / (1 - sigma_m / Sut) if Sut > sigma_m else sigma_a * 10
    Nf = (sigma_eq / Sf) ** (1.0 / b) if sigma_eq > 0 else float('inf')
    return Nf / N_cycles if N_cycles > 0 else float('inf')

def optimize_wall_thickness(D, t_min, M_req, sigma_allow):
    """二分法求满足弯曲强度的最小壁厚 (碳管)"""
    lo, hi = t_min, D/2 - 1e-10
    for _ in range(60):
        mid = (lo + hi) / 2
        d = D - 2*mid
        if d <= 0:
            hi = mid
            continue
        W_cur = math.pi/32 * D**3 * (1 - (d/D)**4)
        if W_cur * sigma_allow >= M_req:
            hi = mid
        else:
            lo = mid
    return max(t_min, (lo + hi) / 2)

def compute_beam_advanced(loads, beam_type, section_type_front, section_type_rear,
                          front_params, rear_params, k_reinforce=0.0,
                          material_E=230e9, material_G=90e9,
                          fatigue_analysis=False, N_cycles=10000,
                          enable_optimization=False, target_safety=1.5):
    """高级梁计算：包含稳定性校核和可选优化"""
    from logic.wing.beam import compute_beam as base_beam
    result = base_beam(loads, beam_type, section_type_front, section_type_rear,
                       front_params, rear_params, k_reinforce)

    # 稳定性校核 (仅对工字梁)
    stability = {}
    if section_type_front == 'i_beam':
        h = front_params['h']
        b_f = front_params['b_f']
        t_f = front_params['t_f']
        t_w = front_params['t_w']
        Iy = (2 * t_f * b_f**3) / 12 + (h - 2*t_f) * t_w**3 / 12
        J = (2 * b_f * t_f**3 + (h - t_f) * t_w**3) / 3
        L_eff = 2 * loads['yR']
        Mcr = lateral_torsional_buckling(Iy, J, L_eff, material_E, material_G)
        tau_cr_web = web_shear_buckling(h, t_w, material_E)
        sigma_cr_flange = flange_local_buckling(b_f, t_f, material_E)
        stability = {
            'Mcr': Mcr,
            'tau_cr_web': tau_cr_web,
            'sigma_cr_flange': sigma_cr_flange,
            'lateral_ok': loads['M_root'] <= Mcr,
            'web_shear_ok': result['front']['tau'] <= tau_cr_web,
            'flange_ok': result['front']['sigma_b'] <= sigma_cr_flange
        }

    # 疲劳
    fatigue = {}
    if fatigue_analysis:
        sigma_max = result['sigma_b']
        sigma_min = 0.0
        flights = fatigue_life_estimation(sigma_max, sigma_min, N_cycles)
        fatigue = {'flights': flights}

    # 优化
    opt = {}
    if enable_optimization and section_type_front == 'tube':
        D = front_params['D']
        t_min = 0.0005
        M_req = loads['M_root'] / target_safety
        t_opt = optimize_wall_thickness(D, t_min, M_req, front_params['sigma_allow'])
        opt = {'t_opt': t_opt}

    result['stability'] = stability
    result['fatigue'] = fatigue
    result['optimization'] = opt
    return result
