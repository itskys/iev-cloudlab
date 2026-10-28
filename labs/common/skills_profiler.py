"""IEV CloudLab 核心工程能力雷达画像与班级短板诊断 | Skills Profiler

功能说明：
  将课程 29 门实验结构化映射至 7 大核心智能网联新能源汽车工程能力维度：
    1. 纵向跟驰与安全控制 (Longitudinal & Safety Control)
    2. 交通流动力学与协同编队 (Traffic Flow & Cooperative Platooning)
    3. 整车能耗与动力总成匹配 (Powertrain & Energy Consumption)
    4. 电池电化学与等效电路建模 (Battery Electrochemistry & ECM)
    5. 智能能量管理与全局优化 (EMS & Optimal Control)
    6. 跨域联合仿真与 FMI/FMU (Cross-Domain Co-Simulation & FMI)
    7. 车载通信与极端场景测试 (Vehicle Network & Edge-Case Testing)

主要接口：
  - compute_student_skill_profile(): 单生 7 大维度能力量化与强弱项诊断
  - render_student_radar_svg(): 生成轻量级高保真原生 SVG/HTML 能力雷达图（零字体依赖，移动端自适应）
  - plot_student_radar_png(): 生成 Matplotlib 静态高分雷达图（PNG 归档）
  - compute_class_skills_matrix(): 全班能力画像矩阵与离散度分析
  - render_class_weakness_html(): 全班能力短板热力看板与精准教学干预提示
"""

import math
import os
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from common.evaluator import GRADING_SPECS
except ImportError:
    try:
        from .evaluator import GRADING_SPECS
    except ImportError:
        GRADING_SPECS = {}

# 7 大工程能力维度定义
SKILL_DIMENSIONS = {
    'longitudinal_safety': {
        'name': '纵向跟驰与安全控制',
        'en_name': 'Longitudinal & Safety Control',
        'color': '#3b82f6',  # 蓝色
        'desc': 'ACC自适应巡航、AEB紧急制动介入、时距控制与运动学动力学闭环避险',
        'experiments': ['A1_cutin_aeb', 'A2_acc_follow', 'A3_aeb_closedloop', 'A4_intersection_yield', 'A5_merge_kinematic_demo', 'E3_mpc_follow'],
    },
    'traffic_dynamics': {
        'name': '交通流动力学与协同编队',
        'en_name': 'Traffic Flow & Platooning',
        'color': '#10b981',  # 绿色
        'desc': '微观跟驰IDM参数标定、交叉口信号控制、拥堵波传播分析与CACC车队控制',
        'experiments': ['B1_idm_calibration', 'B2_traffic_signal', 'B3_sumo_cacc', 'B4_congestion_wave', 'B5_green_wave'],
    },
    'powertrain_energy': {
        'name': '整车能耗与动力总成匹配',
        'en_name': 'Powertrain & Energy Analysis',
        'color': '#f59e0b',  # 琥珀橙
        'desc': '标准工况循环电耗积分、阻力灵敏度分解、车型横向对标与混合动力构型',
        'experiments': ['C1_fastsim_energy', 'C2_vehicle_comparison', 'C3_sensitivity_analysis', 'C4_ems_comparison'],
    },
    'battery_electrochem': {
        'name': '电池电化学与机理建模',
        'en_name': 'Battery Electrochemistry & ECM',
        'color': '#8b5cf6',  # 紫色
        'desc': 'PyBaMM 单粒子模型(SPM)、Peukert倍率容量损耗、OCV-SOC标定与低温快充析锂边界',
        'experiments': ['D1_pybamm_battery', 'D2_rate_capacity', 'D3_ocv_soc_export', 'D4_lithium_plating'],
    },
    'optimal_control': {
        'name': '智能能量管理与全局优化',
        'en_name': 'EMS & Optimal Control',
        'color': '#ec4899',  # 品红
        'desc': 'Pymoo 多目标 Pareto 前沿寻优、动态规划 (DP) 全局最优能量管理策略与实时在线求解',
        'experiments': ['E1_single_objective', 'E2_pymoo_multiobj', 'E4_dp_ems', 'C4_ems_comparison'],
    },
    'cosimulation_fmi': {
        'name': '跨域联合仿真与 FMI/FMU',
        'en_name': 'Cross-Domain Co-Simulation',
        'color': '#06b6d4',  # 青色
        'desc': 'FMI 标准协议接口、OpenModelica 机电液物理建模、多 FMU 主从时间步进协仿真',
        'experiments': ['F1_fmu_load', 'F2_openmodelica_fmu', 'F3_multi_fmu'],
    },
    'network_scenario_eng': {
        'name': '车载通信与极端场景测试',
        'en_name': 'Vehicle Network & Edge-Case Testing',
        'color': '#ef4444',  # 红色
        'desc': 'ROS2 DDS 话题/服务交互、组态场景参数空间批量生成与模糊对抗测试',
        'experiments': ['G1_ros_topics', 'G2_ros_services', 'H1_batch_generation', 'H2_scenario_fuzzing'],
    },
}


