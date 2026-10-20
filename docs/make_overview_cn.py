"""IEV CloudLab 系统总览图（中文版）| Chinese version of overview figures."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import os

plt.rcParams['font.family'] = ['Noto Sans CJK SC', 'Noto Sans CJK JP',
                               'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT = os.path.dirname(os.path.abspath(__file__))


def box(ax, x, y, w, h, text, fc, ec='#37474F', fs=9, bold=False):
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.03',
                       fc=fc, ec=ec, lw=1.2)
    ax.add_patch(b)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, fontweight='bold' if bold else 'normal')
    return b


def arrow(ax, p1, p2, color='#37474F', lw=1.4, rad=0.0):
    a = FancyArrowPatch(p1, p2, arrowstyle='->', mutation_scale=13,
                        color=color, lw=lw,
                        connectionstyle=f'arc3,rad={rad}')
    ax.add_patch(a)
    return a


def layer_label(ax, x, y, text, color):
    ax.text(x, y, text, ha='left', va='center', fontsize=11,
            fontweight='bold', color=color,
            bbox=dict(boxstyle='round,pad=0.3', fc='white', ec=color, lw=1.2))


def fig_architecture_cn():
    fig, ax = plt.subplots(figsize=(13, 9.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 9.5)
    ax.axis('off')
    ax.text(6.5, 9.25, 'IEV CloudLab 智能电动汽车云仿真实验平台 — 系统架构图',
            ha='center', fontsize=15, fontweight='bold')

    layer_label(ax, 0.15, 8.55, '接入层', '#6A1B9A')
    box(ax, 0.6, 8.0, 3.6, 0.95, '学生 / 教师\n（浏览器，零安装）', '#F3E5F5', '#6A1B9A', 10)
    box(ax, 4.7, 8.0, 3.6, 0.95, 'Cloudflare\n隧道 + DNS + CDN', '#F3E5F5', '#6A1B9A', 10)
    box(ax, 8.8, 8.0, 3.6, 0.95, 'ievlab.aisai.cc\n（HTTPS）', '#F3E5F5', '#6A1B9A', 10, bold=True)
    arrow(ax, (4.2, 8.47), (4.7, 8.47), '#6A1B9A')
    arrow(ax, (8.3, 8.47), (8.8, 8.47), '#6A1B9A')

    layer_label(ax, 0.15, 7.35, '平台层（VPS）', '#1565C0')
    box(ax, 0.6, 6.35, 5.6, 0.95, 'JupyterHub 5.5.3\n邮箱验证码登录 | 每人独立容器', '#E3F2FD', '#1565C0', 10)
    box(ax, 6.8, 6.35, 5.6, 0.95, '学生容器（iev-base 镜像）\nUbuntu 24.04 | Python 3.12 + 快速仿真内核', '#E3F2FD', '#1565C0', 10)
    arrow(ax, (10.6, 8.0), (10.6, 7.32), '#1565C0')
    arrow(ax, (6.2, 6.82), (6.8, 6.82), '#1565C0')

    layer_label(ax, 0.15, 5.9, '实验层（29个）', '#2E7D32')
    mods = ['A×5\n自动驾驶\n（场景仿真）', 'B×5\n交通流\n（交通仿真）',
            'C×4\n整车能量\n（快速仿真）', 'D×4\n电池\n（电化学）',
            'E×4\n优化控制\n（多目标/MPC）', 'F×3\n模型交换\n（FMI）',
            'G×2\n中间件\n（ROS 2）', 'H×2\n场景工程\n（生成/模糊）']
    x = 0.6
    for name in mods:
        box(ax, x, 4.75, 1.42, 1.0, name, '#E8F5E9', '#2E7D32', 8.5)
        x += 1.52
    ax.text(6.5, 4.5, '每个实验：实验原理 | 实验目的 | 学生任务 | 验证内容 | 结果分析 | 报错说明（中英双语）',
            ha='center', fontsize=9.5, style='italic', color='#2E7D32')

    layer_label(ax, 0.15, 4.05, '支撑层（labs/）', '#E65100')
    box(ax, 0.6, 3.0, 3.8, 0.95, '共享库 common/\n控制器 | 环境 | 电池适配器\n车辆库 | 原理图库（8张）', '#FFF3E0', '#E65100', 8.5)
    box(ax, 4.6, 3.0, 3.8, 0.95, '场景库 scenarios/\n标准场景定义\n（.xosc / .xodr / .yaml）', '#FFF3E0', '#E65100', 9)
    box(ax, 8.6, 3.0, 3.8, 0.95, '数据库 data/\n车型 | 电池 | 结果\n（共享、可串链）', '#FFF3E0', '#E65100', 9)

    layer_label(ax, 0.15, 2.6, '仿真引擎层', '#AD1457')
    box(ax, 0.6, 1.6, 11.8, 0.9,
        'esmini 场景仿真  |  SUMO 交通仿真  |  FASTSim 整车  |  PyBaMM 电池\nCasADi 优化求解  |  pymoo 多目标  |  FMPy 模型运行  |  ROS 2 Jazzy',
        '#FCE4EC', '#AD1457', 10, bold=True)

    layer_label(ax, 0.15, 1.2, '教学管理层', '#00695C')
    box(ax, 0.6, 0.25, 3.8, 0.85, '自动评分 evaluator\n29套判据\n（阈值=实测值）', '#E0F2F1', '#00695C', 9)
    box(ax, 4.6, 0.25, 3.8, 0.85, '教师面板\n成绩 | 统计 | 图表\n名册管理 + 归档', '#E0F2F1', '#00695C', 9)
    box(ax, 8.6, 0.25, 3.8, 0.85, '成绩汇总（定时任务）\n每小时自动汇总\n代码仓：GitHub iev-cloudlab', '#E0F2F1', '#00695C', 9)

    for y1, y2 in [(8.0, 7.3), (6.35, 5.75), (4.75, 3.95), (3.0, 2.5), (1.6, 1.1)]:
        arrow(ax, (0.38, y1), (0.38, y2), '#90A4AE', lw=1.6)

    path = os.path.join(OUT, 'fig1_architecture_cn.png')
    fig.savefig(path, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return path


def fig_dataflow_cn():
    fig, ax = plt.subplots(figsize=(13, 10))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.text(6.5, 9.75, 'IEV CloudLab — 数据流与工作流图',
            ha='center', fontsize=16, fontweight='bold')

    ax.text(0.2, 9.3, '三条链（任一入口进，全链路出）', fontsize=12.5,
            fontweight='bold', color='#1565C0')

    ax.text(0.2, 8.85, '链1 车型设计链：', fontsize=11, fontweight='bold', color='#2E7D32')
    box(ax, 1.9, 8.15, 2.1, 0.62, 'D3 电池标定\n（PyBaMM）', '#E8F5E9', '#2E7D32', 9)
    box(ax, 4.6, 8.15, 2.1, 0.62, '电池库 CSV\nOCV-SOC曲线', '#FFF8E1', '#F9A825', 9)
    box(ax, 7.3, 8.15, 2.1, 0.62, 'C1/C2 整车能耗\n（FASTSim+适配器）', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 10.0, 8.15, 2.1, 0.62, '车型库 YAML\n整车参数', '#FFF8E1', '#F9A825', 9)
    box(ax, 10.6, 7.3, 2.1, 0.62, 'A1-A4 智驾测试\n（esmini）', '#E8F5E9', '#2E7D32', 9)
    for p1, p2 in [((4.0, 8.46), (4.6, 8.46)), ((6.7, 8.46), (7.3, 8.46)),
                   ((9.4, 8.46), (10.0, 8.46))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (11.05, 8.15), (11.5, 7.92), '#2E7D32')

    ax.text(0.2, 7.55, '链2 算法开发链：', fontsize=11, fontweight='bold', color='#2E7D32')
    box(ax, 1.9, 6.55, 2.1, 0.62, '控制器基类\n（共享库）', '#E3F2FD', '#1565C0', 9)
    box(ax, 4.6, 6.55, 2.1, 0.62, 'A/B 闭环仿真\n场景/交通引擎', '#E8F5E9', '#2E7D32', 9)
    box(ax, 7.3, 6.55, 2.1, 0.62, '指标计算\nTTC/误差/PET', '#FFF8E1', '#F9A825', 9)
    box(ax, 10.0, 6.55, 2.1, 0.62, '调参迭代\n结果 JSON', '#E3F2FD', '#1565C0', 9)
    for p1, p2 in [((4.0, 6.86), (4.6, 6.86)), ((6.7, 6.86), (7.3, 6.86)),
                   ((9.4, 6.86), (10.0, 6.86))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (10.75, 6.55), (5.7, 6.35), '#90A4AE', lw=1.1, rad=-0.25)
    ax.text(8.2, 6.06, '反馈：根据指标重新调参', fontsize=9, color='#607D8B',
            style='italic', ha='center')

    ax.text(0.2, 5.85, '链3 能量管理链：', fontsize=11, fontweight='bold', color='#2E7D32')
    box(ax, 1.9, 5.05, 2.1, 0.62, 'E2/E4 优化\n多目标/动态规划', '#E8F5E9', '#2E7D32', 9)
    box(ax, 4.6, 5.05, 2.1, 0.62, '最优参数\n/ 策略', '#FFF8E1', '#F9A825', 9)
    box(ax, 7.3, 5.05, 2.1, 0.62, 'C4 整车验证\n（FASTSim）', '#E8F5E9', '#2E7D32', 9)
    box(ax, 10.0, 5.05, 2.1, 0.62, '成绩单\n结果 JSON', '#E3F2FD', '#1565C0', 9)
    for p1, p2 in [((4.0, 5.36), (4.6, 5.36)), ((6.7, 5.36), (7.3, 5.36)),
                   ((9.4, 5.36), (10.0, 5.36))]:
        arrow(ax, p1, p2, '#2E7D32')

    ax.text(0.2, 4.45, '成绩数据流', fontsize=12.5, fontweight='bold', color='#AD1457')
    box(ax, 0.6, 3.55, 2.3, 0.7, '学生运行实验', '#FCE4EC', '#AD1457', 9.5)
    box(ax, 3.4, 3.55, 2.3, 0.7, '保存结果\nresults/*.json', '#FFF8E1', '#F9A825', 9.5)
    box(ax, 6.2, 3.55, 2.3, 0.7, '成绩汇总脚本\n每小时（主机定时）', '#FCE4EC', '#AD1457', 9)
    box(ax, 9.0, 3.55, 2.3, 0.7, '评分引擎 +\n成绩册', '#FCE4EC', '#AD1457', 9.5)
    box(ax, 10.6, 2.6, 2.3, 0.7, '教师面板\n表格/统计/图表', '#E0F2F1', '#00695C', 9.5)
    for p1, p2 in [((2.9, 3.9), (3.4, 3.9)), ((5.7, 3.9), (6.2, 3.9)),
                   ((8.5, 3.9), (9.0, 3.9))]:
        arrow(ax, p1, p2, '#AD1457')
    arrow(ax, (11.0, 3.55), (11.6, 3.3), '#AD1457')
    ax.text(6.5, 3.26, '防作弊：最小步数判据 + 执行超时看门狗',
            ha='center', fontsize=9, color='#AD1457', style='italic')

    ax.text(0.2, 2.35, '双角色工作流', fontsize=12.5, fontweight='bold', color='#00695C')
    box(ax, 0.6, 1.45, 11.8, 0.62,
        '学生：邮箱验证码登录 ＞ 选实验 ＞ 读原理（+原理图）＞ 运行调参（试一试）＞ 自查评分 ＞ 写实验报告',
        '#E0F2F1', '#00695C', 10)
    box(ax, 0.6, 0.65, 11.8, 0.62,
        '教师：建名册（添加/批量导入）＞ 按三链授课 ＞ 查看成绩与图表 ＞ 定位薄弱实验 ＞ 结课归档',
        '#FFF3E0', '#E65100', 10)
    box(ax, 0.6, 0.08, 11.8, 0.45,
        '诚实原则：只用真实引擎；替身演示强制标注；A系列目标车冻结等限制在每个受影响实验中如实声明',
        'white', '#90A4AE', 9.5)

    path = os.path.join(OUT, 'fig2_dataflow_cn.png')
    fig.savefig(path, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return path


if __name__ == '__main__':
    for p in [fig_architecture_cn(), fig_dataflow_cn()]:
        print('Generated:', p, os.path.getsize(p), 'bytes')
