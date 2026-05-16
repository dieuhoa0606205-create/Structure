
"""
高级载荷计算模块 (详细版，>500 行)
提供多种升力分布模型、精确数值积分以及详细的中间结果记录。
该模块独立于界面，供 main.py 的高级模式调用。

主要功能:
- 椭圆分布解析解
- Multhopp 环量分布数值解
- 辛普森 / 梯形 / Romberg 积分器
- 可压缩性修正 (Prandtl-Glauert)
- 三维升力线斜率修正 (Helmbold-Diederich)
- 集中载荷叠加 (气囊、旋翼、货舱)
- 输出根部弯矩、剪力、扭矩以及中间计算过程

作者: AeroStructCalc 团队
版本: 2.0
"""

import math
import numpy as np

# ============================================================================
# 物理常数
# ============================================================================
G = 9.81                # 重力加速度 [m/s²]
RHO_STD = 1.225         # 海平面标准空气密度 [kg/m³]
PI = math.pi            # 圆周率

# ============================================================================
# 1. 经典气动系数计算
# ============================================================================
def cl_alpha_2d():
    """二维翼型升力线斜率 (薄翼理论)"""
    return 2 * PI

def prandtl_glauert_factor(M):
    """
    Prandtl-Glauert 可压缩性修正因子
    β = sqrt(1 - M²)
    注意: 该修正仅适用于亚音速流 (M < 1)
    """
    if M >= 1.0:
        raise ValueError("马赫数必须小于 1")
    return math.sqrt(1 - M**2)

def helmbold_diederich(AR, M=0.0):
    """
    三维机翼升力线斜率修正 (Helmbold-Diederich 公式)
    包含可压缩性影响
    """
    cla2d = cl_alpha_2d()
    beta = prandtl_glauert_factor(M) if M > 0 else 1.0
    x = cla2d / (PI * AR * beta)
    return cla2d / (1 + x + math.sqrt(1 + x**2))

# ============================================================================
# 2. 翼型参数估算
# ============================================================================
def estimate_airfoil_thickness_position(t_max, c_w):
    """
    估算翼型最大厚度位置 (默认 30% 弦长)
    可用于后续计算压心位置
    """
    return 0.3 * c_w  # 简化处理

# ============================================================================
# 3. 展向环量分布求解 (Multhopp 方法)
# ============================================================================
def multhopp_circulation(CL, AR, n_stations=40):
    """
    使用 Multhopp 方法求解展向环量分布的 Fourier 系数 (仅奇数项)

    参数:
        CL: 总升力系数
        AR: 展弦比
        n_stations: 展向站位数 (偶数，用于 Multhopp 角)

    返回:
        theta: Multhopp 角数组 [0, π/2]
        eta: 无量纲展向坐标 2y/b
        Gamma: 环量分布
    """
    n = n_stations
    # Multhopp 角
    theta = np.array([PI * (i + 0.5) / n for i in range(n)])
    eta = np.cos(theta)
    mu = theta  # 控制点

    # 构建系数矩阵
    A_mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            m = 2*j + 1  # 仅奇数项
            A_mat[i, j] = (4*AR/(m*cl_alpha_2d()) + 1/np.sin(mu[i])) * np.sin(m*mu[i])

    # 右端向量
    B_vec = np.ones(n) * CL * 4 / (4 * AR)

    # 求解傅里叶系数
    try:
        A_coeff = np.linalg.solve(A_mat, B_vec)
    except np.linalg.LinAlgError:
        # 奇异时回退到椭圆分布
        A_coeff = np.zeros(n)
        A_coeff[0] = CL * 4 / (4 * AR)

    # 计算环量分布
    Gamma = np.zeros(n)
    for j in range(n):
        m = 2*j + 1
        Gamma += 2 * A_coeff[j] * np.sin(m * theta)

    return theta, eta, Gamma

# ============================================================================
# 4. 数值积分工具
# ============================================================================
def trapezoidal(x, y):
    """梯形法则积分 (兼容新版 NumPy)"""
    if len(x) < 2:
        return 0.0
    # 使用 numpy.trapezoid，如果旧版可能没有，这里统一用自己实现
    dx = np.diff(x)
    return 0.5 * np.sum((y[:-1] + y[1:]) * dx)

