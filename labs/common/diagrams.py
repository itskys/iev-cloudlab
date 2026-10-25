"""IEV CloudLab 教学原理图库

为各实验提供可复用的原理图、示意图绘制函数。
所有图用英文标签（matplotlib无中文字体），函数docstring中英双语。

Reference projects:
- matplotlib examples: https://matplotlib.org/stable/gallery/
- python-control: block diagrams
- F1TENTH: vehicle diagrams
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# [优化 - 2026-10-25 给 Muse 说明]：
# 配置中文无衬线字体回退链与负号正常显示支持。
# 配合 iev-base 镜像预装的 fonts-noto-cjk / fonts-wqy-zenhei，图表可安全渲染中文字符而不出现豆腐块。
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def _setup(ax, title, xlabel='', ylabel=''):
    ax.set_title(title, fontsize=12, fontweight='bold')
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=10)
    ax.grid(True, alpha=0.3)


def _block(ax, xy, width, height, text, fc='#E8F4FD', ec='#2196F3'):
    """Draw a block diagram box."""
    box = FancyBboxPatch(xy, width, height, boxstyle="round,pad=0.02",
                         fc=fc, ec=ec, lw=1.5)
    ax.add_patch(box)
    ax.text(xy[0] + width/2, xy[1] + height/2, text,
            ha='center', va='center', fontsize=9, fontweight='bold')
    return box


def _arrow(ax, start, end, label='', color='#333'):
    """Draw an arrow between blocks."""
    arrow = FancyArrowPatch(start, end, arrowstyle='->', mutation_scale=15,
                            color=color, lw=1.5)
    ax.add_patch(arrow)
    if label:
        mx, my = (start[0]+end[0])/2, (start[1]+end[1])/2
        ax.text(mx, my+0.05, label, ha='center', fontsize=8, color=color)
    return arrow


# ==================== A系列：ADAS ====================

def aeb_block_diagram(save_path=None):
    """AEB系统框图 | AEB system block diagram."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    _block(ax, (0.3, 1.5), 1.7, 1.0, 'Radar/\nCamera')
    _block(ax, (2.5, 1.5), 1.7, 1.0, 'TTC\nCalculation')
    _block(ax, (4.7, 1.5), 1.7, 1.0, 'Decision\nLogic')
    _block(ax, (6.9, 1.5), 1.7, 1.0, 'Brake\nActuator')
    _arrow(ax, (2.0, 2.0), (2.5, 2.0), 'range, speed')
    _arrow(ax, (4.2, 2.0), (4.7, 2.0), 'TTC')
    _arrow(ax, (6.4, 2.0), (6.9, 2.0), 'brake cmd')
    ax.text(5, 3.2, 'AEB System Block Diagram', ha='center',
            fontsize=14, fontweight='bold')
    ax.text(5, 0.5, 'Sensor -> Compute TTC -> Decide -> Actuate',
            ha='center', fontsize=10, style='italic', color='#666')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