def _get_mastery_level(score: float, completion_rate: float) -> Tuple[str, str]:
    """返回能力等级称谓与视觉色彩"""
    if completion_rate == 0.0:
        return '未开展 (Unstarted)', '#9ca3af'
    if score >= 85.0 and completion_rate >= 80.0:
        return '精通 (Mastery)', '#10b981'
    if score >= 70.0 and completion_rate >= 60.0:
        return '良好 (Proficient)', '#3b82f6'
    if score >= 60.0 and completion_rate >= 50.0:
        return '合格 (Competent)', '#f59e0b'
    return '需加强 (Needs Work)', '#ef4444'


def compute_student_skill_profile(user_scores: Dict[str, Union[float, int, Dict]]) -> Dict[str, Any]:
    """计算单个学生在 7 大工程能力维度上的画像得分与掌握度。

    :param user_scores: {experiment_id: score_or_dict}
    :return: 结构化能力画像字典
    """
    clean_scores = {}
    for k, v in user_scores.items():
        if isinstance(v, (int, float)):
            clean_scores[k] = float(v)
        elif isinstance(v, dict) and 'score' in v:
            clean_scores[k] = float(v['score'])

    dimensions_output = {}
    dim_scores_list = []

    for dim_key, dim_info in SKILL_DIMENSIONS.items():
        exps = dim_info['experiments']
        n_total = len(exps)
        achieved_scores = []

        for exp_id in exps:
            if exp_id in clean_scores:
                achieved_scores.append(clean_scores[exp_id])

        n_done = len(achieved_scores)
        completion_pct = round((n_done / n_total) * 100.0, 1) if n_total > 0 else 0.0

        # 公平折算：未完成实验记 0 分
        dim_score = round(sum(achieved_scores) / n_total, 1) if n_total > 0 else 0.0
        level_str, level_color = _get_mastery_level(dim_score, completion_pct)

        dim_profile = {
            'dimension_key': dim_key,
            'name': dim_info['name'],
            'en_name': dim_info['en_name'],
            'color': dim_info['color'],
            'desc': dim_info['desc'],
            'score': dim_score,
            'n_done': n_done,
            'n_total': n_total,
            'completion_pct': completion_pct,
            'mastery_level': level_str,
            'level_color': level_color,
            'exps': {e: clean_scores.get(e, None) for e in exps},
        }
        dimensions_output[dim_key] = dim_profile
        dim_scores_list.append((dim_key, dim_score, dim_info['name']))

    # 排序识别最强项与短板项
    sorted_dims = sorted(dim_scores_list, key=lambda x: x[1], reverse=True)
    strongest = sorted_dims[0] if sorted_dims else (None, 0.0, '')
    weakest = sorted_dims[-1] if sorted_dims else (None, 0.0, '')

    composite_average = round(sum(d['score'] for d in dimensions_output.values()) / len(dimensions_output), 1)

    return {
        'composite_score': composite_average,
        'dimensions': dimensions_output,
        'strongest_skill': {'key': strongest[0], 'score': strongest[1], 'name': strongest[2]},
        'weakest_skill': {'key': weakest[0], 'score': weakest[1], 'name': weakest[2]},
    }