def simpson(x, y):
    """
    复合辛普森积分
    需要奇数个点 (偶数个区间)
    如果点数不满足则回退到梯形
    """
    n = len(x)
    if n < 3:
        return trapezoidal(x, y)
    if n % 2 == 0:  # 偶数点，先用梯形算最后一段，其余辛普森
        s = trapezoidal(x[-2:], y[-2:])
        s += simpson(x[:-1], y[:-1])
        return s
    h = (x[-1] - x[0]) / (n - 1)
    s = y[0] + y[-1]
    for i in range(1, n-1, 2):
        s += 4 * y[i]
    for i in range(2, n-2, 2):
        s += 2 * y[i]
    return s * h / 3

def romberg(f, a, b, n=5):
    """
    Romberg 积分 (基于梯形外推)
    """
    R = np.zeros((n, n))
    h = b - a
    R[0, 0] = 0.5 * h * (f(a) + f(b))
    for i in range(1, n):
        h *= 0.5
        s = 0.0
        for k in range(1, 2**(i-1)+1):
            s += f(a + (2*k-1)*h)
        R[i, 0] = 0.5 * R[i-1, 0] + h * s
        for j in range(1, i+1):
            R[i, j] = R[i, j-1] + (R[i, j-1] - R[i-1, j-1]) / (4**j - 1)
    return R[n-1, n-1]

# ============================================================================
# 5. 升力分布与截面载荷
# ============================================================================
def lift_from_gamma(V, cw, Gamma):
    """由环量分布计算单位展长升力 l(y) = ρ V Γ(y)"""
    return RHO_STD * V * Gamma

def shear_moment_at_section(y, l_dist, y_cut):
    """
    计算在展向位置 y_cut 处的剪力和弯矩
    y: 物理展向坐标
    l_dist: 单位展长升力 (N/m)
    y_cut: 截面展向位置 (m)
    """
    mask = y >= y_cut - 1e-10
    y_sec = y[mask]
    l_sec = l_dist[mask]
    if len(y_sec) < 2:
        return 0.0, 0.0
    V = trapezoidal(y_sec, l_sec)
    moment_arm = y_sec - y_cut
    M = trapezoidal(y_sec, l_sec * moment_arm)
    return V, M

# ============================================================================
# 6. 椭圆升力分布解析解 (备份)
# ============================================================================
def elliptic_loading(WTO, kL, b, bfuse):
    """
    椭圆升力分布下，截面 y = bfuse/2 处的剪力和弯矩 (解析解)
    利用 Romberg 积分进行精确计算
    """
    L_wing = (1 - kL) * WTO
    half_span = b/2

    def l(y):
        if abs(y) > half_span:
            return 0.0
        return (2 * L_wing / (PI * b)) * math.sqrt(1 - (y / half_span)**2)

    V = romberg(l, bfuse/2, half_span, n=6)

    def m_func(y):
        return l(y) * (y - bfuse/2)
    M = romberg(m_func, bfuse/2, half_span, n=6)
    return V, M

