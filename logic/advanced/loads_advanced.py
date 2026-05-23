"""
高级载荷计算模块 (完整算法版)
================================
本模块实现基于升力线理论的高精度气动载荷计算，包含：
1. Multhopp 展向环量分布求解 —— 离散傅里叶级数法求解升力线方程
2. Prandtl-Glauert 可压缩性修正 —— 考虑亚音速流动压缩性对升力线斜率的影响
3. Helmbold-Diederich 三维修正 —— 将二维翼型升力线斜率修正为三维机翼
4. 梯形/辛普森/Romberg 数值积分 —— 三种精度梯度的积分方法
5. 椭圆分布解析解 —— 作为 Multhopp 方法的对比基准
6. 集中载荷叠加 —— 气囊浮力、旋翼拉力、货舱载荷的弯矩合成

算法参考：
- Multhopp, H. (1938). "Die Berechnung der Auftriebsverteilung von Tragflügeln."
- Anderson, J.D. (2011). "Fundamentals of Aerodynamics."
"""

import math
import numpy as np

# ============================================================================
# 物理常数
# ============================================================================
G = 9.81                # 重力加速度 [m/s²]
RHO_STD = 1.225         # 海平面标准大气密度 [kg/m³]
PI = math.pi            # 圆周率

# ============================================================================
# 1. 二维翼型升力线斜率 (薄翼理论)
# ============================================================================
def cl_alpha_2d():
    """
    计算二维翼型的升力线斜率 dCl/dα。
    基于薄翼理论，对于理想不可压缩流，该值为 2π (约 6.283 rad⁻¹)。
    实际翼型受厚度和黏性影响略有偏差，但 2π 是理论极限值，适用于绝大多数常规翼型。
    """
    return 2 * PI


# ============================================================================
# 2. Prandtl-Glauert 可压缩性修正因子
# ============================================================================
def prandtl_glauert_factor(M):
    """
    计算亚音速可压缩性修正因子 β。
    当来流马赫数 M > 0 时，机翼表面局部流速增加，导致升力线斜率增大。
    Prandtl-Glauert 准则通过因子 β = sqrt(1 - M²) 来修正这一效应。
    注意：该准则仅适用于 M < 0.7~0.8 的亚音速范围。

    参数:
        M (float): 来流马赫数，必须 < 1.0

    返回:
        float: 可压缩性因子 β
    """
    if M >= 1.0:
        raise ValueError("Prandtl-Glauert 修正仅适用于亚音速流 (M < 1)")
    return math.sqrt(1 - M**2)


# ============================================================================
# 3. Helmbold-Diederich 三维机翼升力线斜率修正
# ============================================================================
def helmbold_diederich(AR, M=0.0):
    """
    将二维翼型升力线斜率修正为三维有限翼展机翼的升力线斜率。
    有限翼展机翼由于翼尖涡的下洗效应，有效攻角减小，升力线斜率低于二维值。
    Helmbold-Diederich 公式是一种简洁且广泛使用的工程修正方法。

    计算公式:
        CLα_3D = CLα_2D / (1 + x + sqrt(1 + x²))
        其中 x = CLα_2D / (π · AR · β)
              β 为 Prandtl-Glauert 可压缩性因子

    参数:
        AR (float): 机翼展弦比
        M  (float): 来流马赫数 (默认 0 表示不可压)

    返回:
        float: 三维机翼升力线斜率 (rad⁻¹)
    """
    cla2d = cl_alpha_2d()
    beta = prandtl_glauert_factor(M) if M > 0 else 1.0
    x = cla2d / (PI * AR * beta)
    return cla2d / (1 + x + math.sqrt(1 + x**2))


