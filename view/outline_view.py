
"""
飞行器俯视轮廓可视化 (动态边界)
展向沿水平 x 轴，弦向沿垂直 y 轴。
"""

import matplotlib.pyplot as plt
import numpy as np

def plot_aircraft_outline(b, cw, tmax, r_env, r_env_long, D_rotor, delta,
                          airfoil_coords=None, naca_label=None, rotor_chord_pos=0.0):
    half_span = b / 2.0
    rotor_center = half_span + r_env + D_rotor/2 + delta
    rotor_radius = D_rotor / 2

    fig, ax = plt.subplots(figsize=(14, 7))
    ax.grid(True, alpha=0.2, linestyle='--', linewidth=0.5)
    ax.set_aspect('equal')

    # 机翼
    wing = plt.Rectangle((-half_span, -cw/2), b, cw,
                         linewidth=1.5, edgecolor='blue', facecolor='steelblue', alpha=0.3, label='机翼')
    ax.add_patch(wing)

    # 前缘后缘线
    ax.plot([-half_span, half_span], [cw/2, cw/2], 'k--', linewidth=0.8)
    ax.plot([-half_span, half_span], [-cw/2, -cw/2], 'k--', linewidth=0.8)

    # 气囊
    for x_sign in [-1, 1]:
        env = plt.matplotlib.patches.Ellipse(
            xy=(x_sign*half_span, 0), width=2*r_env, height=2*r_env_long,
            linewidth=1.5, edgecolor='green', facecolor='lightgreen', alpha=0.4
        )
        ax.add_patch(env)

    # 四个旋翼
    for offset, color in [(-0.3*cw, 'red'), (0.3*cw, 'darkred')]:
        for x_sign in [-1, 1]:
            rotor = plt.Circle(
                (x_sign*rotor_center, rotor_chord_pos+offset), rotor_radius,
                linewidth=2, edgecolor=color, facecolor='none'
            )
            ax.add_patch(rotor)

    # 旋翼臂
    ax.plot([-half_span, -rotor_center], [0, 0], 'k-', linewidth=1.5, alpha=0.7)
    ax.plot([half_span, rotor_center], [0, 0], 'k-', linewidth=1.5, alpha=0.7)

    # ---------- 动态计算坐标轴范围 ----------
    # 收集所有元素的边界点
    elements_x_min = -rotor_center - rotor_radius
    elements_x_max = rotor_center + rotor_radius
    # 弦向考虑机翼、气囊、旋翼
    y_span = max(cw/2, r_env_long, rotor_radius + abs(rotor_chord_pos))
    margin = 0.1 * (elements_x_max - elements_x_min)  # 10% 边距
    ax.set_xlim(elements_x_min - margin, elements_x_max + margin)
    ax.set_ylim(-y_span - margin, y_span + margin)

    ax.set_xlabel('展向 (m)')
    ax.set_ylabel('弦向 (m)')
    title = '飞行器俯视轮廓'
    if naca_label:
        title += f' (翼型: {naca_label})'
    ax.set_title(title)
    ax.legend()
    return fig
