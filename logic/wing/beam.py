
import math

G = 9.81

def compute_beam(loads, beam_type, section_type_front, section_type_rear,
                 front_params, rear_params, k_reinforce=0.0):
    M_root = loads['M_root']
    V_root = loads['V_root']
    yR = loads['yR']
    L_beam = 2 * yR

    def calc_section(params, s_type):
        if s_type == 'tube':
            D, t = params['D'], params['t']
            if t <= 0 or D <= 2*t: return 0.0, 0.0, 0.0
            d = D - 2*t
            A = math.pi/4*(D**2 - d**2)
            I = math.pi/64*(D**4 - d**4)
            W_sec = 2*I/D
            return A, I, W_sec
        else:
            h, b_f, t_f, t_w = params['h'], params['b_f'], params['t_f'], params['t_w']
            if h <= 2*t_f or b_f <= 0 or t_f <= 0 or t_w <= 0: return 0.0, 0.0, 0.0
            I = (b_f * h**3 - (b_f - t_w) * (h - 2*t_f)**3) / 12
            if I <= 0: return 0.0, 0.0, 0.0
            W_sec = 2 * I / h
            A = 2*b_f*t_f + (h - 2*t_f)*t_w
            return A, I, W_sec

    def check_section(params, s_type, M, V):
        A, I, W_sec = calc_section(params, s_type)
        sigma_allow = params['sigma_allow']
        tau_allow = 0.5 * sigma_allow
        sigma = M / W_sec if W_sec > 0 else 0.0
        A_web = A if s_type == 'tube' else (params['h'] - 2*params['t_f']) * params['t_w']
        tau = V / A_web if A_web > 0 else 0.0
        return {
            'A': A, 'I': I, 'W': W_sec,
            'sigma_b': sigma, 'tau': tau,
            'sigma_allow': sigma_allow, 'tau_allow': tau_allow,
            'bend_ok': sigma <= sigma_allow,
            'shear_ok': tau <= tau_allow,
            'M_allow': sigma_allow * W_sec
        }

    if beam_type == 'single':
        fc = check_section(front_params, section_type_front, M_root, V_root)
        W_beam = front_params['rho'] * fc['A'] * L_beam * G * (1 + k_reinforce)
        return {
            'W_beam': W_beam, 'front': fc, 'rear': None,
            'bend_ok': fc['bend_ok'], 'shear_ok': fc['shear_ok'],
            'sigma_b': fc['sigma_b'], 'tau_beam': fc['tau'],
            'sigma_allow': fc['sigma_allow'], 'tau_allow': fc['tau_allow'],
            'M_allow': fc['M_allow']
        }
    else:
        A_f, I_f, _ = calc_section(front_params, section_type_front)
        A_r, I_r, _ = calc_section(rear_params, section_type_rear)
        I_sum = I_f + I_r
        if I_sum <= 0: return {'W_beam': 0, 'bend_ok': False, 'shear_ok': False, 'sigma_b': 0, 'tau_beam': 0, 'sigma_allow': 0, 'tau_allow': 0, 'M_allow': 0}
        M_front = M_root * I_f / I_sum
        M_rear = M_root * I_r / I_sum
        V_front = V_root * A_f / (A_f + A_r)
        V_rear = V_root * A_r / (A_f + A_r)
        fc = check_section(front_params, section_type_front, M_front, V_front)
        rc = check_section(rear_params, section_type_rear, M_rear, V_rear)
        W_beam = (front_params['rho'] * A_f + rear_params['rho'] * A_r) * L_beam * G * (1 + k_reinforce)
        return {
            'W_beam': W_beam, 'front': fc, 'rear': rc,
            'bend_ok': fc['bend_ok'] and rc['bend_ok'],
            'shear_ok': fc['shear_ok'] and rc['shear_ok'],
            'sigma_b': max(fc['sigma_b'], rc['sigma_b']),
            'tau_beam': max(fc['tau'], rc['tau']),
            'sigma_allow': fc['sigma_allow'],
            'tau_allow': fc['tau_allow'],
            'M_allow_front': fc['M_allow'],
            'M_allow_rear': rc['M_allow'] if rc else None,
            'M_front': M_front,
            'M_rear': M_rear,
            'M_allow': min(fc['M_allow'], rc['M_allow']) if rc else fc['M_allow']
        }