# ============================================================================
# 4. Multhopp 展向环量分布求解
# ============================================================================
def multhopp_circulation(CL, AR, n_stations=40):
    """
    使用 Multhopp 方法求解升力线方程，得到展向环量分布。
    这是经典升力线理论的一种高效数值解法。

    算法原理:
    1. 将升力线方程中的环量分布 Γ(θ) 展开为 Fourier 正弦级数 (仅奇数项):
       Γ(θ) = 2bV∞ Σ A_n sin(nθ)   (n = 1, 3, 5, ...)
    2. 在 N 个展向控制点 (Multhopp 角) 上建立线性方程组:
       Σ [ (4AR / (n·CLα_2D) + 1/sin(θ_i)) · sin(nθ_i) ] · A_n = CL · μ
    3. 求解 Fourier 系数 A_n，回代得到环量分布。

    Multhopp 角定义为 θ_i = π(i + 0.5) / N (i = 0, 1, ..., N-1)，
    对应的展向位置为 η_i = cos(θ_i)。

    参数:
        CL (float): 机翼总升力系数
        AR (float): 展弦比
        n_stations (int): 展向站位数 (建议 ≥ 40 以获得平滑分布)

    返回:
        tuple: (theta, eta, Gamma)
            - theta: Multhopp 角数组 [0, π/2]
            - eta:   无量纲展向坐标 2y/b
            - Gamma: 环量分布数组 (m²/s)
    """
    n = n_stations
    # 计算 Multhopp 角 θ 及其对应的展向位置 η
    theta = np.array([PI * (i + 0.5) / n for i in range(n)])
    eta = np.cos(theta)      # 无量纲展向位置
    mu = theta               # 控制点与站位重合

    # 构建系数矩阵 A_mat 和右端向量 B_vec
    A_mat = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            m = 2 * j + 1     # 仅奇数项
            # 系数矩阵元素: 由升力线方程离散得到
            A_mat[i, j] = (4 * AR / (m * cl_alpha_2d()) + 1.0 / np.sin(mu[i])) * np.sin(m * mu[i])

    B_vec = np.ones(n) * CL * 4.0 / (4.0 * AR)

    # 求解线性方程组得到 Fourier 系数 A_n
    try:
        A_coeff = np.linalg.solve(A_mat, B_vec)
    except np.linalg.LinAlgError:
        # 矩阵奇异时回退到椭圆分布 (仅 A1 非零)
        A_coeff = np.zeros(n)
        A_coeff[0] = CL * 4.0 / (4.0 * AR)

    # 回代 Fourier 系数得到环量分布
    Gamma = np.zeros(n)
    for j in range(n):
        m = 2 * j + 1
        Gamma += 2.0 * A_coeff[j] * np.sin(m * theta)

    return theta, eta, Gamma


# ============================================================================
# 5. 数值积分方法
# ============================================================================
def trapezoidal(x, y):
    """
    梯形法则积分。
    将区间分段，每小段用梯形面积近似积分。
    适用于光滑函数，精度 O(h²)。

    参数:
        x (ndarray): 积分节点的横坐标 (必须单调递增)
        y (ndarray): 积分节点的函数值

    返回:
        float: 积分近似值
    """
    if len(x) < 2:
        return 0.0
    dx = np.diff(x)
    return 0.5 * np.sum((y[:-1] + y[1:]) * dx)


def simpson(x, y):
    """
    复合辛普森积分。
    每两个子区间用二次抛物线近似被积函数，精度 O(h⁴)。
    要求积分点数为奇数 (区间数为偶数)。
    若点数为偶数，自动将最后一段用梯形法处理。

    参数:
        x (ndarray): 积分节点横坐标
        y (ndarray): 积分节点函数值

    返回:
        float: 积分近似值
    """
    n = len(x)
    if n < 3:
        return trapezoidal(x, y)
    if n % 2 == 0:  # 偶数点，最后一段用梯形
        s = trapezoidal(x[-2:], y[-2:])
        s += simpson(x[:-1], y[:-1])
        return s
    h = (x[-1] - x[0]) / (n - 1)
    s = y[0] + y[-1]
    for i in range(1, n - 1, 2):
        s += 4.0 * y[i]
    for i in range(2, n - 2, 2):
        s += 2.0 * y[i]
    return s * h / 3.0


def romberg(f, a, b, n=5):
    """
    Romberg 积分 (理查森外推法)。
    基于梯形法则，通过逐步减半步长并外推，可达到极高精度。
    适用于光滑函数，收敛速度远快于单纯梯形法。

    参数:
        f (callable): 被积函数
        a (float): 积分下限
        b (float): 积分上限
        n (int): 外推阶数 (越大精度越高，默认 5)

    返回:
        float: 积分近似值
    """
    R = np.zeros((n, n))
    h = b - a
    R[0, 0] = 0.5 * h * (f(a) + f(b))
    for i in range(1, n):
        h *= 0.5
        s = 0.0
        for k in range(1, 2**(i-1) + 1):
            s += f(a + (2*k - 1) * h)
        R[i, 0] = 0.5 * R[i-1, 0] + h * s
        for j in range(1, i + 1):
            R[i, j] = R[i, j-1] + (R[i, j-1] - R[i-1, j-1]) / (4**j - 1)
    return R[n-1, n-1]


# ============================================================================
# 6. 升力分布与截面载荷
# ============================================================================
def lift_from_gamma(V, cw, Gamma):
    """
    由环量分布计算单位展长升力。
    根据 Kutta-Joukowski 定理: l(y) = ρ · V∞ · Γ(y)
    """
    return RHO_STD * V * Gamma


