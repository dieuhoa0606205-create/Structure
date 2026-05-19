"""
全翼展弯矩/剪力分布可视化 (根部汇总版 · 完整注释)
功能: 绘制全翼展对称双轴弯矩和剪力分布图, 根部集中显示最大弯矩和剪力数值,
      旋翼和翼梢仅保留位置线, 避免文字重叠, 提供专业配色与网格。
作者: AeroStructCalc 团队
版本: 3.0 (2026-05-19)
"""

# 导入所需库
import matplotlib.pyplot as plt             # 绘图核心
import numpy as np                          # 数值计算
from matplotlib.ticker import AutoMinorLocator  # 自动次刻度

# ============================================================================
# 全局绘图参数设置
# 这些参数控制曲线的颜色、线宽、填充透明度等，可根据需要调整。
# ============================================================================
COLOR_SHEAR = '#1f77b4'          # 剪力曲线颜色 (蓝色)
COLOR_MOMENT = '#d62728'         # 弯矩曲线颜色 (红色)
COLOR_GUST_SHEAR = '#1f77b4'     # 突风剪力预留色
COLOR_GUST_MOMENT = '#d62728'    # 突风弯矩预留色
GRID_MAJOR_COLOR = '#cccccc'     # 主网格线颜色
GRID_MINOR_COLOR = '#e0e0e0'     # 次网格线颜色
FILL_ALPHA = 0.1                 # 曲线下方填充的透明度
LINE_WIDTH = 2.5                 # 曲线线宽
FONT_FAMILY = ['Arial', 'DejaVu Sans', 'Microsoft YaHei', 'SimHei']  # 字体族

# ============================================================================
# 基础样式设置函数
# ============================================================================
def set_global_style():
    """
    设置 matplotlib 的全局字体和样式。
    该函数在绘图前被调用，确保所有文字使用统一的字体族，
    并正确处理负号显示。
    """
    plt.rcParams['font.family'] = FONT_FAMILY
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['axes.linewidth'] = 1.2
    plt.rcParams['xtick.major.width'] = 1.0
    plt.rcParams['ytick.major.width'] = 1.0

def apply_axis_style(ax):
    """
    对单个坐标轴应用专业的网格和刻度样式。
    包括主次网格线、次刻度，使图表更易读。
    """
    ax.grid(True, which='major', linestyle='-', linewidth=0.7, color=GRID_MAJOR_COLOR, alpha=0.8)
    ax.grid(True, which='minor', linestyle=':', linewidth=0.4, color=GRID_MINOR_COLOR, alpha=0.5)
    ax.minorticks_on()
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax.yaxis.set_minor_locator(AutoMinorLocator(4))

def format_engineering(value, unit, precision=0):
    """
    将数值转换为带工程单位的字符串，便于阅读。
    例如: format_engineering(123456, 'N') -> '123.5 kN'
    """
    if abs(value) >= 1e6:
        return f"{value/1e6:.{precision}f} M{unit}"
    elif abs(value) >= 1e3:
        return f"{value/1e3:.{precision}f} k{unit}"
    else:
        return f"{value:.{precision}f} {unit}"

# ============================================================================
# 气动载荷计算函数 (基于椭圆升力分布)
# ============================================================================
def elliptic_load(WTO, kL, b, y):
    """
    计算椭圆升力分布下，展向位置 y 处的单位展长升力 (N/m)。
    参数:
        WTO: 起飞重量 (N)
        kL: 气囊升力占比
        b: 展长 (m)
        y: 展向坐标数组 (m)，半翼展范围内
    返回:
        l: 单位展长升力数组
    """
    L_wing = (1 - kL) * WTO          # 机翼承担的总升力
    half = b / 2.0                   # 半翼展
    ratio = np.clip(1 - (y / half)**2, 0, None)  # 椭圆方程
    return (2 * L_wing / (np.pi * b)) * np.sqrt(ratio)

