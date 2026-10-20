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


def box(ax, x, y, w, h, text, fc, ec='#37474F', fs=9, bold=False, tc='black',
        ls='-'):
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.03',
                       fc=fc, ec=ec, lw=1.2, linestyle=ls)
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
    layer_label(ax, 0.15, 7.35, 'PLATFORM', '#1565C0')
    box(ax, 0.6, 6.35, 3.8, 0.95, 'JupyterHub 5.5.3 (VPS)\nEmail-OTP login\nDockerSpawner',
        '#E3F2FD', '#1565C0', 9)
    box(ax, 4.6, 6.35, 3.8, 0.95, 'Student Container (CPU)\niev-base image\nPython 3.12 + py310 kernel',
        '#E3F2FD', '#1565C0', 9)
    box(ax, 8.6, 6.35, 3.8, 0.95, 'GPU Pods (RunPod 4090)\nOn-demand | ievlab.submit()\nStage 2 - planned',
        '#EDE7F6', '#5E35B1', 9, ls='--')
    arrow(ax, (10.6, 8.0), (10.6, 7.3), '#1565C0')
    arrow(ax, (4.4, 6.82), (4.6, 6.82), '#1565C0')
    arrow(ax, (8.4, 6.82), (8.6, 6.82), '#5E35B1')

    # ---- 实验层 ----
    layer_label(ax, 0.15, 5.9, 'EXPERIMENTS (29 live + 5 GPU planned)', '#2E7D32')
    mods = [
        ('A x5\nADAS\n(esmini)', '#E8F5E9', '#2E7D32', '-'),
        ('B x5\nTraffic\n(SUMO)', '#E8F5E9', '#2E7D32', '-'),
        ('C x4\nVehicle\n(FASTSim)', '#E8F5E9', '#2E7D32', '-'),
        ('D x4\nBattery\n(PyBaMM)', '#E8F5E9', '#2E7D32', '-'),
        ('E x4\nOptimize\n(pymoo)', '#E8F5E9', '#2E7D32', '-'),
        ('F x3\nFMI\n(FMPy)', '#E8F5E9', '#2E7D32', '-'),
        ('G x2\nROS 2\n(rclpy)', '#E8F5E9', '#2E7D32', '-'),
        ('H x2\nScenarios\n(gen.)', '#E8F5E9', '#2E7D32', '-'),
        ('I x5\nPerception+AD\n(CARLA, GPU)', '#EDE7F6', '#5E35B1', '--'),
    ]
    x = 0.6
    for name, fc, ec, ls in mods:
        box(ax, x, 4.75, 1.24, 1.0, name, fc, ec, 7.5, ls=ls)
        x += 1.317
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
        'esmini 3.10  |  SUMO 1.18 (TraCI)  |  FASTSim 2.1.5  |  PyBaMM 26.6  |  CasADi 3.7  |  pymoo 0.6.2  |  FMPy 0.3.22  |  ROS 2 Jazzy\n+ Stage 2 (GPU): CARLA 0.9.16  |  AWSIM  |  Autoware  |  YOLO',
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
    fig, ax = plt.subplots(figsize=(13, 11.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 11.5)
    ax.axis('off')
    ax.text(6.5, 11.25, 'IEV CloudLab - Data Flow & Workflows',
            ha='center', fontsize=16, fontweight='bold')

    # ---------- chains ----------
    ax.text(0.2, 10.8, 'FOUR CHAINS (any entry, full chain out)', fontsize=12,
            fontweight='bold', color='#1565C0')

    # Chain 1
    ax.text(0.2, 10.35, 'Chain 1  Vehicle Design:', fontsize=10.5,
            fontweight='bold', color='#2E7D32')
    box(ax, 1.6, 9.65, 2.1, 0.62, 'D3 PyBaMM\ncalibration', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 4.3, 9.65, 2.1, 0.62, 'batteries/*.csv\nOCV-SOC', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 7.0, 9.65, 2.1, 0.62, 'C1/C2 FASTSim\n(+ Adapter)', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 9.7, 9.65, 2.1, 0.62, 'vehicles/*.yaml', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 10.6, 8.8, 2.1, 0.62, 'A1-A4 esmini\nADAS tests', '#E8F5E9', '#2E7D32', 8.5)
    for p1, p2 in [((3.7, 9.96), (4.3, 9.96)), ((6.4, 9.96), (7.0, 9.96)),
                   ((9.1, 9.96), (9.7, 9.96))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (10.75, 9.65), (11.2, 9.42), '#2E7D32')

    # Chain 2
    ax.text(0.2, 8.6, 'Chain 2  Algorithm Dev:', fontsize=10.5,
            fontweight='bold', color='#2E7D32')
    box(ax, 1.6, 7.85, 2.1, 0.62, 'BaseController\n(common)', '#E3F2FD', '#1565C0', 8.5)
    box(ax, 4.3, 7.85, 2.1, 0.62, 'A / B closed loop\nesmini / TraCI', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 7.0, 7.85, 2.1, 0.62, 'Metrics\nTTC / error / PET', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 9.7, 7.85, 2.1, 0.62, 'Tune & iterate\nresults/*.json', '#E3F2FD', '#1565C0', 8.5)
    for p1, p2 in [((3.7, 8.16), (4.3, 8.16)), ((6.4, 8.16), (7.0, 8.16)),
                   ((9.1, 8.16), (9.7, 8.16))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (10.75, 7.85), (5.4, 7.62), '#90A4AE', lw=1.1, rad=-0.25)
    ax.text(8.0, 7.32, 'feedback: retune controller', fontsize=8.5,
            color='#607D8B', style='italic', ha='center')

    # Chain 3
    ax.text(0.2, 7.0, 'Chain 3  Energy Mgmt:', fontsize=10.5,
            fontweight='bold', color='#2E7D32')
    box(ax, 1.6, 6.2, 2.1, 0.62, 'E2/E4 optimize\npymoo / DP', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 4.3, 6.2, 2.1, 0.62, 'Optimal params\n/ strategy', '#FFF8E1', '#F9A825', 8.5)
    box(ax, 7.0, 6.2, 2.1, 0.62, 'C4 FASTSim\nvalidation', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 9.7, 6.2, 2.1, 0.62, 'Report card\nresults/*.json', '#E3F2FD', '#1565C0', 8.5)
    for p1, p2 in [((3.7, 6.51), (4.3, 6.51)), ((6.4, 6.51), (7.0, 6.51)),
                   ((9.1, 6.51), (9.7, 6.51))]:
        arrow(ax, p1, p2, '#2E7D32')

    # Chain 4 (Stage 2, planned - purple dashed)
    ax.text(0.2, 5.6, 'Chain 4  Perception (Stage 2):', fontsize=10.5,
            fontweight='bold', color='#5E35B1')
    box(ax, 1.6, 4.8, 2.1, 0.62, 'I1 CARLA/AWSIM\n3D world (GPU pod)', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    box(ax, 4.3, 4.8, 2.1, 0.62, 'Sensor data\ncamera/LiDAR/radar', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    box(ax, 7.0, 4.8, 2.1, 0.62, 'Perception\nYOLO / fusion', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    box(ax, 9.7, 4.8, 2.1, 0.62, 'I5 Autoware\nfull-stack AD', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    for p1, p2 in [((3.7, 5.11), (4.3, 5.11)), ((6.4, 5.11), (7.0, 5.11)),
                   ((9.1, 5.11), (9.7, 5.11))]:
        arrow(ax, p1, p2, '#5E35B1')
    ax.text(11.9, 4.5, 'planned', fontsize=8.5, color='#5E35B1',
            style='italic', ha='center')

    # ---------- grading ----------
    ax.text(0.2, 4.15, 'GRADING FLOW', fontsize=12, fontweight='bold',
            color='#AD1457')
    box(ax, 0.6, 3.25, 2.3, 0.7, 'Student runs\nexperiment', '#FCE4EC', '#AD1457', 9)
    box(ax, 3.4, 3.25, 2.3, 0.7, 'save_result()\nresults/*.json', '#FFF8E1', '#F9A825', 9)
    box(ax, 6.2, 3.25, 2.3, 0.7, 'collect_grades.py\nhourly cron (host)', '#FCE4EC', '#AD1457', 9)
    box(ax, 9.0, 3.25, 2.3, 0.7, 'evaluator +\ngradebook', '#FCE4EC', '#AD1457', 9)
    box(ax, 10.6, 2.3, 2.3, 0.7, 'Teacher Dashboard\ntable/stats/charts', '#E0F2F1', '#00695C', 9)
    for p1, p2 in [((2.9, 3.6), (3.4, 3.6)), ((5.7, 3.6), (6.2, 3.6)),
                   ((8.5, 3.6), (9.0, 3.6))]:
        arrow(ax, p1, p2, '#AD1457')
    arrow(ax, (11.0, 3.25), (11.6, 3.0), '#AD1457')
    ax.text(6.5, 2.95, 'Anti-cheat: min-steps criteria + execution timeout watchdog',
            ha='center', fontsize=8.5, color='#AD1457', style='italic')

    # ---------- workflows ----------
    ax.text(0.2, 2.1, 'WORKFLOWS', fontsize=12, fontweight='bold', color='#00695C')
    box(ax, 0.6, 1.3, 11.8, 0.6,
        'Student:  Email-OTP login  >  Pick experiment  >  Read principles (+ schematics)  >  Run & tune (Try-It)  >  Self-check score  >  Lab report',
        '#E0F2F1', '#00695C', 9.5)
    box(ax, 0.6, 0.6, 11.8, 0.6,
        'Teacher:  Roster (add / CSV import)  >  Teach with chains  >  View grades + charts  >  Identify weak experiments  >  Archive (course done)',
        '#FFF3E0', '#E65100', 9.5)
    box(ax, 0.6, 0.05, 11.8, 0.42,
        'Honesty by design: real engines only; stand-ins labeled; planned (dashed) = Stage 2, not yet live',
        'white', '#90A4AE', 9)

    path = os.path.join(OUT, 'fig2_dataflow.png')
    fig.savefig(path, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return path


if __name__ == '__main__':
    for p in [fig_architecture(), fig_dataflow()]:
        print('Generated:', p, os.path.getsize(p), 'bytes')