def render_student_radar_svg(
    skill_profile: Dict[str, Any],
    student_name: str = "Student",
    width: int = 500,
    height: int = 400,
) -> str:
    """生成零外部依赖、高保真的原生矢量 SVG 雷达图。"""
    cx = width / 2.0
    cy = height / 2.0 + 10
    radius = min(width, height) * 0.35

    dims = list(SKILL_DIMENSIONS.keys())
    n = len(dims)
    angle_step = 2.0 * math.pi / n

    # 背景网格圈 (20, 40, 60, 80, 100)
    grid_svg = ""
    for level in [20, 40, 60, 80, 100]:
        r = radius * (level / 100.0)
        pts = []
        for i in range(n):
            a = i * angle_step - math.pi / 2.0
            x = cx + r * math.cos(a)
            y = cy + r * math.sin(a)
            pts.append(f"{x:.1f},{y:.1f}")
        grid_svg += f'<polygon points="{" ".join(pts)}" fill="none" stroke="#e2e8f0" stroke-width="1" />\n'
        # 刻度标记
        grid_svg += f'<text x="{cx + 4:.1f}" y="{cy - r + 10:.1f}" font-size="9" fill="#94a3b8" font-family="sans-serif">{level}</text>\n'

    # 辐射轴线与轴标签
    axes_svg = ""
    labels_svg = ""
    student_pts = []

    for i, dim_k in enumerate(dims):
        a = i * angle_step - math.pi / 2.0
        x_edge = cx + radius * math.cos(a)
        y_edge = cy + radius * math.sin(a)
        axes_svg += f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{x_edge:.1f}" y2="{y_edge:.1f}" stroke="#cbd5e1" stroke-width="1" stroke-dasharray="2 2" />\n'

        # 标签位置
        r_label = radius + 32
        x_label = cx + r_label * math.cos(a)
        y_label = cy + r_label * math.sin(a)

        dim_data = skill_profile['dimensions'].get(dim_k, {})
        score = dim_data.get('score', 0.0)
        name = dim_data.get('name', dim_k)

        # 文字对齐
        anchor = "middle"
        if math.cos(a) > 0.3:
            anchor = "start"
        elif math.cos(a) < -0.3:
            anchor = "end"

        labels_svg += f'''
        <text x="{x_label:.1f}" y="{y_label:.1f}" text-anchor="{anchor}" font-size="11" font-weight="600" fill="#334155" font-family="system-ui, sans-serif">
            {name}
            <tspan fill="#2563eb" font-weight="700"> ({score:.0f})</tspan>
        </text>
        '''

        # 学生实际数据点
        r_score = radius * (max(0.0, min(100.0, score)) / 100.0)
        x_pt = cx + r_score * math.cos(a)
        y_pt = cy + r_score * math.sin(a)
        student_pts.append(f"{x_pt:.1f},{y_pt:.1f}")

    polygon_pts = " ".join(student_pts)
    data_polygon = f'''
    <polygon points="{polygon_pts}" fill="rgba(37, 99, 235, 0.25)" stroke="#2563eb" stroke-width="2.5" />
    '''
    dots_svg = ""
    for pt in student_pts:
        x, y = pt.split(',')
        dots_svg += f'<circle cx="{x}" cy="{y}" r="4" fill="#2563eb" stroke="#ffffff" stroke-width="1.5" />\n'

    svg = f'''
    <div style="background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin: 12px 0; box-shadow: 0 2px 6px rgba(0,0,0,0.03); max-width: {width + 40}px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 10px;">
            <div>
                <h4 style="margin: 0; font-size: 15px; color: #0f172a; font-family: system-ui, sans-serif;">
                    📊 {student_name} - 7 大工程能力画像雷达图
                </h4>
                <p style="margin: 2px 0 0 0; font-size: 12px; color: #64748b; font-family: system-ui, sans-serif;">
                    综合能力均分: <strong style="color: #2563eb;">{skill_profile['composite_score']:.1f}</strong> | 最优: {skill_profile['strongest_skill']['name']} | 需强化: {skill_profile['weakest_skill']['name']}
                </p>
            </div>
        </div>
        <div style="display: flex; justify-content: center;">
            <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
                {grid_svg}
                {axes_svg}
                {data_polygon}
                {dots_svg}
                {labels_svg}
            </svg>
        </div>
    </div>
    '''
    return svg


