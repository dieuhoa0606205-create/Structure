
"""
展向弯矩与剪力分布 (高级版)
双轴图、包络线、极值标注、统计信息
"""

import matplotlib.pyplot as plt
import numpy as np

def plot_moment_distribution(loads_dict, WTO, kL, b, bfuse, cw, V_cruise):
    """
    绘制展向弯矩与剪力分布，双轴，专业风格。
    """
    L_wing = (1 - kL) * WTO
    half_span = b/2
    y = np.linspace(bfuse/2, half_span, 200)

    # 椭圆分布升力
    l_dist = (2 * L_wing / (np.pi * b)) * np.sqrt(1 - (y / half_span)**2)

    # 计算 V(y), M(y)
    V_y = np.array([np.trapezoid(l_dist[y>=yi], y[y>=yi]) for yi in y])
    M_y = np.array([np.trapezoid(l_dist[y>=yi] * (y[y>=yi] - yi), y[y>=yi]) for yi in y])

    M_root = loads_dict.get('M_root', M_y[0])
    V_root = loads_dict.get('V_root', V_y[0])

    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 剪力 (左轴)
    color_v = '#1f77b4'
    ax1.fill_between(y, V_y, alpha=0.15, color=color_v)
    ax1.plot(y, V_y, color=color_v, linewidth=2.5, label='剪力 V(y)')
    ax1.set_xlabel('展向位置 y (m)', fontsize=13)
    ax1.set_ylabel('剪力 (N)', color=color_v, fontsize=13)
    ax1.tick_params(axis='y', labelcolor=color_v)
    ax1.grid(True, alpha=0.3, linestyle='--')

    # 弯矩 (右轴)
    ax2 = ax1.twinx()
    color_m = '#d62728'
    ax2.fill_between(y, M_y, alpha=0.1, color=color_m)
    ax2.plot(y, M_y, color=color_m, linewidth=2.5, label='弯矩 M(y)')
    ax2.set_ylabel('弯矩 (N·m)', color=color_m, fontsize=13)
    ax2.tick_params(axis='y', labelcolor=color_m)

    # 极值标注
    max_M_idx = np.argmax(M_y)
    ax2.scatter(y[max_M_idx], M_y[max_M_idx], color=color_m, s=80, zorder=6)
    ax2.text(y[max_M_idx], M_y[max_M_idx], f'  {M_y[max_M_idx]:.1f}', color=color_m, va='bottom', fontsize=10)
    max_V_idx = np.argmax(np.abs(V_y))
    ax1.scatter(y[max_V_idx], V_y[max_V_idx], color=color_v, s=80, zorder=6)

    # 中心线参考线
    ax1.axvline(x=bfuse/2, color='gray', linestyle=':', linewidth=1.5)
    ax1.text(bfuse/2, ax1.get_ylim()[1]*0.9, '中心线', rotation=90, va='top', ha='right', color='gray', fontsize=9)

    # 图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    # 标题和信息框
    ax1.set_title('展向剪力与弯矩分布', fontsize=15, fontweight='bold')
    stats_text = f"根部弯矩: {M_root:.1f} N·m    |    根部剪力: {V_root:.1f} N"
    plt.figtext(0.5, 0.01, stats_text, ha='center', fontsize=11,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.6))

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    return fig