def ttc_principle(save_path=None):
    """TTC原理示意图 | TTC principle illustration."""
    fig, ax = plt.subplots(figsize=(8, 4))
    # Ego car
    ego = mpatches.Rectangle((1, 1.5), 1.5, 0.8, fc='#2196F3', ec='black')
    ax.add_patch(ego)
    ax.text(1.75, 1.9, 'Ego\nv_ego', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold')
    # Target car
    tgt = mpatches.Rectangle((5, 1.5), 1.5, 0.8, fc='#F44336', ec='black')
    ax.add_patch(tgt)
    ax.text(5.75, 1.9, 'Target\nv_tgt', ha='center', va='center',
            fontsize=9, color='white', fontweight='bold')
    # Distance arrow
    ax.annotate('', xy=(5, 1.2), xytext=(2.5, 1.2),
                arrowprops=dict(arrowstyle='<->', color='black', lw=1.5))
    ax.text(3.75, 0.9, 'd (distance)', ha='center', fontsize=10)
    # Formula
    ax.text(3.75, 3.0, r'TTC = d / (v_ego - v_tgt)',
            ha='center', fontsize=14,
            bbox=dict(boxstyle='round', fc='#FFF9C4'))
    ax.text(3.75, 2.5, 'if v_ego > v_tgt, else TTC = inf',
            ha='center', fontsize=9, color='#666')
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 4)
    ax.axis('off')
    ax.set_title('TTC Principle', fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


def acc_control_loop(save_path=None):
    """ACC控制闭环图 | ACC control loop."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    _block(ax, (0.5, 1.5), 1.5, 1.0, 'Desired\nGap')
    _block(ax, (2.8, 1.5), 1.5, 1.0, 'PD\nController')
    _block(ax, (5.1, 1.5), 1.5, 1.0, 'Vehicle\nDynamics')
    _block(ax, (7.4, 1.5), 1.5, 1.0, 'Sensor\n(Radar)')
    _arrow(ax, (2.0, 2.0), (2.8, 2.0), '')
    _arrow(ax, (4.3, 2.0), (5.1, 2.0), 'accel cmd')
    _arrow(ax, (6.6, 2.0), (7.4, 2.0), '')
    # Feedback
    ax.annotate('', xy=(1.25, 1.5), xytext=(8.15, 1.5),
                arrowprops=dict(arrowstyle='->', color='#F44336',
                                lw=1.5, connectionstyle='arc3,rad=0.3'))
    ax.text(4.7, 0.6, 'measured gap (feedback)', ha='center',
            fontsize=9, color='#F44336')
    ax.text(5, 3.2, 'ACC Closed-Loop Control', ha='center',
            fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


# ==================== C系列：车辆能量 ====================

def vehicle_forces(save_path=None):
    """车辆受力示意图 | Vehicle forces diagram."""
    fig, ax = plt.subplots(figsize=(9, 5))
    # Car body (side view)
    car = mpatches.Rectangle((3, 2), 3, 1.2, fc='#90CAF9',
                             ec='black', lw=2)
    ax.add_patch(car)
    # Wheels
    for wx in [3.6, 5.4]:
        wheel = plt.Circle((wx, 1.8), 0.4, fc='#333', ec='black')
        ax.add_patch(wheel)
    ax.text(4.5, 2.6, 'm', ha='center', fontsize=14, fontweight='bold')
    # Aero drag (opposing motion)
    ax.annotate('', xy=(3, 2.6), xytext=(1.5, 2.6),
                arrowprops=dict(arrowstyle='->', color='#F44336', lw=2))
    ax.text(1.0, 2.8, r'$F_{aero} = \frac{1}{2}\rho C_d A v^2$',
            fontsize=10, color='#F44336')
    # Rolling resistance
    ax.annotate('', xy=(4.5, 1.2), xytext=(3.0, 1.2),
                arrowprops=dict(arrowstyle='->', color='#FF9800', lw=2))
    ax.text(2.2, 0.8, r'$F_{rr} = C_{rr} m g$', fontsize=10, color='#FF9800')
    # Grade force
    ax.annotate('', xy=(6, 2.6), xytext=(7.5, 2.6),
                arrowprops=dict(arrowstyle='->', color='#4CAF50', lw=2))
    ax.text(7.8, 2.8, r'$F_{grade} = m g \sin\theta$', fontsize=10,
            color='#4CAF50')
    # Traction
    ax.annotate('', xy=(6, 1.8), xytext=(7.5, 1.8),
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2.5))
    ax.text(7.8, 1.6, r'$F_{trac}$', fontsize=12, color='#2196F3',
            fontweight='bold')
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4.5)
    ax.axis('off')
    ax.set_title('Vehicle Longitudinal Forces', fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


# ==================== D系列：电池 ====================

def battery_spm(save_path=None):
    """SPM单颗粒模型示意图 | Single Particle Model."""
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    # Negative electrode particle
    n_part = plt.Circle((2, 2), 0.8, fc='#9E9E9E', ec='black', lw=2)
    ax.add_patch(n_part)
    ax.text(2, 2, 'Li+', ha='center', va='center', fontsize=10,
            fontweight='bold')
    ax.text(2, 0.7, 'Negative\n(Graphite)', ha='center', fontsize=9)
    # Separator
    ax.add_patch(mpatches.Rectangle((3.5, 1), 0.3, 2, fc='#FFF9C4',
                                    ec='black'))
    ax.text(3.65, 0.7, 'Sep.', ha='center', fontsize=8)
    # Positive electrode particle
    p_part = plt.Circle((5.5, 2), 0.8, fc='#FFB74D', ec='black', lw=2)
    ax.add_patch(p_part)
    ax.text(5.5, 2, 'Li+', ha='center', va='center', fontsize=10,
            fontweight='bold')
    ax.text(5.5, 0.7, 'Positive\n(NMC)', ha='center', fontsize=9)
    # Li+ movement (discharge)
    ax.annotate('', xy=(4.7, 2.5), xytext=(2.8, 2.5),
                arrowprops=dict(arrowstyle='->', color='#2196F3', lw=2))
    ax.text(3.75, 2.8, 'Discharge', ha='center', fontsize=9, color='#2196F3')
    # Info
    ax.text(8, 2.5, 'SPM Assumptions:\n- 1 particle/electrode\n- No electrolyte\ndynamics\n- Fickian diffusion',
            fontsize=9, bbox=dict(boxstyle='round', fc='#E8F5E9'))
    ax.set_title('Single Particle Model (SPM)', fontsize=14, fontweight='bold')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


# ==================== E系列：优化 ====================

def mpc_horizon(save_path=None):
    """MPC预测时域示意图 | MPC prediction horizon."""
    fig, ax = plt.subplots(figsize=(9, 4))
    N = 10
    t = np.arange(N+1)
    # Past (solid)
    ax.plot([-2, -1, 0], [0, 0.5, 1.0], 'b-', lw=2.5, label='Past (applied)')
    # Predicted (dashed)
    t_pred = np.arange(0, N+1)
    x_pred = 1.0 + 0.5*t_pred - 0.02*t_pred**2
    ax.plot(t_pred, x_pred, 'r--', lw=2, label='Predicted (N steps)')
    # First control applied
    ax.plot([0, 1], [1.0, 1.48], 'g-', lw=3, label='1st control applied')
    ax.axvline(0, color='k', ls=':', label='Now')
    ax.axvspan(0, N, alpha=0.1, color='red')
    ax.text(N/2, ax.get_ylim()[1]*0.9 if ax.get_ylim()[1] else 5,
            'Prediction\nHorizon', ha='center', fontsize=10, color='#F44336')
    _setup(ax, 'MPC Receding Horizon', 'Time step', 'State')
    ax.legend(fontsize=9)
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


# ==================== F系列：FMI ====================

def fmi_architecture(save_path=None):
    """FMI架构图 | FMI architecture."""
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    _block(ax, (0.5, 1.5), 1.8, 1.0, 'FMU 1\n(Vehicle)', fc='#E3F2FD')
    _block(ax, (0.5, 0.3), 1.8, 1.0, 'FMU 2\n(Battery)', fc='#FFF3E0')
    _block(ax, (4.2, 1.0), 1.8, 1.2, 'Master\nAlgorithm', fc='#E8F5E9',
           ec='#4CAF50')
    _block(ax, (7.5, 1.0), 1.8, 1.2, 'FMPy\n(Simulator)', fc='#F3E5F5',
           ec='#9C27B0')
    _arrow(ax, (2.3, 2.0), (4.2, 1.8), 'v, x')
    _arrow(ax, (2.3, 0.8), (4.2, 1.4), 'V, I')
    _arrow(ax, (6.0, 1.6), (7.5, 1.6), 'doStep')
    ax.text(5, 3.2, 'FMI Co-Simulation Architecture', ha='center',
            fontsize=14, fontweight='bold')
    ax.text(5, 0.1, 'Each FMU: .xml + .so + resources | Master orchestrates time',
            ha='center', fontsize=9, color='#666', style='italic')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


# ==================== G系列：ROS ====================

def ros_pubsub(save_path=None):
    """ROS发布订阅图 | ROS pub/sub."""
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis('off')
    _block(ax, (0.5, 1.5), 1.8, 1.0, 'Publisher\nNode', fc='#E8F5E9',
           ec='#4CAF50')
    _block(ax, (4.1, 2.2), 1.8, 1.0, 'Topic\n/cmd_vel', fc='#FFF3E0',
           ec='#FF9800')
    _block(ax, (7.7, 1.5), 1.8, 1.0, 'Subscriber\nNode', fc='#E3F2FD',
           ec='#2196F3')
    _arrow(ax, (2.3, 2.0), (4.1, 2.7), 'publish')
    _arrow(ax, (5.9, 2.7), (7.7, 2.0), 'subscribe')
    ax.text(5, 3.5, 'ROS 2 Topic Communication', ha='center',
            fontsize=14, fontweight='bold')
    ax.text(5, 0.5, 'Decoupled: publisher does not know subscriber',
            ha='center', fontsize=10, color='#666', style='italic')
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    return fig


if __name__ == '__main__':
    import os
    outdir = '/home/hatch/workspace/ievlab/labs/common/diagram_outputs'
    os.makedirs(outdir, exist_ok=True)
    for name, fn in [
        ('aeb_block', aeb_block_diagram),
        ('ttc_principle', ttc_principle),
        ('acc_loop', acc_control_loop),
        ('vehicle_forces', vehicle_forces),
        ('battery_spm', battery_spm),
        ('mpc_horizon', mpc_horizon),
        ('fmi_arch', fmi_architecture),
        ('ros_pubsub', ros_pubsub),
    ]:
        fn(os.path.join(outdir, f'{name}.png'))
        print(f'Generated {name}.png')
    print('Done')