def compute_class_skills_matrix(grade_table: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """基于 gradebook 成绩汇总表，计算全班 7 大能力的均分、及格率与离散度。

    :param grade_table: build_grade_table 的输出字典 {username: row}
    :return: 全班能力画像矩阵字典
    """
    if not grade_table:
        return {'n_students': 0, 'dimensions': {}}

    student_profiles = {}
    dim_all_scores = {k: [] for k in SKILL_DIMENSIONS}

    for user, row in grade_table.items():
        if user in ('admin', 'lost+found'):
            continue
        p = compute_student_skill_profile(row)
        student_profiles[user] = p
        for k, d in p['dimensions'].items():
            dim_all_scores[k].append(d['score'])

    n_students = len(student_profiles)
    dim_summary = {}
    weakness_ranking = []

    for k, scores in dim_all_scores.items():
        if not scores:
            continue
        mean_v = sum(scores) / len(scores)
        pass_pct = (sum(1 for s in scores if s >= 60.0) / len(scores)) * 100.0
        # 样本标准差
        var_v = sum((s - mean_v) ** 2 for s in scores) / (len(scores) - 1) if len(scores) > 1 else 0.0
        std_v = math.sqrt(var_v)

        dim_info = SKILL_DIMENSIONS[k]
        dim_summary[k] = {
            'name': dim_info['name'],
            'en_name': dim_info['en_name'],
            'mean_score': round(mean_v, 1),
            'std_dev': round(std_v, 1),
            'pass_rate': round(pass_pct, 1),
            'color': dim_info['color'],
            'desc': dim_info['desc'],
        }
        weakness_ranking.append((k, mean_v, dim_info['name']))

    # 升序排序：均分越低，越是全班薄弱环节
    weakness_ranking.sort(key=lambda x: x[1])

    return {
        'n_students': n_students,
        'dimensions': dim_summary,
        'weakness_ranking': weakness_ranking,
        'student_profiles': student_profiles,
    }


def render_class_weakness_html(class_matrix: Dict[str, Any]) -> str:
    """生成全班工程能力短板诊断看板 (HTML)。"""
    if class_matrix.get('n_students', 0) == 0:
        return '<p>暂无班级学生成绩数据</p>'

    rows_html = ""
    for item in class_matrix['weakness_ranking']:
        k, mean_score, name = item
        info = class_matrix['dimensions'][k]
        pass_rate = info['pass_rate']
        std_dev = info['std_dev']

        # 预警等级
        if mean_score < 50.0 or pass_rate < 50.0:
            alert_badge = '<span style="background: #fef2f2; color: #dc2626; border: 1px solid #f87171; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">🚨 极度薄弱</span>'
            bar_color = "#ef4444"
        elif mean_score < 70.0:
            alert_badge = '<span style="background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">⚠️ 需专项复导</span>'
            bar_color = "#f59e0b"
        else:
            alert_badge = '<span style="background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">✅ 整体达标</span>'
            bar_color = "#10b981"

        rows_html += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 10px 14px; font-weight: 600; color: #1e293b;">{name}</td>
            <td style="padding: 10px 14px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="flex-grow: 1; background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden; width: 100px;">
                        <div style="background: {bar_color}; width: {min(100.0, max(0.0, mean_score))}%; height: 100%;"></div>
                    </div>
                    <strong style="color: #0f172a; font-size: 13px;">{mean_score:.1f}</strong>
                </div>
            </td>
            <td style="padding: 10px 14px; color: #475569; font-size: 13px;">{pass_rate:.1f}%</td>
            <td style="padding: 10px 14px; color: #64748b; font-size: 12px;">±{std_dev:.1f}</td>
            <td style="padding: 10px 14px; text-align: center;">{alert_badge}</td>
        </tr>
        """

    top_weakness = class_matrix['weakness_ranking'][0] if class_matrix['weakness_ranking'] else (None, 0, '')

    html = f"""
    <div style="background: white; border: 1px solid #cbd5e1; border-radius: 12px; padding: 20px; margin: 14px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 2px solid #f1f5f9; padding-bottom: 12px;">
            <div>
                <h3 style="margin: 0; color: #0f172a; font-size: 17px; font-weight: 700;">
                    🎯 全班 7 大核心工程能力短板诊断看板 ({class_matrix['n_students']} 名学生)
                </h3>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">
                    识别全班共性工程盲区，驱动精准课堂答疑与随堂测验策略
                </p>
            </div>
            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 8px 14px; text-align: right;">
                <span style="font-size: 11px; color: #991b1b; font-weight: 600; text-transform: uppercase;">首要攻坚短板</span><br/>
                <strong style="color: #b91c1c; font-size: 14px;">{top_weakness[2]} ({top_weakness[1]:.1f}分)</strong>
            </div>
        </div>
        <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px;">
            <thead>
                <tr style="background: #f8fafc; color: #475569; border-bottom: 1px solid #e2e8f0;">
                    <th style="padding: 8px 14px;">能力维度 (Engineering Dimension)</th>
                    <th style="padding: 8px 14px;">全班均分 (Class Avg)</th>
                    <th style="padding: 8px 14px;">及格率 (Pass Rate)</th>
                    <th style="padding: 8px 14px;">离散标准差 (Std)</th>
                    <th style="padding: 8px 14px; text-align: center;">预警级别</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
    """
    return html
