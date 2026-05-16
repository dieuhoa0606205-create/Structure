
import matplotlib.pyplot as plt
import numpy as np

def plot_airfoil(xu, yu, xl, yl, title="翼型几何"):
    """绘制翼型形状并标注最大厚度位置"""
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.plot(xu, yu, 'b-', label='上表面')
    ax.plot(xl, yl, 'b-', label='下表面')
    ax.plot([0, 1], [0, 0], 'k--', linewidth=0.5)
    # 计算最大厚度位置及值
    t = yu - yl
    idx = np.argmax(t)
    max_pos = xu[idx]
    max_val = t[idx]
    ax.axvline(x=max_pos, color='r', linestyle='--', linewidth=0.8)
    ax.plot(max_pos, 0, 'ro')
    ax.text(max_pos, 0.02, f'{max_pos*100:.1f}% c\nmax t/c = {max_val*100:.1f}%',
            color='red', fontsize=9, ha='center')
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.5, 0.5)
    ax.set_aspect('equal')
    ax.set_xlabel('弦向位置 x/c')
    ax.set_ylabel('y/c')
    ax.set_title(title)
    ax.legend(loc='upper right')
    return fig