def shear_and_moment_elliptic(WTO, kL, b, y):
    """
    计算椭圆升力分布下，展向位置 y 处的剪力 (N) 和弯矩 (N·m)。
    采用梯形数值积分。
    参数:
        WTO, kL, b: 同 elliptic_load
        y: 展向坐标数组 (从0到半翼展)
    返回:
        V: 剪力数组
        M: 弯矩数组
    """
    l_func = elliptic_load(WTO, kL, b, y)  # 单位展长升力
    V = np.zeros_like(y)
    M = np.zeros_like(y)
    for i in range(len(y)):
        mask = y >= y[i]                   # 积分区间: 从当前点到翼梢
        if len(y[mask]) > 1:
            V[i] = np.trapezoid(l_func[mask], y[mask])
            M[i] = np.trapezoid(l_func[mask] * (y[mask] - y[i]), y[mask])
    return V, M

# ============================================================================
# 全翼展对称扩展
# ============================================================================
def make_symmetric(y_half, V_half, M_half):
    """
    将半翼展 (0 到 b/2) 的剪力和弯矩数据对称扩展到全翼展 (-b/2 到 b/2)。
    由于载荷对称，剪力镜像不变，弯矩镜像也不变。
    """
    y_neg = -y_half[::-1]
    V_neg = V_half[::-1]
    M_neg = M_half[::-1]
    y_full = np.concatenate([y_neg, y_half])
    V_full = np.concatenate([V_neg, V_half])
    M_full = np.concatenate([M_neg, M_half])
    return y_full, V_full, M_full

# ============================================================================
# 标注函数 (根部汇总, 旋翼/翼梢仅位置线)
# ============================================================================
def draw_root_annotation(ax, V_root, M_root):
    """
    在根部 (y=0) 绘制垂直虚线，并使用带引线的文本框
    标注根部的剪力和弯矩数值。文字放置在图表左上方，避免遮挡曲线。
    """
    ax.axvline(x=0, color='gray', linestyle='--', linewidth=1.5, alpha=0.6)
    ax.annotate(
        f'根部截面\nV = {format_engineering(V_root, "N")}\nM = {format_engineering(M_root, "N·m")}',
        xy=(0, V_root * 0.9 if V_root != 0 else 0),
        xytext=(-120, 60), textcoords='offset points',
        fontsize=9, ha='center',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9, edgecolor='gray'),
        arrowprops=dict(arrowstyle='->', color='gray', lw=1.2)
    )

def draw_rotor_annotation(ax, yR):
    """
    在左右旋翼安装位置 (y = ±yR) 绘制竖直虚线，并添加 '旋翼' 文字标签。
    不显示弯矩数值，以减少图形负担。
    """
    for sign in [-1, 1]:
        yr = sign * yR
        ax.axvline(x=yr, color='orange', linestyle='--', linewidth=1.2, alpha=0.8)
        ax.text(yr, ax.get_ylim()[1]*0.15, '旋翼', rotation=90, va='bottom', ha='right',
                fontsize=8, color='darkorange')

def draw_tip_annotation(ax, half_span):
    """
    在翼梢 (y = ±half_span) 绘制竖直虚线，并添加 '翼梢' 文字标签。
    """
    for sign in [-1, 1]:
        yt = sign * half_span
        ax.axvline(x=yt, color='green', linestyle=':', linewidth=1.2, alpha=0.8)
        ax.text(yt, 0, '翼梢', rotation=90, va='bottom', ha='right', fontsize=8, color='darkgreen')

def draw_max_moment_annotation(ax, y_full, M_full):
    """
    在全翼展弯矩分布中找到最大弯矩点，并绘制一个红色圆点标记。
    不显示具体数值，因为根部已经汇总显示了最大弯矩值。
    """
    idx = np.argmax(M_full)
    y_max = y_full[idx]
    M_max = M_full[idx]
    ax.scatter(y_max, M_max, color='red', s=60, zorder=5)

# ============================================================================
# 辅助信息与图例
# ============================================================================
def add_footer_info(fig, WTO, kL, b, cw, V_cruise, wing_area, n_design):
    """
    在图表底部添加一行关键参数信息，便于查看当前设计条件。
    """
    text = (f"起飞重量: {WTO:.1f} N | 气囊占比: {kL*100:.0f}% | "
            f"展长: {b:.2f} m | 弦长: {cw:.2f} m | 翼面积: {wing_area:.2f} m² | "
            f"巡航速度: {V_cruise:.1f} m/s | 设计过载: {n_design:.2f}")
    fig.text(0.5, 0.01, text, ha='center', fontsize=9,
             bbox=dict(boxstyle='round,pad=0.4', facecolor='whitesmoke', alpha=0.7))

