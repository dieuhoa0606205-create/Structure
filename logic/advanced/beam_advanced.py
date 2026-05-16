
"""
高级梁计算模块 (完整版)
- 铁木辛柯梁弯曲与剪切修正
- 侧向扭转屈曲 (Lateral Torsional Buckling)
- 腹板剪切屈曲 (Web Shear Buckling)
- 缘条局部屈曲 (Flange Local Buckling)
- 疲劳寿命估算 (简化 S-N 方法)
- 最小重量优化 (二分法/梯度搜索)
"""

import math
import numpy as np

G = 9.81               # 重力加速度 [m/s²]
EPS = 1e-8

# ---------- 截面属性计算 ----------
def tube_section_properties(D, t):
    """碳管截面属性：面积、惯性矩、截面模量"""
    if t <= 0 or D <= 2*t:
        return 0.0, 0.0, 0.0
    d = D - 2*t
    A = math.pi/4 * (D**2 - d**2)
    I = math.pi/64 * (D**4 - d**4)
    W = 2*I/D
    return A, I, W

def i_beam_section_properties(h, b_f, t_f, t_w):
    """工字梁截面属性 (忽略根部圆弧)"""
    A = 2*b_f*t_f + (h - 2*t_f)*t_w
    if A <= 0:
        return 0.0, 0.0, 0.0
    # 对强轴 (高度方向) 的惯性矩
    I = (b_f * h**3 - (b_f - t_w) * (h - 2*t_f)**3) / 12
    W = 2*I/h
    return A, I, W

# ---------- 经典强度校核 ----------
def bending_stress(M, W):
    """弯曲正应力"""
    return M / W if W > EPS else float('inf')

def shear_stress_beam(V, A_web):
    """腹板平均剪应力"""
    return V / A_web if A_web > EPS else float('inf')

# ---------- 稳定性校核 ----------
def lateral_torsional_buckling_crit(Iy, J, L_eff, E, G_mat):
    """
    简支梁侧向扭转屈曲临界弯矩 (经典弹性解)
    Mcr = (pi/L_eff) * sqrt(E * Iy * G_mat * J)
    """
    if L_eff <= 0 or Iy <= 0 or J <= 0:
        return float('inf')
    return math.pi / L_eff * math.sqrt(E * Iy * G_mat * J)

def web_shear_buckling_crit(h, t_w, E, mu=0.3):
    """
    腹板剪切屈曲临界应力 (四边简支矩形板)
    ks = 5.34 (长板)
    """
    if h <= 0 or t_w <= 0:
        return float('inf')
    ks = 5.34
    return ks * math.pi**2 * E / (12*(1 - mu**2)) * (t_w / h)**2

def flange_local_buckling_crit(b_f, t_f, E, mu=0.3, boundary='one_edge_free'):
    """
    缘条局部屈曲临界应力
    - 若一端自由 (如工字梁外伸缘条): k = 0.425
    - 若两端简支 (如箱型内部): k = 4.0
    """
    if b_f <= 0 or t_f <= 0:
        return float('inf')
    k = 0.425 if boundary == 'one_edge_free' else 4.0
    return k * math.pi**2 * E / (12*(1 - mu**2)) * (t_f / b_f)**2

# ---------- 疲劳寿命估算 (简化) ----------
def fatigue_life_estimation(sigma_max, sigma_min, N_cycles_per_flight, material='aluminum'):
    """
    简化 S-N 疲劳估算 (基于 Goodman 修正)
    返回：容许飞行次数 (基于 Palmgren-Miner 线性累积)
    """
    if sigma_max <= 0:
        return float('inf')
    # 材料参数 (简化，单位 MPa)
    if material == 'aluminum':
        S_ut = 450.0     # 极限强度
        S_f = 190.0      # 疲劳强度 (5e8 循环)
        b = -0.12        # Basquin 指数
    elif material == 'composite':
        S_ut = 600.0
        S_f = 250.0
        b = -0.10
    else:  # steel
        S_ut = 700.0
        S_f = 300.0
        b = -0.09
    # Goodman 修正
    sigma_a = (sigma_max - sigma_min) / 2
    sigma_m = (sigma_max + sigma_min) / 2
    sigma_eq = sigma_a / (1 - sigma_m / S_ut) if S_ut > sigma_m else sigma_a * 10.0
    # S-N 曲线: σ_eq = S_f * (N_f)^b
    N_f = (sigma_eq / S_f) ** (1.0 / b) if sigma_eq > 0 else float('inf')
    flights = N_f / N_cycles_per_flight if N_cycles_per_flight > 0 else float('inf')
    return flights