def shear_moment_at_section(y, l_dist, y_cut):
    """
    从升力分布积分得到指定展向位置处的剪力和弯矩。
    剪力 V(y_cut) = ∫_{y_cut}^{b/2} l(η) dη
    弯矩 M(y_cut) = ∫_{y_cut}^{b/2} l(η) · (η - y_cut) dη
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
# 7. 椭圆分布解析解 (对比基准)
# ============================================================================
def elliptic_loading(WTO, kL, b, bfuse):
    """
    椭圆升力分布下根部剪力和弯矩的解析解 (Romberg 积分精确计算)。
    椭圆分布是升力线理论中诱导阻力最小的理想分布，常用于基准对比。
    """
    L_wing = (1 - kL) * WTO
    half_span = b / 2.0

    def l(y):
        if abs(y) > half_span:
            return 0.0
        return (2.0 * L_wing / (PI * b)) * math.sqrt(1.0 - (y / half_span)**2)

    V = romberg(l, bfuse / 2.0, half_span, n=6)

    def m_func(y):
        return l(y) * (y - bfuse / 2.0)
    M = romberg(m_func, bfuse / 2.0, half_span, n=6)
    return V, M


# ============================================================================
# 8. 主计算函数
# ============================================================================
def compute_design_loads_advanced(WTO, kL, nvtol, fs, b, bfuse,
                                  r_env, D_rotor, delta, cw, rho,
                                  V_cruise, Cm0, W_payload, W_cargo_width,
                                  use_elliptic=False):
    """
    高级载荷计算主函数 (仅考虑垂直起飞飞行工况)。

    算法流程:
    1. 计算旋翼展向安装位置 yR
    2. 根据 use_elliptic 选择 Multhopp 环量分布或椭圆分布计算气动载荷
    3. 合成集中力弯矩: 气囊浮力 M_env + 旋翼拉力 M_rotor + 货舱载荷 M_payload
    4. 得到根部总弯矩 M_total 和总剪力 V_total
    5. 应用过载系数 nvtol 和安全系数 fs 得到设计载荷
    6. 估算气动扭矩 T_aero

    返回:
        dict: {
            'M_root':   设计根部弯矩 (N·m),
            'V_root':   设计根部剪力 (N),
            'T_aero':   气动扭矩 (N·m),
            'yR':       旋翼展向位置 (m),
            'q_cruise': 巡航动压 (Pa),
            'n_design': 设计过载系数,
            'CL_wing':  机翼升力系数
        }
    """
    # 1. 旋翼展向位置
    yR = b / 2.0 + r_env + D_rotor / 2.0 + delta

    # 2. 机翼参考量
    S = b * cw                      # 参考面积
    q = 0.5 * rho * V_cruise**2     # 动压
    L_wing = (1 - kL) * WTO         # 机翼需产生的总升力
    CL_wing = L_wing / (q * S) if q * S > 0 else 0.0

    # 3. 气动载荷计算
    if use_elliptic and cw > 0:
        # Multhopp 环量分布法
        AR = b / cw if cw > 0 else 10.0
        theta, eta, Gamma = multhopp_circulation(CL_wing, AR, n_stations=40)
        y_phys = eta * b / 2.0      # 物理展向坐标
        l_dist = lift_from_gamma(V_cruise, cw, Gamma)
        V_wing, M_wing = shear_moment_at_section(y_phys, l_dist, bfuse / 2.0)
    else:
        # 椭圆分布解析解
        V_wing, M_wing = elliptic_loading(WTO, kL, b, bfuse)

    # 4. 集中力贡献
    M_env = (kL * WTO / 2.0) * ((b - bfuse) / 2.0)
    V_env = (kL * WTO / 2.0)

    M_rotor = -((1.0 - kL) * WTO / 2.0) * yR
    V_rotor = -((1.0 - kL) * WTO / 2.0)

    M_payload = -(W_payload / 2.0) * (W_cargo_width / 2.0)
    V_payload = -(W_payload / 2.0)

    # 5. 总载荷
    M_total = M_wing + M_env + M_rotor + M_payload
    V_total = V_wing + V_env + V_rotor + V_payload

    # 6. 设计载荷 (考虑过载和安全系数)
    n_design = nvtol
    M_root = n_design * fs * abs(M_total)
    V_root = n_design * fs * abs(V_total)

    # 7. 气动扭矩
    T_aero = q * S * cw * abs(Cm0)

    return {
        'M_root': M_root,
        'V_root': V_root,
        'T_aero': T_aero,
        'yR': yR,
        'q_cruise': q,
        'n_design': n_design,
        'CL_wing': CL_wing
    }