def add_combined_legend(ax1, ax2):
    """
    将左右轴的图例合并，统一显示在图表右上角，使图面更整洁。
    """
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right',
               framealpha=0.9, fontsize=10)

# ============================================================================
# 主绘图函数
# ============================================================================
def plot_full_span_moment(loads_dict, WTO, kL, b, cw, V_cruise):
    """
    绘制全翼展弯矩与剪力分布图 (专业版 · 根部汇总)。
    参数:
        loads_dict (dict): 载荷字典，必须包含 'M_root', 'V_root', 'yR', 'n_design'
        WTO (float): 起飞重量 (N)
        kL (float): 气囊升力占比
        b (float): 展长 (m)
        cw (float): 弦长 (m)
        V_cruise (float): 巡航速度 (m/s)
    返回:
        fig (matplotlib Figure): 绘制好的图表对象
    """
    # 设置全局字体
    set_global_style()

    # 从载荷字典中提取关键参数
    M_root = loads_dict.get('M_root', 0)
    V_root = loads_dict.get('V_root', 0)
    yR = loads_dict.get('yR', b/2 + 1.0)  # 旋翼展向位置
    n_design = loads_dict.get('n_design', 1.0)

    # 半翼展计算网格 (400个点，保证曲线平滑)
    half_span = b / 2.0
    y_half = np.linspace(0, half_span, 400)

    # 使用椭圆分布模型计算剪力和弯矩
    V_half, M_half = shear_and_moment_elliptic(WTO, kL, b, y_half)

    # 对称扩展至全翼展
    y_full, V_full, M_full = make_symmetric(y_half, V_half, M_half)

    # 创建图像和双轴
    fig, ax1 = plt.subplots(figsize=(16, 7))
    ax2 = ax1.twinx()
    apply_axis_style(ax1)  # 应用网格和刻度样式

    # ---- 绘制剪力曲线 (左轴) ----
    ax1.plot(y_full, V_full, color=COLOR_SHEAR, linewidth=LINE_WIDTH, label='剪力 V')
    ax1.fill_between(y_full, V_full, alpha=FILL_ALPHA, color=COLOR_SHEAR)
    ax1.set_xlabel('展向位置 y (m)', fontsize=13)
    ax1.set_ylabel('剪力 (N)', color=COLOR_SHEAR, fontsize=13)
    ax1.tick_params(axis='y', labelcolor=COLOR_SHEAR)

    # ---- 绘制弯矩曲线 (右轴) ----
    ax2.plot(y_full, M_full, color=COLOR_MOMENT, linewidth=LINE_WIDTH, label='弯矩 M')
    ax2.fill_between(y_full, M_full, alpha=FILL_ALPHA, color=COLOR_MOMENT)
    ax2.set_ylabel('弯矩 (N·m)', color=COLOR_MOMENT, fontsize=13)
    ax2.tick_params(axis='y', labelcolor=COLOR_MOMENT)

    # ---- 添加关键位置标注 ----
    draw_root_annotation(ax1, V_root, M_root)     # 根部 (中心线) 集中显示弯矩和剪力
    draw_rotor_annotation(ax1, yR)                 # 旋翼位置
    draw_tip_annotation(ax1, half_span)            # 翼梢位置
    draw_max_moment_annotation(ax2, y_full, M_full) # 最大弯矩点

    # ---- 图例、标题、辅助信息 ----
    add_combined_legend(ax1, ax2)
    ax1.set_title('全翼展弯矩与剪力分布（设计载荷）', fontsize=16, fontweight='bold')

    wing_area = b * cw
    add_footer_info(fig, WTO, kL, b, cw, V_cruise, wing_area, n_design)

    # 自动调整布局，避免文字被裁剪
    plt.tight_layout(rect=[0, 0.06, 1, 0.96])
    return fig

# ============================================================================
# 兼容旧版调用接口
# ============================================================================
def plot_moment_distribution(loads_dict, WTO, kL, b, bfuse=None, cw=1.2, V_cruise=10.0):
    """
    旧版本兼容函数，直接调用新的全翼展绘图函数。
    bfuse 参数已不再使用，仅保留以兼容旧代码调用。
    """
    return plot_full_span_moment(loads_dict, WTO, kL, b, cw, V_cruise)