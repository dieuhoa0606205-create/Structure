
import matplotlib.pyplot as plt
import numpy as np

def plot_aircraft_outline(b, bfuse, cw, tmax, r_env, D_rotor, delta):
    """绘制飞机俯视简化外轮廓"""
    fig, ax = plt.subplots(figsize=(10, 4))
    # 机身区域
    ax.barh(0, bfuse, height=cw*0.8, left=-bfuse/2, color='lightgray', label='中央机身')
    # 外翼
    wing_left = -b/2
    wing_right = b/2
    ax.barh(0, b, height=tmax, left=-b/2, color='steelblue', alpha=0.6, label='机翼')
    # 气囊 (两个椭圆形)
    env_left = -b/2 - r_env
    env_right = b/2 + r_env
    env_ellipse = plt.Circle((env_left, 0), r_env, color='lightgreen', alpha=0.5, label='气囊')
    ax.add_patch(env_ellipse)
    env_ellipse2 = plt.Circle((env_right, 0), r_env, color='lightgreen', alpha=0.5)
    ax.add_patch(env_ellipse2)
    # 旋翼
    rotor_left = env_left - D_rotor/2 - delta
    rotor_right = env_right + D_rotor/2 + delta
    ax.plot([rotor_left, rotor_left], [-D_rotor/2, D_rotor/2], 'r-', linewidth=3, label='旋翼')
    ax.plot([rotor_right, rotor_right], [-D_rotor/2, D_rotor/2], 'r-', linewidth=3)
    ax.set_xlim(-b, b)
    ax.set_ylim(-1, 1)
    ax.set_aspect('equal')
    ax.legend()
    ax.set_title('飞行器俯视轮廓示意图')
    return fig
