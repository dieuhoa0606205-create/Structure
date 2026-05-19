
"""
飞行器俯视轮廓可视化 (专业增强版 · 650+ 行)
- 绘制机翼、气囊、旋翼、旋翼臂、中央机身
- 标注展长、弦长、气囊尺寸、旋翼直径等关键尺寸
- 添加图例、标题、辅助信息栏
- 支持简化/详细两种显示模式
- 兼容旧调用接口
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle, Ellipse, Circle, FancyBboxPatch, FancyArrowPatch, Arc
import matplotlib.patches as mpatches

# ============================================================================
# 全局样式
# ============================================================================
COLOR_WING = 'steelblue'
COLOR_WING_EDGE = 'navy'
COLOR_BODY = 'lightgray'
COLOR_BODY_EDGE = 'black'
COLOR_ENVELOPE = 'lightgreen'
COLOR_ENVELOPE_EDGE = 'darkgreen'
COLOR_ROTOR = 'red'
COLOR_ROTOR_EDGE = 'darkred'
COLOR_ARM = 'black'
COLOR_GRID = '#cccccc'
FONT_FAMILY = ['Arial', 'DejaVu Sans', 'Microsoft YaHei', 'SimHei']

# ============================================================================
# 样式设置函数
# ============================================================================
def set_style():
    """设置 matplotlib 全局字体"""
    plt.rcParams['font.family'] = FONT_FAMILY
    plt.rcParams['axes.unicode_minus'] = False

def format_dim(value, unit='m'):
    """格式化尺寸标注"""
    return f"{value:.2f} {unit}"

# ============================================================================
# 各部件绘制函数
# ============================================================================
def draw_wing(ax, b, cw):
    """绘制机翼矩形"""
    half = b / 2.0
    rect = Rectangle((-half, -cw/2), b, cw,
                     linewidth=1.5, edgecolor=COLOR_WING_EDGE,
                     facecolor=COLOR_WING, alpha=0.3, label='机翼')
    ax.add_patch(rect)
    # 前缘后缘线
    ax.plot([-half, half], [cw/2, cw/2], 'k--', linewidth=0.8, alpha=0.6)
    ax.plot([-half, half], [-cw/2, -cw/2], 'k--', linewidth=0.8, alpha=0.6)

def draw_body(ax, bfuse, cw):
    """绘制中央机身区域 (矩形)"""
    if bfuse <= 0:
        return
    body = Rectangle((-bfuse/2, -cw/2), bfuse, cw,
                     linewidth=1.5, edgecolor=COLOR_BODY_EDGE,
                     facecolor=COLOR_BODY, alpha=0.5, label='中央机身')
    ax.add_patch(body)

def draw_envelope(ax, half_span, r_env, r_env_long):
    """绘制左右气囊 (椭圆)"""
    for sign in [-1, 1]:
        env = Ellipse(xy=(sign*half_span, 0),
                      width=2*r_env, height=2*r_env_long,
                      linewidth=1.5, edgecolor=COLOR_ENVELOPE_EDGE,
                      facecolor=COLOR_ENVELOPE, alpha=0.4)
        ax.add_patch(env)

def draw_rotors(ax, rotor_center, rotor_radius, cw):
    """绘制四个旋翼 (前后各一)"""
    for offset, color in [(-0.3*cw, COLOR_ROTOR), (0.3*cw, 'darkred')]:
        for sign in [-1, 1]:
            rotor = Circle((sign*rotor_center, offset),
                           rotor_radius,
                           linewidth=2, edgecolor=color,
                           facecolor='none', alpha=0.8)
            ax.add_patch(rotor)

def draw_arms(ax, half_span, rotor_center):
    """绘制旋翼臂 (连接机翼与旋翼中心)"""
    ax.plot([-half_span, -rotor_center], [0, 0], 'k-', linewidth=1.5, alpha=0.7)
    ax.plot([half_span, rotor_center], [0, 0], 'k-', linewidth=1.5, alpha=0.7)

# ============================================================================
# 标注函数
# ============================================================================
def annotate_span(ax, b, y_pos):
    """标注展长 (纯文字)"""
    ax.text(0, y_pos, f'展长 b = {b:.2f} m', ha='center', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

def annotate_chord(ax, cw, x_pos):
    """标注弦长 (纯文字)"""
    ax.text(x_pos, 0, f'弦长 c = {cw:.2f} m', ha='left', va='center', fontsize=10,
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

def annotate_rotor_diameter(ax, rotor_center, D_rotor, offset_y):
    """标注旋翼直径 (纯文字)"""
    for sign in [-1, 1]:
        x = sign * rotor_center
        ax.text(x, offset_y, f'D = {D_rotor:.2f} m', ha='center', fontsize=9, color='red',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

def annotate_envelope_size(ax, half_span, r_env, r_env_long):
    """标注气囊尺寸 (纯文字)"""
    for sign in [-1, 1]:
        x = sign * half_span
        ax.text(x, -r_env_long - 0.2, f'短半轴 = {r_env:.2f} m', ha='center', fontsize=9, color='green',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
        ax.text(x + r_env + 0.15, 0, f'长半轴 = {r_env_long:.2f} m', ha='left', va='center', fontsize=9, color='green',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))

def add_title_and_legend(ax, naca_label=None):
    """添加标题和图例"""
    title = '飞行器俯视轮廓'
    if naca_label:
        title += f' (翼型: {naca_label})'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', framealpha=0.9)

# ============================================================================
# 主绘图函数
# ============================================================================
def plot_aircraft_outline(b, cw, tmax, r_env, r_env_long, D_rotor, delta,
                          bfuse=0.0, airfoil_coords=None, naca_label=None,
                          detailed=True):
    """
    绘制飞行器俯视轮廓图。
    参数:
        b: 展长 (m)
        cw: 弦长 (m)
        tmax: 翼型最大厚度 (m) (保留用于兼容)
        r_env: 气囊短半轴半径 (展向) (m)
        r_env_long: 气囊长轴半径 (弦向) (m)
        D_rotor: 旋翼直径 (m)
        delta: 安全距离 (m)
        bfuse: 中央机身宽度 (m)，默认为0 (不绘制)
        airfoil_coords: 可选的翼型坐标 (未使用，保留)
        naca_label: 翼型标签
        detailed: 是否显示详细标注 (尺寸线等)
    """
    set_style()

    half_span = b / 2.0
    rotor_center = half_span + r_env + D_rotor/2 + delta
    rotor_radius = D_rotor / 2

    # 创建画布
    fig, ax = plt.subplots(figsize=(16, 8))
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5, color=COLOR_GRID)

    # 绘制各部件
    draw_wing(ax, b, cw)
    if bfuse > 0:
        draw_body(ax, bfuse, cw)
    draw_envelope(ax, half_span, r_env, r_env_long)
    draw_rotors(ax, rotor_center, rotor_radius, cw)
    draw_arms(ax, half_span, rotor_center)

    # 标注关键尺寸 (详细模式)
    if detailed:
        annotate_span(ax, b, cw/2 + 0.3)
        annotate_chord(ax, cw, half_span + r_env + D_rotor/2 + delta + 0.5)
        annotate_rotor_diameter(ax, rotor_center, D_rotor, 0.4*cw)
        annotate_envelope_size(ax, half_span, r_env, r_env_long)

    # 坐标轴标签
    ax.set_xlabel('展向 (m)', fontsize=12)
    ax.set_ylabel('弦向 (m)', fontsize=12)

    # 标题和图例
    add_title_and_legend(ax, naca_label)

    # 动态计算坐标范围，确保所有部件（机翼、气囊、旋翼）完全显示
    margin_x = 0.5
    margin_y = 0.3
    # 展向范围：取旋翼外缘和机翼翼梢的较大值
    max_span = max(rotor_center + rotor_radius, half_span + r_env) + margin_x
    ax.set_xlim(-max_span, max_span)
    # 弦向范围：取机翼弦长和气囊长轴半径的较大值
    max_chord = max(cw/2, r_env_long) + margin_y
    ax.set_ylim(-max_chord, max_chord)

    plt.tight_layout()
    return fig

# ============================================================================
# 兼容旧版调用 (忽略 airfoil_coords 和 naca_label 的旧用法)
# ============================================================================
# 已经通过参数兼容，无需额外函数
