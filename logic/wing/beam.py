
"""
梁计算模块
支持单梁/双梁，碳管/工字梁，强度校核与重量计算
"""

import math

G = 9.81


def compute_beam(loads, beam_type, section_type_front, section_type_rear,
                 front_params, rear_params, k_reinforce=0.0):
    """
    计算梁的重量与强度校核

    Args:
        loads: 载荷字典 (来自 compute_design_loads)
        beam_type: 'single' 或 'double'
        section_type_front: 'tube' 或 'i_beam' (前梁截面)
        section_type_rear: 'tube' 或 'i_beam' (后梁截面, 单梁时忽略)
        front_params: 前梁参数 dict
            碳管: {'D': 外径(m), 't': 壁厚(m), 'rho': 密度, 'sigma_allow': 许用应力}
            工字梁: {'h': 高, 'b_f': 缘条宽, 't_f': 缘条厚, 't_w': 腹板厚, 'rho': 密度, 'sigma_allow': 许用应力}
        rear_params: 后梁参数 (类似 front_params)
        k_reinforce: 加强系数 (作用在梁重量上)

    Returns:
        dict: {
            'W_beam': 梁总重 (N),
            'front': 前梁校核结果,
            'rear': 后梁校核结果 (双梁时),
            'bend_ok': 弯曲是否通过,
            'shear_ok': 剪切是否通过,
            'sigma_b': 弯曲应力,
            'tau_beam': 剪切应力,
            'sigma_allow': 许用弯曲应力,
            'tau_allow': 许用剪切应力
        }
    """
    M_root = loads['M_root']
    V_root = loads['V_root']
    yR = loads['yR']
    L_beam = 2 * yR

    def calc_section(params, s_type):
        """计算单个梁截面的几何属性"""
        if s_type == 'tube':
            D, t = params['D'], params['t']
            d = D - 2*t
            A = math.pi / 4 * (D**2 - d**2)
            I = math.pi / 64 * (D**4 - d**4)
            W_sec = 2 * I / D
        else:
            h, b_f, t_f, t_w = params['h'], params['b_f'], params['t_f'], params['t_w']
            A = 2*b_f*t_f + (h - 2*t_f)*t_w
            I = (b_f*h**3 - (b_f - t_w)*(h - 2*t_f)**3) / 12
            W_sec = 2 * I / h
        return A, I, W_sec

    def check_section(params, s_type, M, V):
        """对单个梁进行强度校核"""
        A, I, W_sec = calc_section(params, s_type)
        sigma = M / W_sec
        A_web = A if s_type == 'tube' else (params['h'] - 2*params['t_f']) * params['t_w']
        tau = V / A_web
        sigma_allow = params['sigma_allow']
        tau_allow = 0.5 * sigma_allow
        return {
            'A': A, 'I': I, 'W': W_sec,
            'sigma_b': sigma, 'tau': tau,
            'sigma_allow': sigma_allow, 'tau_allow': tau_allow,
            'bend_ok': sigma <= sigma_allow,
            'shear_ok': tau <= tau_allow
        }

    if beam_type == 'single':
        front_check = check_section(front_params, section_type_front, M_root, V_root)
        W_beam = front_params['rho'] * front_check['A'] * L_beam * G * (1 + k_reinforce)
        return {
            'W_beam': W_beam, 'front': front_check, 'rear': None,
            'bend_ok': front_check['bend_ok'], 'shear_ok': front_check['shear_ok'],
            'sigma_b': front_check['sigma_b'], 'tau_beam': front_check['tau'],
            'sigma_allow': front_check['sigma_allow'], 'tau_allow': front_check['tau_allow']
        }
    else:
        A_f, I_f, _ = calc_section(front_params, section_type_front)
        A_r, I_r, _ = calc_section(rear_params, section_type_rear)
        I_sum = I_f + I_r
        M_front = M_root * I_f / I_sum
        M_rear = M_root * I_r / I_sum
        V_front = V_root * A_f / (A_f + A_r)
        V_rear = V_root * A_r / (A_f + A_r)
        front_check = check_section(front_params, section_type_front, M_front, V_front)
        rear_check = check_section(rear_params, section_type_rear, M_rear, V_rear)
        W_beam = (front_params['rho'] * A_f + rear_params['rho'] * A_r) * L_beam * G * (1 + k_reinforce)
        bend_ok = front_check['bend_ok'] and rear_check['bend_ok']
        shear_ok = front_check['shear_ok'] and rear_check['shear_ok']
        return {
            'W_beam': W_beam, 'front': front_check, 'rear': rear_check,
            'bend_ok': bend_ok, 'shear_ok': shear_ok,
            'sigma_b': max(front_check['sigma_b'], rear_check['sigma_b']),
            'tau_beam': max(front_check['tau'], rear_check['tau']),
            'sigma_allow': front_check['sigma_allow'],
            'tau_allow': front_check['tau_allow']
        }
