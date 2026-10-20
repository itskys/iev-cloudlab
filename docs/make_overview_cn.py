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


def box(ax, x, y, w, h, text, fc, ec='#37474F', fs=9, bold=False, ls='-'):
    b = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.03',
                       fc=fc, ec=ec, lw=1.2, linestyle=ls)
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

    layer_label(ax, 0.15, 7.35, '平台层', '#1565C0')
    box(ax, 0.6, 6.35, 3.8, 0.95, 'JupyterHub 5.5.3（VPS）\n邮箱验证码登录\n每人独立容器', '#E3F2FD', '#1565C0', 9)
    box(ax, 4.6, 6.35, 3.8, 0.95, '学生容器（CPU）\niev-base 镜像\nPython 3.12 + 快速仿真内核', '#E3F2FD', '#1565C0', 9)
    box(ax, 8.6, 6.35, 3.8, 0.95, 'GPU 算力舱（RunPod 4090）\n按需调用 ievlab.submit()\n二期规划', '#EDE7F6', '#5E35B1', 9, ls='--')
    arrow(ax, (10.6, 8.0), (10.6, 7.32), '#1565C0')
    arrow(ax, (4.4, 6.82), (4.6, 6.82), '#1565C0')
    arrow(ax, (8.4, 6.82), (8.6, 6.82), '#5E35B1')

    layer_label(ax, 0.15, 5.9, '实验层（29已上线+5 GPU规划）', '#2E7D32')
    mods = [('A×5\n自动驾驶\n（场景仿真）', '#E8F5E9', '#2E7D32', '-'),
            ('B×5\n交通流\n（交通仿真）', '#E8F5E9', '#2E7D32', '-'),
            ('C×4\n整车能量\n（快速仿真）', '#E8F5E9', '#2E7D32', '-'),
            ('D×4\n电池\n（电化学）', '#E8F5E9', '#2E7D32', '-'),
            ('E×4\n优化控制\n（多目标）', '#E8F5E9', '#2E7D32', '-'),
            ('F×3\n模型交换\n（FMI）', '#E8F5E9', '#2E7D32', '-'),
            ('G×2\n中间件\n（ROS 2）', '#E8F5E9', '#2E7D32', '-'),
            ('H×2\n场景工程\n（生成/模糊）', '#E8F5E9', '#2E7D32', '-'),
            ('I×5\n感知与驾驶\n（CARLA·GPU）', '#EDE7F6', '#5E35B1', '--')]
    x = 0.6
    for name, fc, ec, ls in mods:
        box(ax, x, 4.75, 1.24, 1.0, name, fc, ec, 8, ls=ls)
        x += 1.317
    ax.text(6.5, 4.5, '每个实验：实验原理 | 实验目的 | 学生任务 | 验证内容 | 结果分析 | 报错说明（中英双语）',
            ha='center', fontsize=9.5, style='italic', color='#2E7D32')

    layer_label(ax, 0.15, 4.05, '支撑层（labs/）', '#E65100')
    box(ax, 0.6, 3.0, 3.8, 0.95, '共享库 common/\n控制器 | 环境 | 电池适配器\n车辆库 | 原理图库（8张）', '#FFF3E0', '#E65100', 8.5)
    box(ax, 4.6, 3.0, 3.8, 0.95, '场景库 scenarios/\n标准场景定义\n（.xosc / .xodr / .yaml）', '#FFF3E0', '#E65100', 9)
    box(ax, 8.6, 3.0, 3.8, 0.95, '数据库 data/\n车型 | 电池 | 结果\n（共享、可串链）', '#FFF3E0', '#E65100', 9)

    layer_label(ax, 0.15, 2.6, '仿真引擎层', '#AD1457')
    box(ax, 0.6, 1.6, 11.8, 0.9,
        'esmini 场景仿真  |  SUMO 交通仿真  |  FASTSim 整车  |  PyBaMM 电池  |  CasADi 优化  |  pymoo 多目标  |  FMPy  |  ROS 2 Jazzy\n+ 二期（GPU）：CARLA 三维仿真  |  AWSIM  |  Autoware 自动驾驶栈  |  YOLO 目标检测',
        '#FCE4EC', '#AD1457', 9.5, bold=True)

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
    fig, ax = plt.subplots(figsize=(13, 11.5))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 11.5)
    ax.axis('off')
    ax.text(6.5, 11.25, 'IEV CloudLab — 数据流与工作流图',
            ha='center', fontsize=16, fontweight='bold')

    ax.text(0.2, 10.8, '四条链（任一入口进，全链路出）', fontsize=12.5,
            fontweight='bold', color='#1565C0')

    ax.text(0.2, 10.35, '链1 车型设计链：', fontsize=11, fontweight='bold', color='#2E7D32')
    box(ax, 1.9, 9.65, 2.1, 0.62, 'D3 电池标定\n（PyBaMM）', '#E8F5E9', '#2E7D32', 9)
    box(ax, 4.6, 9.65, 2.1, 0.62, '电池库 CSV\nOCV-SOC曲线', '#FFF8E1', '#F9A825', 9)
    box(ax, 7.3, 9.65, 2.1, 0.62, 'C1/C2 整车能耗\n（FASTSim+适配器）', '#E8F5E9', '#2E7D32', 8.5)
    box(ax, 10.0, 9.65, 2.1, 0.62, '车型库 YAML\n整车参数', '#FFF8E1', '#F9A825', 9)
    box(ax, 10.6, 8.8, 2.1, 0.62, 'A1-A4 智驾测试\n（esmini）', '#E8F5E9', '#2E7D32', 9)
    for p1, p2 in [((4.0, 9.96), (4.6, 9.96)), ((6.7, 9.96), (7.3, 9.96)),
                   ((9.4, 9.96), (10.0, 9.96))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (11.05, 9.65), (11.5, 9.42), '#2E7D32')

    ax.text(0.2, 8.6, '链2 算法开发链：', fontsize=11, fontweight='bold', color='#2E7D32')
    box(ax, 1.9, 7.85, 2.1, 0.62, '控制器基类\n（共享库）', '#E3F2FD', '#1565C0', 9)
    box(ax, 4.6, 7.85, 2.1, 0.62, 'A/B 闭环仿真\n场景/交通引擎', '#E8F5E9', '#2E7D32', 9)
    box(ax, 7.3, 7.85, 2.1, 0.62, '指标计算\nTTC/误差/PET', '#FFF8E1', '#F9A825', 9)
    box(ax, 10.0, 7.85, 2.1, 0.62, '调参迭代\n结果 JSON', '#E3F2FD', '#1565C0', 9)
    for p1, p2 in [((4.0, 8.16), (4.6, 8.16)), ((6.7, 8.16), (7.3, 8.16)),
                   ((9.4, 8.16), (10.0, 8.16))]:
        arrow(ax, p1, p2, '#2E7D32')
    arrow(ax, (10.75, 7.85), (5.7, 7.62), '#90A4AE', lw=1.1, rad=-0.25)
    ax.text(8.2, 7.3, '反馈：根据指标重新调参', fontsize=9, color='#607D8B',
            style='italic', ha='center')

    ax.text(0.2, 7.0, '链3 能量管理链：', fontsize=11, fontweight='bold', color='#2E7D32')
    box(ax, 1.9, 6.2, 2.1, 0.62, 'E2/E4 优化\n多目标/动态规划', '#E8F5E9', '#2E7D32', 9)
    box(ax, 4.6, 6.2, 2.1, 0.62, '最优参数\n/ 策略', '#FFF8E1', '#F9A825', 9)
    box(ax, 7.3, 6.2, 2.1, 0.62, 'C4 整车验证\n（FASTSim）', '#E8F5E9', '#2E7D32', 9)
    box(ax, 10.0, 6.2, 2.1, 0.62, '成绩单\n结果 JSON', '#E3F2FD', '#1565C0', 9)
    for p1, p2 in [((4.0, 6.51), (4.6, 6.51)), ((6.7, 6.51), (7.3, 6.51)),
                   ((9.4, 6.51), (10.0, 6.51))]:
        arrow(ax, p1, p2, '#2E7D32')

    ax.text(0.2, 5.6, '链4 感知链（二期）：', fontsize=11, fontweight='bold', color='#5E35B1')
    box(ax, 1.9, 4.8, 2.1, 0.62, 'I1 三维场景\nCARLA/AWSIM（GPU舱）', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    box(ax, 4.6, 4.8, 2.1, 0.62, '传感器数据\n相机/激光雷达/雷达', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    box(ax, 7.3, 4.8, 2.1, 0.62, '感知算法\nYOLO检测/融合', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    box(ax, 10.0, 4.8, 2.1, 0.62, 'I5 完整驾驶栈\nAutoware', '#EDE7F6', '#5E35B1', 8.5, ls='--')
    for p1, p2 in [((4.0, 5.11), (4.6, 5.11)), ((6.7, 5.11), (7.3, 5.11)),
                   ((9.4, 5.11), (10.0, 5.11))]:
        arrow(ax, p1, p2, '#5E35B1')
    ax.text(11.05, 4.5, '规划中', fontsize=9, color='#5E35B1',
            style='italic', ha='center')

    ax.text(0.2, 4.15, '成绩数据流', fontsize=12.5, fontweight='bold', color='#AD1457')
    box(ax, 0.6, 3.25, 2.3, 0.7, '学生运行实验', '#FCE4EC', '#AD1457', 9.5)
    box(ax, 3.4, 3.25, 2.3, 0.7, '保存结果\nresults/*.json', '#FFF8E1', '#F9A825', 9.5)
    box(ax, 6.2, 3.25, 2.3, 0.7, '成绩汇总脚本\n每小时（主机定时）', '#FCE4EC', '#AD1457', 9)
    box(ax, 9.0, 3.25, 2.3, 0.7, '评分引擎 +\n成绩册', '#FCE4EC', '#AD1457', 9.5)
    box(ax, 10.6, 2.3, 2.3, 0.7, '教师面板\n表格/统计/图表', '#E0F2F1', '#00695C', 9.5)
    for p1, p2 in [((2.9, 3.6), (3.4, 3.6)), ((5.7, 3.6), (6.2, 3.6)),
                   ((8.5, 3.6), (9.0, 3.6))]:
        arrow(ax, p1, p2, '#AD1457')
    arrow(ax, (11.0, 3.25), (11.6, 3.0), '#AD1457')
    ax.text(6.5, 2.95, '防作弊：最小步数判据 + 执行超时看门狗',
            ha='center', fontsize=9, color='#AD1457', style='italic')

    ax.text(0.2, 2.1, '双角色工作流', fontsize=12.5, fontweight='bold', color='#00695C')
    box(ax, 0.6, 1.3, 11.8, 0.6,
        '学生：邮箱验证码登录 ＞ 选实验 ＞ 读原理（+原理图）＞ 运行调参（试一试）＞ 自查评分 ＞ 写实验报告',
        '#E0F2F1', '#00695C', 10)
    box(ax, 0.6, 0.6, 11.8, 0.6,
        '教师：建名册（添加/批量导入）＞ 按链授课 ＞ 查看成绩与图表 ＞ 定位薄弱实验 ＞ 结课归档',
        '#FFF3E0', '#E65100', 10)
    box(ax, 0.6, 0.05, 11.8, 0.42,
        '诚实原则：只用真实引擎；替身演示强制标注；虚线框 = 二期规划，尚未上线',
        'white', '#90A4AE', 9.5)

    path = os.path.join(OUT, 'fig2_dataflow_cn.png')
    fig.savefig(path, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return path


if __name__ == '__main__':
    for p in [fig_architecture_cn(), fig_dataflow_cn()]:
        print('Generated:', p, os.path.getsize(p), 'bytes')
