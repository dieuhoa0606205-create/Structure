
import matplotlib.pyplot as plt
import numpy as np
from logic.advanced.loads_advanced import multhopp_circulation, elliptic_loading, lift_from_gamma, shear_moment_at_section, cl_alpha_2d

def plot_moment_distribution(loads_dict, WTO, kL, b, bfuse, cw, V_cruise):
    """绘制机翼展向弯矩和剪力分布"""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
    # 计算展向分布
    y = np.linspace(bfuse/2, b/2, 100)
    # 使用椭圆分布做演示
    L_wing = (1 - kL) * WTO
    half_span = b/2
    l_dist = (2 * L_wing / (np.pi * b)) * np.sqrt(1 - (y / half_span)**2)
    # 计算剪力和弯矩
    V_y = []
    M_y = []
    for yi in y:
        mask = y >= yi
        dy = np.diff(y[mask], prepend=y[mask][0])[1:] if len(y[mask])>1 else [0]
        V_y.append(np.trapezoid(l_dist[mask], y[mask]))
        M_y.append(np.trapezoid(l_dist[mask] * (y[mask] - yi), y[mask]))
    ax1.plot(y, V_y, 'b-')
    ax1.set_xlabel('展向位置 y (m)')
    ax1.set_ylabel('剪力 (N)')
    ax1.grid(True)
    ax2.plot(y, M_y, 'r-')
    ax2.set_xlabel('展向位置 y (m)')
    ax2.set_ylabel('弯矩 (N·m)')
    ax2.grid(True)
    plt.tight_layout()
    return fig