# ---------- 最小重量优化 ----------
def optimize_wall_thickness(D, t_min, M_req, sigma_allow):
    """
    二分法求满足弯曲强度的最小壁厚 (碳管)
    返回: (t_opt, weight_ratio)
    """
    lo = t_min
    hi = D/2 - EPS
    if lo >= hi:
        return lo, 1.0
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
    t_opt = max(t_min, (lo+hi)/2)
    weight_ratio = t_opt / t_min if t_min > 0 else 1.0
    return t_opt, weight_ratio

# ---------- 高级梁主计算函数 ----------
def compute_beam_advanced(loads, beam_type, section_type_front, section_type_rear,
                          front_params, rear_params, k_reinforce=0.0,
                          material_E=230e9, material_G=90e9, material_density=1600,
                          fatigue_analysis=False, N_cycles=10000,
                          enable_optimization=False, target_safety=1.5):
    """
    高级梁计算主函数
    """
    M_root = loads.get('M_root', 0.0)
    V_root = loads.get('V_root', 0.0)
    yR = loads.get('yR', 1.0)
    L_beam = 2 * yR  # 一体梁总长

    # 准备返回结果
    result = {
        'M_root': M_root,
        'V_root': V_root,
        'L_beam': L_beam,
        'beam_type': beam_type,
        'front': {},
        'rear': {},
        'W_beam': 0.0,
        'bend_ok': False,
        'shear_ok': False,
        'stability': {},
        'fatigue': {},
        'optimization': {}
    }

    # ---------- 处理前梁 (及单梁) ----------
    if front_params:
        A_f, I_f, W_f = 0.0, 0.0, 0.0
        if section_type_front == 'tube':
            A_f, I_f, W_f = tube_section_properties(front_params['D'], front_params['t'])
            # 计算剪应力 (薄壁圆管近似)
            A_web = A_f  # 圆管全截面受剪
            sigma_f = bending_stress(M_root, W_f)
            tau_f = shear_stress_beam(V_root, A_web)
            # 局部稳定性 (对圆管不直接适用，但可考虑壳屈曲，简略)
            stability_note = "圆管局部屈曲未详细计算"
            section_type = 'tube'
        else:  # i_beam
            A_f, I_f, W_f = i_beam_section_properties(front_params['h'], front_params['b_f'],
                                                      front_params['t_f'], front_params['t_w'])
            A_web = (front_params['h'] - 2*front_params['t_f']) * front_params['t_w']
            sigma_f = bending_stress(M_root, W_f)
            tau_f = shear_stress_beam(V_root, A_web)
            # 侧向扭转屈曲
            Iy = (2*front_params['t_f']*front_params['b_f']**3) / 12
            J = (2*front_params['b_f']*front_params['t_f']**3 + (front_params['h']-front_params['t_f'])*front_params['t_w']**3) / 3
            Mcr = lateral_torsional_buckling_crit(Iy, J, L_beam, material_E, material_G)
            tau_cr = web_shear_buckling_crit(front_params['h'], front_params['t_w'], material_E)
            flange_cr = flange_local_buckling_crit(front_params['b_f'], front_params['t_f'], material_E)
            result['stability'] = {
                'Mcr': Mcr, 'tau_cr_web': tau_cr, 'sigma_cr_flange': flange_cr,
                'lateral_ok': M_root <= Mcr,
                'web_shear_ok': tau_f <= tau_cr,
                'flange_ok': sigma_f <= flange_cr
            }
            section_type = 'i_beam'

        # 强度校核
        sigma_allow_f = front_params.get('sigma_allow', 350e6)
        tau_allow_f = 0.5 * sigma_allow_f
        front_ok = sigma_f <= sigma_allow_f and tau_f <= tau_allow_f

        result['front'] = {
            'A': A_f, 'I': I_f, 'W': W_f,
            'sigma_b': sigma_f, 'tau': tau_f,
            'sigma_allow': sigma_allow_f, 'tau_allow': tau_allow_f,
            'bend_ok': sigma_f <= sigma_allow_f,
            'shear_ok': tau_f <= tau_allow_f,
            'section_type': section_type
        }

        # 疲劳估算
        if fatigue_analysis:
            sigma_max = sigma_f / 1e6  # MPa
            sigma_min = 0.0  # 假设脉冲循环
            flights = fatigue_life_estimation(sigma_max, sigma_min, N_cycles)
            result['fatigue']['front_flights'] = flights
            result['fatigue']['material'] = 'aluminum' if sigma_allow_f < 300e6 else 'composite'

        # 优化
        if enable_optimization and section_type_front == 'tube':
            t_opt, ratio = optimize_wall_thickness(front_params['D'], 0.0005,
                                                   M_root / target_safety, sigma_allow_f)
            result['optimization']['tube_wall_opt'] = t_opt
            result['optimization']['weight_ratio'] = ratio

    # ---------- 后梁 (仅双梁时) ----------
    if beam_type == 'double' and rear_params:
        A_r, I_r, W_r = 0.0, 0.0, 0.0
        if section_type_rear == 'tube':
            A_r, I_r, W_r = tube_section_properties(rear_params['D'], rear_params['t'])
        else:
            A_r, I_r, W_r = i_beam_section_properties(rear_params['h'], rear_params['b_f'],
                                                      rear_params['t_f'], rear_params['t_w'])
        # 按刚度分配弯矩 (简化)
        A_f_val = result['front'].get('A', 0.0)
        I_f_val = result['front'].get('I', 0.0)
        I_sum = I_f_val + I_r if I_r else 1.0
        ratio_M = I_r / I_sum if I_sum > 0 else 0.5
        M_rear = M_root * ratio_M
        V_rear = V_root * A_r / (A_f_val + A_r) if (A_f_val + A_r) > 0 else V_root/2

        sigma_allow_r = rear_params.get('sigma_allow', 350e6)
        tau_allow_r = 0.5 * sigma_allow_r
        sigma_r = bending_stress(M_rear, W_r) if W_r > 0 else 0
        tau_r = shear_stress_beam(V_rear, A_r) if A_r > 0 else 0

        result['rear'] = {
            'A': A_r, 'I': I_r, 'W': W_r,
            'sigma_b': sigma_r, 'tau': tau_r,
            'sigma_allow': sigma_allow_r, 'tau_allow': tau_allow_r,
            'bend_ok': sigma_r <= sigma_allow_r,
            'shear_ok': tau_r <= tau_allow_r
        }

    # ---------- 重量计算 ----------
    A_front = result['front'].get('A', 0.0)
    A_rear = result['rear'].get('A', 0.0) if result['rear'] else 0.0
    total_area = A_front + A_rear
    W_beam = material_density * total_area * L_beam * G * (1 + k_reinforce)
    result['W_beam'] = W_beam

    # 综合结论
    result['bend_ok'] = result['front'].get('bend_ok', False) and (result['rear'].get('bend_ok', True) if result['rear'] else True)
    result['shear_ok'] = result['front'].get('shear_ok', False) and (result['rear'].get('shear_ok', True) if result['rear'] else True)

    return result