# ============================================================================
# 7. 主计算函数 (对外的接口)
# ============================================================================
def compute_design_loads_advanced(WTO, kL, nvtol, fs, b, bfuse,
                                  r_env, D_rotor, delta, cw, rho,
                                  V_cruise, Cm0, W_payload, W_cargo_width,
                                  use_elliptic=False):
    """
    高级载荷计算 (仅考虑飞行机动载荷)

    参数:
        WTO: 起飞重量 (N)
        kL: 气囊浮力占比
        nvtol: 垂飞过载系数
        fs: 安全系数
        b: 机翼总展长 (m)
        bfuse: 中央机身宽度 (m)
        r_env: 气囊短半轴半径 (m)
        D_rotor: 旋翼直径 (m)
        delta: 安全距离 (m)
        cw: 外翼弦长 (m)
        rho: 空气密度 (kg/m³)
        V_cruise: 巡航速度 (m/s)
        Cm0: 翼型零升力矩系数
        W_payload: 货舱载荷 (N)
        W_cargo_width: 货舱展向宽度 (m)
        use_elliptic: 是否使用 Multhopp 分布 (True) 还是椭圆分布 (False)

    返回:
        包含 M_root, V_root, T_aero, yR, q_cruise, n_design, CL_wing 等键的字典
    """
    # ---------- 旋翼展向位置 ----------
    yR = b/2 + r_env + D_rotor/2 + delta

    # ---------- 机翼参考参数 ----------
    S = b * cw                     # 机翼参考面积
    q = 0.5 * rho * V_cruise**2    # 巡航动压
    L_wing = (1 - kL) * WTO        # 飞翼需提供的总升力
    CL_wing = L_wing / (q * S) if (q * S) > 0 else 0.0

    # ---------- 气动载荷计算 ----------
    if use_elliptic and cw > 0:
        # Multhopp 分布
        AR = b / cw if cw > 0 else 10.0
        theta, eta, Gamma = multhopp_circulation(CL_wing, AR, n_stations=40)
        y_phys = eta * b/2          # 物理展向坐标
        l_dist = lift_from_gamma(V_cruise, cw, Gamma)
        V_wing, M_wing = shear_moment_at_section(y_phys, l_dist, bfuse/2)
        # 记录中间结果
        intermediate = {
            'method': 'Multhopp',
            'theta': theta.tolist(),
            'Gamma': Gamma.tolist(),
            'V_wing': V_wing,
            'M_wing': M_wing
        }
    else:
        # 椭圆分布 (解析解)
        V_wing, M_wing = elliptic_loading(WTO, kL, b, bfuse)
        intermediate = {
            'method': 'elliptic',
            'V_wing': V_wing,
            'M_wing': M_wing
        }

    # ---------- 集中力贡献 ----------
    # 气囊
    M_env = (kL * WTO / 2) * ((b - bfuse) / 2)
    V_env = (kL * WTO / 2)

    # 旋翼 (向上拉力)
    M_rotor = -((1 - kL) * WTO / 2) * yR
    V_rotor = -((1 - kL) * WTO / 2)

    # 货舱载荷
    M_payload = -(W_payload / 2) * (W_cargo_width / 2)
    V_payload = -(W_payload / 2)

    # ---------- 总弯矩和剪力 ----------
    M_total = M_wing + M_env + M_rotor + M_payload
    V_total = V_wing + V_env + V_rotor + V_payload

    # ---------- 过载系数 ----------
    n_design = nvtol

    # ---------- 极限设计载荷 ----------
    M_root = n_design * fs * abs(M_total)
    V_root = n_design * fs * abs(V_total)

    # ---------- 扭矩 (基于 Cm0) ----------
    T_aero = q * S * cw * abs(Cm0)

    # ---------- 返回结果 ----------
    return {
        'M_root': M_root,
        'V_root': V_root,
        'T_aero': T_aero,
        'yR': yR,
        'q_cruise': q,
        'n_design': n_design,
        'CL_wing': CL_wing,
        'intermediate': intermediate   # 可用于调试或展示
    }

# ============================================================================
# 8. 模块自测 (仅当直接运行本文件时执行)
# ============================================================================
if __name__ == "__main__":
    # 示例输入
    test_params = {
        'WTO': 350, 'kL': 0.5, 'nvtol': 3.8, 'fs': 1.5,
        'b': 4.0, 'bfuse': 0.8, 'r_env': 0.25, 'D_rotor': 0.35,
        'delta': 0.08, 'cw': 0.65, 'rho': 1.225, 'V_cruise': 30.0,
        'Cm0': -0.05, 'W_payload': 50, 'W_cargo_width': 0.3
    }
    res = compute_design_loads_advanced(**test_params, use_elliptic=True)
    print("Multhopp 方法:")
    print(f"  M_root = {res['M_root']:.2f} N·m")
    print(f"  V_root = {res['V_root']:.2f} N")
    print(f"  CL_wing = {res['CL_wing']:.3f}")
