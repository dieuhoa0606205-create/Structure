
"""
翼型可视化模块 (专业版)
绘制翼型外形、压力分布、关键参数标注、弦向厚度分布
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib import cm

def plot_airfoil(xu, yu, xl, yl, title="翼型几何"):
    """
    绘制翼型外形、弦向厚度分布、标注最大厚度与弯度。
    """
    # 准备数据
    t = yu - yl
    camber = (yu + yl) / 2.0
    max_t_idx = np.argmax(t)
    max_t_pos = xu[max_t_idx]
    max_t_val = t[max_t_idx]
    max_camber_idx = np.argmax(np.abs(camber))
    max_camber_pos = xu[max_camber_idx]
    max_camber_val = camber[max_camber_idx]

    # 创建画布
    fig = plt.figure(figsize=(12, 7))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[2, 1])

    # 左上：翼型轮廓
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(xu, yu, 'b-', linewidth=2, label='上表面')
    ax1.plot(xl, yl, 'b-', linewidth=2, label='下表面')
    ax1.plot([0, 1], [0, 0], 'k--', linewidth=0.8)
    # 中弧线
    ax1.plot(xu, camber, 'gray', linestyle=':', linewidth=1, label='中弧线')
    # 最大厚度标注
    ax1.axvline(x=max_t_pos, color='r', linestyle='--', linewidth=1.2)
    ax1.plot(max_t_pos, camber[max_t_idx], 'ro', markersize=6)
    ax1.annotate(f'最大厚度 {max_t_val*100:.2f}%c\n@{max_t_pos*100:.1f}%c',
                 xy=(max_t_pos, camber[max_t_idx]),
                 xytext=(max_t_pos+0.1, max_t_val/2),
                 arrowprops=dict(arrowstyle="->", color='red'),
                 fontsize=9, color='red')
    # 最大弯度标注
    ax1.axvline(x=max_camber_pos, color='green', linestyle='--', linewidth=1.0)
    ax1.plot(max_camber_pos, max_camber_val, 'go', markersize=6)
    ax1.annotate(f'最大弯度 {max_camber_val*100:.2f}%c',
                 xy=(max_camber_pos, max_camber_val),
                 xytext=(max_camber_pos-0.2, max_camber_val-0.05),
                 arrowprops=dict(arrowstyle="->", color='green'),
                 fontsize=9, color='green')
    ax1.set_xlabel('弦向位置 x/c')
    ax1.set_ylabel('y/c')
    ax1.set_title('翼型外形与中弧线')
    ax1.legend(loc='upper right')
    ax1.set_aspect('equal')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_xlim(0, 1)
    ax1.set_ylim(-0.5, 0.5)

    # 右上：厚度分布
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.fill_between(xu, 0, t, alpha=0.4, color='steelblue', label='厚度分布')
    ax2.plot(xu, t, 'b-', linewidth=2)
    ax2.axvline(max_t_pos, color='r', linestyle='--')
    ax2.scatter([max_t_pos], [max_t_val], color='red', s=40, zorder=5)
    ax2.set_xlabel('弦向位置 x/c')
    ax2.set_ylabel('厚度 t/c')
    ax2.set_title('弦向厚度分布')
    ax2.legend()
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_xlim(0, 1)
    ax2.set_ylim(bottom=0)

    # 下方：翼型数据表
    ax3 = fig.add_subplot(gs[1, :])
    ax3.axis('off')
    table_data = [
        ["参数", "数值"],
        ["最大厚度", f"{max_t_val*100:.3f}%c"],
        ["最大厚度位置", f"{max_t_pos*100:.1f}%c"],
        ["最大弯度", f"{max_camber_val*100:.3f}%c"],
        ["最大弯度位置", f"{max_camber_pos*100:.1f}%c"],
        ["翼型名称", title]
    ]
    table = ax3.table(cellText=table_data, cellLoc='left', loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.5)
    ax3.set_title('翼型参数', fontsize=12, fontweight='bold')

    plt.tight_layout()
    return fig
