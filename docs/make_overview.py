"""IEV CloudLab 系统总览图 | System overview figures.

图1 系统架构图（五层） | Fig1: Layered architecture
图2 数据流与工作流图（三链 + 成绩流 + 双角色流） | Fig2: Data & workflows
英文标签（matplotlib无中文字体），中文释义见配套说明文档。
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

OUT = os.path.dirname(os.path.abspath(__file__))


def box(ax, x, y, w, h, text, fc, ec='#37474F', fs=9, bold=False, tc='black'):
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.03',
                       fc=fc, ec=ec, lw=1.2)
    ax.add_patch(b)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, fontweight='bold' if bold else 'normal', color=tc)
    return b


def arrow(ax, p1, p2, color='#37474F', style='->', lw=1.4, rad=0.0):
    a = FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=13,
                        color=color, lw=lw,
                        connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(a)
    return a


def layer_label(ax, x, y, text, color):
    ax.text(x, y, text, ha='left', va='center', fontsize=11,
            fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, lw=1.2))


# ============================================================ 图1 架构
def fig_architecture():
    fig, ax = plt.subplots(figsize=(13, 9.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9.5)
    ax.axis('off')
    ax.text(6.5, 9.25, 'IEV CloudLab - System Architecture',
            ha='center', fontsize=16, fontweight='bold')

    # ---- 接入层 ----
    layer_label(ax, 0.15, 8.55, 'ACCESS', '#6A1B9A')
    box(ax, 0.6, 8.0, 3.6, 0.95, 'Students / Teachers\n(browser, zero install)',
        '#F3E5F5', '#6A1B9A', 9.5)
    box(ax, 4.7, 8.0, 3.6, 0.95, 'Cloudflare\nTunnel + DNS + CDN', '#F3E5F5',
        '#6A1B9A', 9.5)
    box(ax, 8.8, 8.0, 3.6, 0.95, 'ievlab.aisai.cc\n(HTTPS)', '#F3E5F5',
        '#6A1B9A', 9.5, bold=True)
    arrow(ax, (4.2, 8.47), (4.7, 8.47), '#6A1B9A')
    arrow(ax, (8.3, 8.47), (8.8, 8.47), '#6A1B9A')

    # ---- 平台层 ----
    layer_label(ax, 0.15, 7.35, 'PLATFORM (VPS)', '#1565C0')
    box(ax, 0.6, 6.35, 5.6, 0.95, 'JupyterHub 5.5.3\nEmail-OTP login | DockerSpawner (per-user container)',
        '#E3F2FD', '#1565C0', 9.5)
    box(ax, 6.8, 6.35, 5.6, 0.95, 'Student Container (iev-base image)\nUbuntu 24.04 | Python 3.12 + py310-fastsim kernel',
        '#E3F2FD', '#1565C0', 9.5)
    arrow(ax, (10.6, 8.0), (10.6, 7.3), '#1565C0')
    arrow(ax, (10.6, 7.3), (9.6, 7.3), '#1565C0')
    arrow(ax, (9.6, 7.3), (9.6, 7.3), '#1565C0')
    arrow(ax, (6.2, 6.82), (6.8, 6.82), '#1565C0')

    # ---- 实验层 ----
    layer_label(ax, 0.15, 5.9, 'EXPERIMENTS (29)', '#2E7D32')
    mods = [
        ('A x5\nADAS\n(esmini)', '#E8F5E9'),
        ('B x5\nTraffic\n(SUMO)', '#E8F5E9'),
        ('C x4\nVehicle\n(FASTSim)', '#E8F5E9'),
        ('D x4\nBattery\n(PyBaMM)', '#E8F5E9'),
        ('E x4\nOptimize\n(pymoo/CasADi)', '#E8F5E9'),
        ('F x3\nFMI\n(FMPy)', '#E8F5E9'),
        ('G x2\nROS 2\n(rclpy)', '#E8F5E9'),
        ('H x2\nScenarios\n(scenariogen.)', '#E8F5E9'),
    ]
    x = 0.6
    for name, fc in mods:
        box(ax, x, 4.75, 1.42, 1.0, name, fc, '#2E7D32', 8)
        x += 1.52
    ax.text(6.5, 4.52, 'Each experiment: Principles | Objectives | Tasks | Verification | Result Analysis | Troubleshooting (bilingual)',
            ha='center', fontsize=9, style='italic', color='#2E7D32')

    # ---- 支撑层 ----
    layer_label(ax, 0.15, 4.05, 'SUPPORT (labs/)', '#E65100')
    box(ax, 0.6, 3.0, 3.8, 0.95, 'common/\ncontroller | esmini_env | battery_adapter\nvehicle_library | diagrams (8 schematics)',
        '#FFF3E0', '#E65100', 8)
    box(ax, 4.6, 3.0, 3.8, 0.95, 'scenarios/\nStandard scenario definitions\n(.xosc / .xodr / .yaml)',
        '#FFF3E0', '#E65100', 8.5)
    box(ax, 8.6, 3.0, 3.8, 0.95, 'data/\nvehicles/ | batteries/ | results/\n(shared, chainable)',
        '#FFF3E0', '#E65100', 8.5)

    # ---- 引擎层 ----
    layer_label(ax, 0.15, 2.6, 'ENGINES', '#AD1457')
    box(ax, 0.6, 1.6, 11.8, 0.9,
        'esmini 3.10  |  SUMO 1.18 (TraCI)  |  FASTSim 2.1.5  |  PyBaMM 26.6\nCasADi 3.7 + IPOPT  |  pymoo 0.6.2  |  FMPy 0.3.22  |  ROS 2 Jazzy',
        '#FCE4EC', '#AD1457', 9.5, bold=True)

    # ---- 管理层 ----
    layer_label(ax, 0.15, 1.2, 'TEACHING MGMT', '#00695C')
    box(ax, 0.6, 0.25, 3.8, 0.85, 'evaluator.py\nAuto-grading (29 specs,\nverified thresholds)',
        '#E0F2F1', '#00695C', 8.5)
    box(ax, 4.6, 0.25, 3.8, 0.85, 'Teacher Dashboard\nGrades | Statistics | Charts\nRoster mgmt + archive',
        '#E0F2F1', '#00695C', 8.5)
    box(ax, 8.6, 0.25, 3.8, 0.85, 'collect_grades.py (cron)\nHourly aggregation\nGitHub: itskys/iev-cloudlab',
        '#E0F2F1', '#00695C', 8.5)

    # vertical flow arrows (left margin)
    for y1, y2 in [(8.0, 7.3), (6.35, 5.75), (4.75, 3.95), (3.0, 2.5), (1.6, 1.1)]:
        arrow(ax, (0.38, y1), (0.38, y2), '#90A4AE', lw=1.6)

    path = os.path.join(OUT, 'fig1_architecture.png')
    fig.savefig(path, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return path


# ============================================================ 图2 数据流+工作流
def fig_dataflow():
    fig, ax = plt.subplots(figsize=(13, 10))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.text(6.5, 9.75, 'IEV CloudLab - Data Flow & Workflows',
            ha='center', fontsize=16, fontweight='bold')

    # ---------- 三条链 ----------
    ax.text(0.2, 9.3, 'THREE CHAINS (any entry, full chain out)', fontsize=12,
            fontweight='bold', color='#1565C0')

    # Chain 1
    ax.text(0.2, 8.85, 'Chain 1  Vehicle Design:', fontsize=10.5,
            fontweight='bold', color='#2E7D32')
    box(ax, 1.6, 8.15, 2.1, 0.62, 'D3 PyBaMM\ncalibration', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 4.3, 8.15, 2.1, 0.62, 'batteries/*.csv\nOCV-SOC', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 7.0, 8.15, 2.1, 0.62, 'C1/C2 FASTSim\n(+ Adapter)', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 9.7, 8.15, 2.1, 0.62, 'vehicles/*.yaml', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 10.6, 7.3, 2.1, 0.62, 'A1-A4 esmini\nADAS tests', '#E8F5E9', '#2E7D32', 8.5)
    for p1, p2 in [((3.7, 8.46), (4.3, 8.46)), ((6.4, 8.46), (7.0, 8.46)),
                   ((9.1, 8.46), (9.7, 8.46))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (10.75, 8.15), (11.2, 7.92), '#2E7D32')

    # Chain 2
    ax.text(0.2, 7.55, 'Chain 2  Algorithm Dev:', fontsize=10.5,
            fontweight='bold', color='#2E7D32')
    box(ax, 1.6, 6.55, 2.1, 0.62, 'BaseController\n(common)', '#E3F2FD', '#1565C0', 8.5)
    box(ax, 4.3, 6.55, 2.1, 0.62, 'A / B closed loop\nesmini / TraCI', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 7.0, 6.55, 2.1, 0.62, 'Metrics\nTTC / error / PET', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 9.7, 6.55, 2.1, 0.62, 'Tune & iterate\nresults/*.json', '#E3F2FD', '#1565C0', 8.5)
    for p1, p2 in [((3.7, 6.86), (4.3, 6.86)), ((6.4, 6.86), (7.0, 6.86)),
                   ((9.1, 6.86), (9.7, 6.86))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (10.75, 6.55), (5.4, 6.35), '#90A4AE', lw=1.1, rad=-0.25)
    ax.text(8.0, 6.08, 'feedback: retune controller', fontsize=8.5,
            color='#607D8B', style='italic', ha='center')

    # Chain 3
    ax.text(0.2, 5.85, 'Chain 3  Energy Mgmt:', fontsize=10.5,
            fontweight='bold', color='#2E7D32')
    box(ax, 1.6, 5.05, 2.1, 0.62, 'E2/E4 optimize\npymoo / DP', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 4.3, 5.05, 2.1, 0.62, 'Optimal params\n/ strategy', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 7.0, 5.05, 2.1, 0.62, 'C4 FASTSim\nvalidation', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 9.7, 5.05, 2.1, 0.62, 'Report card\nresults/*.json', '#E3F2FD', '#1565C0', 8.5)
    for p1, p2 in [((3.7, 5.36), (4.3, 5.36)), ((6.4, 5.36), (7.0, 5.36)),
                   ((9.1, 5.36), (9.7, 5.36))]:
        arrow(ax, p1, p2, '#2E7D32')

    # ---------- 成绩流 ----------
    ax.text(0.2, 4.45, 'GRADING FLOW', fontsize=12, fontweight='bold',
            color='#AD1457')
    box(ax, 0.6, 3.55, 2.3, 0.7, 'Student runs\nexperiment', '#FCE4EC', '#AD1457', 9)
    box(ax, 3.4, 3.55, 2.3, 0.7, 'save_result()\nresults/*.json', '#FFF8E1', '#F9A825', 9)
    box(ax, 6.2, 3.55, 2.3, 0.7, 'collect_grades.py\nhourly cron (host)', '#FCE4EC', '#AD1457', 9)
    box(ax, 9.0, 3.55, 2.3, 0.7, 'evaluator +\ngradebook', '#FCE4EC', '#AD1457', 9)
    box(ax, 10.6, 2.6, 2.3, 0.7, 'Teacher Dashboard\ntable/stats/charts', '#E0F2F1', '#00695C', 9)
    for p1, p2 in [((2.9, 3.9), (3.4, 3.9)), ((5.7, 3.9), (6.2, 3.9)),
                   ((8.5, 3.9), (9.0, 3.9))]:
        arrow(ax, p1, p2, '#AD1457')
    arrow(ax, (11.0, 3.55), (11.6, 3.3), '#AD1457')
    ax.text(6.5, 3.28, 'Anti-cheat: min-steps criteria + execution timeout watchdog',
            ha='center', fontsize=8.5, color='#AD1457', style='italic')

    # ---------- 双角色工作流 ----------
    ax.text(0.2, 2.35, 'WORKFLOWS', fontsize=12, fontweight='bold', color='#00695C')
    box(ax, 0.6, 1.45, 11.8, 0.62,
        'Student:  Email-OTP login  >  Pick experiment  >  Read principles (+ schematics)  >  Run & tune (Try-It)  >  Self-check score  >  Lab report',
        '#E0F2F1', '#00695C', 9.5)
    box(ax, 0.6, 0.65, 11.8, 0.62,
        'Teacher:  Roster (add / CSV import)  >  Teach with 3 chains  >  View grades + charts  >  Identify weak experiments  >  Archive (course done)',
        '#FFF3E0', '#E65100', 9.5)
    box(ax, 0.6, 0.08, 11.8, 0.45,
        'Honesty by design: real engines only; stand-ins labeled; A-series target-freeze disclosed in every affected notebook',
        'white', '#90A4AE', 9)

    path = os.path.join(OUT, 'fig2_dataflow.png')
    fig.savefig(path, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return path


if __name__ == '__main__':
    for p in [fig_architecture(), fig_dataflow()]:
        print('Generated:', p, os.path.getsize(p), 'bytes')
