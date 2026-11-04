"""IEV CloudLab 教师演示大屏与学情全景洞察看板 | Instructor Live Presentation Dashboard

功能说明：
  专为智能网联新能源汽车专业教师打造的课堂多媒体授课与学情全景诊断工作台。
  深度解决教师在教学演示中“班级学情缺乏全局把控、共性卡点难以量化、典型错误对比不直观”的痛点。

核心模块：
  1. 课堂演示全景 KPI 与三链通关大屏 (render_teacher_live_dashboard_html)；
  2. 全班高频失效模式排行榜与课堂机理讲评卡 (compute_class_failure_analytics)；
  3. 优秀满分方案 vs 典型受阻方案同屏对标视窗 (render_side_by_side_comparison_html)；
  4. 一键导出课堂讲评教案与学期分析简报 (export_teacher_debrief_markdown)；
  5. Jupyter 原生交互式一键调用 (show_teacher_presentation)。
"""

import json
import os
import math
from typing import Dict, Any, List, Optional, Tuple

try:
    from common.evaluator import GRADING_SPECS, grade_metrics
    from common.gradebook import build_grade_table, statistics
    from common.skills_profiler import compute_class_skills_matrix, SKILL_DIMENSIONS
    from common.copilot import diagnose_experiment, DIAGNOSTIC_KNOWLEDGE_BASE
except ImportError:
    try:
        from .evaluator import GRADING_SPECS, grade_metrics
        from .gradebook import build_grade_table, statistics
        from .skills_profiler import compute_class_skills_matrix, SKILL_DIMENSIONS
        from .copilot import diagnose_experiment, DIAGNOSTIC_KNOWLEDGE_BASE
    except ImportError:
        GRADING_SPECS = {}
        SKILL_DIMENSIONS = {}
        DIAGNOSTIC_KNOWLEDGE_BASE = {}


# ==================== 典型实验对比样本库 (Side-by-Side Reference Cases) ====================
SIDE_BY_SIDE_CASES = {
    'A1_cutin_aeb': {
        'name': 'Cut-in 加塞紧急避险',
        'domain': '智能驾驶极限感知与规控',
        'focus_metric': '碰撞状态与最小安全时距 (TTC)',
        'failed': {
            'title': '典型受阻标定方案 (碰撞追尾)',
            'params': {'ttc_threshold': '1.2 s (触发偏晚)', 'decel_req': '-3.0 m/s² (减速不足)', 'brake_delay': '0.35 s'},
            'metrics': {'collision': 'True (发生碰撞 ❌)', 'min_ttc': '0.38 s', 'speed_impact': '18.5 km/h'},
            'behavior_curve': '加塞车横移入道时距急缩至 12m，系统于 TTC<1.2s 才启动减速，制动滑行距离 > 相对间距，在第 3.2s 追尾。',
            'root_cause': '忽视了执行器建压时延与相对速度差平方做功效应，制动触发窗口留白不足。',
            'bg_color': '#fef2f2', 'border_color': '#ef4444', 'badge_color': '#dc2626'
        },
        'golden': {
            'title': '优秀量产级标定方案 (零碰撞从容避险)',
            'params': {'ttc_threshold': '2.4 s (提前感知)', 'decel_req': '-6.0 m/s² (梯次重制动)', 'brake_delay': '0.12 s (预充压)'},
            'metrics': {'collision': 'False (零碰撞 ✔)', 'min_ttc': '2.15 s', 'stop_clearance': '2.4 m'},
            'behavior_curve': '目标车侵入 30% 立即触发预制动点刹 (-2.5m/s²)，危险收缩时切入 -6.0m/s² 全制动，以 2.4m 安全余量平顺停稳。',
            'root_cause': '符合 Euro NCAP 2023 CCRs 分级梯次制动规范，前置建压消除液压滞后。',
            'bg_color': '#f0fdf4', 'border_color': '#22c55e', 'badge_color': '#16a34a'
        }
    },
    'B3_sumo_cacc': {
        'name': 'CACC 车队协同编队控制',
        'domain': '车联网车路协同与交通流',
        'focus_metric': '编队间距误差与传递函数弦稳定性',
        'failed': {
            'title': '典型受阻标定方案 (车队弦不稳定振荡发散)',
            'params': {'ka_feedforward': '1.15 (前馈过敏)', 'kv_damping': '0.40 (阻尼偏弱)', 'time_delay': '120 ms'},
            'metrics': {'max_spacing_error': '3.82 m (超标发散 ❌)', 'string_stability': '振荡放大 ‖H(jω)‖_∞ = 1.34', 'tail_car_jerk': '4.2 m/s³'},
            'behavior_curve': '领航车轻微减速扰动向下游传播时未被衰减，在第 4~5 辆尾车引发急刹幽灵堵车。',
            'root_cause': '前馈增益超调且未补偿通信延迟，闭环幅值上界击穿 1.0 产生谐振。',
            'bg_color': '#fef2f2', 'border_color': '#ef4444', 'badge_color': '#dc2626'
        },
        'golden': {
            'title': '优秀量产级标定方案 (单调衰减平稳跟随)',
            'params': {'ka_feedforward': '0.65 (稳态前馈)', 'kv_damping': '1.05 (临界阻尼)', 'delay_comp': 'Smith 预估补偿'},
            'metrics': {'max_spacing_error': '0.78 m (高精跟踪 ✔)', 'string_stability': '单调衰减 ‖H(jω)‖_∞ = 0.88', 'tail_car_jerk': '1.1 m/s³'},
            'behavior_curve': '扰动传至第 2 辆车即被吸收 60%，尾车速度与间距曲线保持高平滑度巡航。',
            'root_cause': '严格满足频域弦稳定性李雅普诺夫判据，通信时延被有效内模补偿。',
            'bg_color': '#f0fdf4', 'border_color': '#22c55e', 'badge_color': '#16a34a'
        }
    },
    'C1_fastsim_energy': {
        'name': 'UDDS 循环百公里电耗动力流',
        'domain': '动力总成与整车能耗匹配',
        'focus_metric': '百公里电耗与能量损耗瀑布分布',
        'failed': {
            'title': '典型高能耗方案 (电耗严重超标)',
            'params': {'cd': '0.36 (迎风风阻过大)', 'mass': '2200 kg (重负荷)', 'regen_active': 'False (未开回充)'},
            'metrics': {'energy_kwh_100km': '24.8 kWh/100km (超标 ❌)', 'regen_ratio': '0.0% (机械摩擦全损耗)', 'aero_loss': '8.6 kWh'},
            'behavior_curve': '频繁启停做功全部依赖电驱正向放电，减速动能全部被制动盘转化为无效摩擦热。',
            'root_cause': '气动外形粗糙叠加未利用电机四象限逆变回充特性，严重违反能耗平衡方程。',
            'bg_color': '#fef2f2', 'border_color': '#ef4444', 'badge_color': '#dc2626'
        },
        'golden': {
            'title': '优秀节能低碳方案 (极度轻量与高能量回收)',
            'params': {'cd': '0.22 (超低风阻轿跑)', 'mass': '1600 kg (轻量化铝身)', 'regen_active': 'True (82% 回收效率)'},
            'metrics': {'energy_kwh_100km': '11.8 kWh/100km (优秀达标 ✔)', 'regen_ratio': '36.5% (深度动能回收)', 'aero_loss': '3.2 kWh'},
            'behavior_curve': '减速阶段绿色负功率回充柱峰值达 45kW，百公里综合能耗较基准大幅缩减 52%。',
            'root_cause': '流线型低风阻与制动能量解耦闭环协同，满足工业量产 WLTC 最优电耗区。',
            'bg_color': '#f0fdf4', 'border_color': '#22c55e', 'badge_color': '#16a34a'
        }
    },
    'D4_lithium_plating': {
        'name': '电芯微观剖面电位与析锂机理',
        'domain': '动力电池电化学与安全边界',
        'focus_metric': '负极界面局部电位与金属锂析出状态',
        'failed': {
            'title': '典型危险析锂工况 (枝晶刺穿隔膜热失控)',
            'params': {'charge_rate': '3.0 C (激进过充)', 'temperature': '-10 °C (低温未预热)', 'preheat_active': 'False'},
            'metrics': {'min_potential': '-0.58 V (严重跌穿 0V ❌)', 'plating_time': '248 s (持续沉积)', 'dendrite_length': '28 μm (刺破隔膜)'},
            'behavior_curve': '低温固相离子扩散阻抗剧增，石墨嵌锂速率赶不上电荷堆积，金属锂单质在表面快速析出并长成针状结晶。',
            'root_cause': '违背 Arrhenius 活化能扩散定律与宁德时代低温充电规范，存在灾难性内短路隐患。',
            'bg_color': '#fef2f2', 'border_color': '#ef4444', 'badge_color': '#dc2626'
        },
        'golden': {
            'title': '优秀温控快充方案 (全生命周期安全嵌锂)',
            'params': {'charge_rate': '2.0 C (梯次降流)', 'temperature': '25 °C (热管理预热)', 'preheat_active': 'True (先热后充)'},
            'metrics': {'min_potential': '+0.065 V (全程安全区 ✔)', 'plating_time': '0.0 s (零析锂)', 'lattice_state': '均匀 LiC6 嵌入'},
            'behavior_curve': '负极局部过电位平稳维持于 0V 红线上方，离子通畅扩散嵌入石墨晶格层间。',
            'root_cause': 'BMS 电化学热管理模型确保电芯在最适温区充电，彻底消除枝晶生成原动力。',
            'bg_color': '#f0fdf4', 'border_color': '#22c55e', 'badge_color': '#16a34a'
        }
    },
    'E3_mpc_follow': {
        'name': 'CasADi MPC 非线性跟车实时优化',
        'domain': '运筹优化与最优控制',
        'focus_metric': '单步平均求解时间与车载实时性看门狗',
        'failed': {
            'title': '典型求解发散方案 (控制周期溢出脱节)',
            'params': {'horizon_N': '35 步 (时域过长)', 'constraints_type': '硬约束防撞几何', 'warm_start': 'False'},
            'metrics': {'avg_solve_ms': '82.5 ms (超时严重 ❌)', 'max_solve_ms': '210 ms', 'realtime_violation': '周期溢出率 45%'},
            'behavior_curve': 'IPOPT 内点法在硬边界处 Hessian 矩阵条件数发散，迭代步数暴增，导致车载 ECU 控制中断。',
            'root_cause': '未进行实时性时域截断与约束软化松弛，违反车载嵌入式 ASIL-D 调度要求。',
            'bg_color': '#fef2f2', 'border_color': '#ef4444', 'badge_color': '#dc2626'
        },
        'golden': {
            'title': '优秀量产级 MPC 方案 (毫秒级超快确定性收敛)',
            'params': {'horizon_N': '12 步 (精准截断)', 'constraints_type': '罚函数软约束松弛', 'warm_start': 'True (上一帧热启动)'},
            'metrics': {'avg_solve_ms': '11.4 ms (极致硬实时 ✔)', 'max_solve_ms': '18.2 ms', 'realtime_violation': '0% 完美达标'},
            'behavior_curve': '单步求解稳定于 12ms 黄金窗口内，精准跟踪前车车速并保证车乘员加速度平顺。',
            'root_cause': '合理权衡预测时域与计算复杂度，软约束松弛保证了数值求解凸性与收敛性。',
            'bg_color': '#f0fdf4', 'border_color': '#22c55e', 'badge_color': '#16a34a'
        }
    }
}


def _get_demo_class_results() -> Dict[str, Any]:
    """生成具有真实教学代表性的班级全量模拟学情数据（32 位学生典型分布）"""
    import random
    rng = random.Random(42)  # 固定种子保证结果确定性

    students = [f"stu_2026_{i:03d}" for i in range(1, 33)]
    mock_data = {}

    for s_idx, stu in enumerate(students):
        stu_res = {}
        # 学生水平梯度分布：优秀 (前25%)、良好 (中50%)、后进待辅导 (后25%)
        is_top = s_idx < 8
        is_struggling = s_idx >= 24

        for exp_id in GRADING_SPECS:
            # 基础完成概率
            p_submit = 0.95 if is_top else (0.80 if not is_struggling else 0.55)
            if rng.random() > p_submit:
                continue

            # 针对不同实验注入真实特征指标
            if exp_id == 'A1_cutin_aeb':
                # 高频易错点：加塞碰撞
                has_collision = (rng.random() < 0.40) if is_struggling else (rng.random() < 0.08)
                ttc = rng.uniform(0.5, 0.95) if has_collision else rng.uniform(1.6, 2.8)
                stu_res[exp_id] = {'collision': has_collision, 'min_ttc_s': round(ttc, 2)}
            elif exp_id == 'B3_sumo_cacc':
                # 高频易错点：编队弦不稳定
                err = rng.uniform(2.2, 3.8) if (is_struggling or rng.random() < 0.30) else rng.uniform(0.6, 1.4)
                stu_res[exp_id] = {'max_spacing_error': round(err, 2), 'steps': 400}
            elif exp_id == 'C1_fastsim_energy':
                # 高频易错点：电耗过高
                energy = rng.uniform(21.0, 26.5) if (is_struggling and rng.random() < 0.45) else rng.uniform(11.8, 14.2)
                stu_res[exp_id] = {'energy_kwh_100km': round(energy, 2), 'cd': 0.28, 'mass': 1700}
            elif exp_id == 'D4_lithium_plating':
                # 高频易错点：大倍率未析锂或错误常态析锂
                pot = rng.uniform(0.01, 0.15) if (is_struggling and rng.random() < 0.35) else rng.uniform(-0.85, -0.25)
                stu_res[exp_id] = {'min_potential_3c_v': round(pot, 2)}
            elif exp_id == 'E3_mpc_follow':
                # 高频易错点：求解超时
                solve_ms = rng.uniform(55.0, 95.0) if (is_struggling and rng.random() < 0.35) else rng.uniform(9.0, 24.0)
                stu_res[exp_id] = {'avg_solve_ms': round(solve_ms, 1), 'max_spacing_error': 0.9}
            elif exp_id == 'Capstone_iev_integrated':
                cap_col = (rng.random() < 0.30) if is_struggling else (rng.random() < 0.05)
                stu_res[exp_id] = {
                    'collision': cap_col,
                    'min_ttc_s': round(rng.uniform(0.7, 1.2) if cap_col else rng.uniform(1.6, 2.5), 2),
                    'window_net_kwh': round(rng.uniform(0.015, 0.035), 3),
                    'capstone_completed': True
                }
            else:
                # 其他常规实验随机合理通过
                p_pass = 0.95 if is_top else (0.85 if not is_struggling else 0.60)
                is_passed = (rng.random() < p_pass)
                # 依据规则构造合适指标
                stu_res[exp_id] = {'passed': is_passed, 'score': 85.0 if is_passed else 45.0}

        mock_data[stu] = stu_res

    return mock_data


def compute_class_failure_analytics(all_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """深度聚合并统计全班高频失效模式与易错实验排行 (Top 5 Failure Modes)"""
    if all_results is None:
        all_results = _get_demo_class_results()

    failure_counts = {}
    exp_stats = {}

    for stu, exps in all_results.items():
        if stu in ('admin', 'lost+found'):
            continue
        for exp_id, metrics in exps.items():
            if exp_id not in exp_stats:
                exp_stats[exp_id] = {'n_submissions': 0, 'n_failed': 0, 'n_passed': 0}
            exp_stats[exp_id]['n_submissions'] += 1

            # 评测是否达标
            graded = grade_metrics(exp_id, metrics if isinstance(metrics, dict) else {})
            if not graded['passed']:
                exp_stats[exp_id]['n_failed'] += 1
                # 归因诊断
                diag = diagnose_experiment(exp_id, metrics if isinstance(metrics, dict) else {})
                for f in diag.get('findings', []):
                    key = (exp_id, f['symptom'])
                    if key not in failure_counts:
                        failure_counts[key] = {
                            'exp_id': exp_id,
                            'exp_name': diag['experiment_name'],
                            'symptom': f['symptom'],
                            'severity': f['severity'],
                            'physics_root_cause': f['physics_root_cause'],
                            'prescriptions': f['prescriptions'],
                            'oem_benchmark': f.get('oem_benchmark', ''),
                            'tuning_matrix': f.get('tuning_matrix', []),
                            'occurrences': 0,
                            'affected_students': []
                        }
                    failure_counts[key]['occurrences'] += 1
                    failure_counts[key]['affected_students'].append(stu)
            else:
                exp_stats[exp_id]['n_passed'] += 1

    # 排序得到 Top 5 高频失效
    top_failures = sorted(
        failure_counts.values(),
        key=lambda x: (1 if x['severity'] == 'critical' else 0, x['occurrences']),
        reverse=True
    )[:5]

    total_submissions = sum(s['n_submissions'] for s in exp_stats.values())
    total_failures = sum(s['n_failed'] for s in exp_stats.values())

    return {
        'total_students': len(all_results),
        'total_submissions': total_submissions,
        'total_failures': total_failures,
        'exp_stats': exp_stats,
        'top_failures': top_failures,
    }


def render_side_by_side_comparison_html(exp_id: str = 'A1_cutin_aeb') -> str:
    """生成“优秀满分方案 vs 典型受阻方案”同屏双栏动态对标卡片 (HTML)"""
    clean_id = exp_id.replace('_pro', '').replace('_export', '')
    if clean_id not in SIDE_BY_SIDE_CASES:
        clean_id = 'A1_cutin_aeb'

    case = SIDE_BY_SIDE_CASES[clean_id]
    f = case['failed']
    g = case['golden']

    def _render_col(c: dict, is_gold: bool):
        badge = "🏆 优秀满分工程方案 (Gold Standard)" if is_gold else "⚠️ 典型受阻方案 (Typical Failure)"
        params_html = "".join(f"<div style='margin-bottom: 4px;'>• <b style='color: #334155;'>{k}</b>: <span style='font-family: monospace; color: #0284c7;'>{v}</span></div>" for k, v in c['params'].items())
        metrics_html = "".join(f"<div style='margin-bottom: 4px;'>• <b style='color: #334155;'>{k}</b>: <span style='font-weight: 700; color: {c['badge_color']};'>{v}</span></div>" for k, v in c['metrics'].items())

        return f"""
        <div style="flex: 1 1 340px; background: {c['bg_color']}; border: 1.5px solid {c['border_color']}; border-radius: 10px; padding: 14px 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0,0,0,0.08); padding-bottom: 8px; margin-bottom: 10px;">
                <span style="font-size: 13px; font-weight: 800; color: {c['badge_color']};">{badge}</span>
                <span style="background: white; border: 1px solid {c['border_color']}; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 700; color: #475569;">{c['title']}</span>
            </div>

            <div style="font-size: 12px; margin-bottom: 10px;">
                <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">🎛️ 核心控制参数标定：</div>
                {params_html}
            </div>

            <div style="font-size: 12px; margin-bottom: 10px;">
                <div style="font-weight: 700; color: #0f172a; margin-bottom: 4px;">📊 实测动力学响应输出：</div>
                {metrics_html}
            </div>

            <div style="font-size: 11.5px; line-height: 1.5; color: #334155; background: rgba(255,255,255,0.7); border-radius: 6px; padding: 8px 10px; margin-bottom: 8px;">
                <b>📈 动力学过程演化：</b>{c['behavior_curve']}
            </div>

            <div style="font-size: 11.5px; line-height: 1.4; color: #475569; border-top: 1px dashed rgba(0,0,0,0.1); padding-top: 6px;">
                <b>🔍 机理本质：</b>{c['root_cause']}
            </div>
        </div>
        """

    html = f"""
    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 12px; padding: 16px 20px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 14px;">
            <div>
                <span style="background: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;">
                    {case['domain']}
                </span>
                <h3 style="margin: 4px 0 0 0; color: #0f172a; font-size: 16px; font-weight: 700;">
                    ⚖️ 课堂同屏对标演示器：{case['name']} ({clean_id})
                </h3>
            </div>
            <div style="font-size: 12px; color: #64748b; font-weight: 600;">
                聚焦评测标尺：<span style="color: #2563eb;">{case['focus_metric']}</span>
            </div>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 16px;">
            {_render_col(f, is_gold=False)}
            {_render_col(g, is_gold=True)}
        </div>
    </div>
    """
    return html


def render_teacher_live_dashboard_html(
    all_results: Optional[Dict[str, Any]] = None,
    class_name: str = "智能网联新能源汽车专业 2026 级"
) -> str:
    """生成全景观摩与多媒体大屏授课演示中心 (HTML)"""
    if all_results is None:
        all_results = _get_demo_class_results()

    # 1. 基础全班统计
    grade_table = build_grade_table(all_results)
    stats = statistics(grade_table)
    analytics = compute_class_failure_analytics(all_results)
    skills_matrix = compute_class_skills_matrix(grade_table)

    n_students = stats.get('n_students', len(all_results))
    avg_score = stats.get('mean', 0.0)
    pass_rate = stats.get('pass_rate', 0.0)
    cap_pass_rate = stats.get('capstone_pass_rate', 0.0)
    mean_comp = stats.get('mean_completion_rate', 0.0)

    # 2. 8 大能力热力柱状条
    skills_bars_html = ""
    for dim_k, dim_val, dim_name in skills_matrix.get('weakness_ranking', []):
        info = skills_matrix['dimensions'][dim_k]
        score = info['mean_score']
        p_rate = info['pass_rate']
        c_code = info['color']

        status_text = "极度薄弱" if score < 50 else ("需复导" if score < 70 else "良好")
        status_color = "#dc2626" if score < 50 else ("#d97706" if score < 70 else "#16a34a")

        skills_bars_html += f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 3px;">
                <span style="font-weight: 600; color: #1e293b;">{dim_name}</span>
                <span style="color: #64748b;">及格率: {p_rate:.0f}% | 均分: <b style="color: {c_code};">{score:.1f}</b> ({status_text})</span>
            </div>
            <div style="background: #e2e8f0; height: 8px; border-radius: 4px; overflow: hidden;">
                <div style="background: {c_code}; width: {min(100.0, max(0.0, score))}%; height: 100%;"></div>
            </div>
        </div>
        """

    # 3. Top 5 高频失效讲评卡片
    top_failures_html = ""
    for idx, f in enumerate(analytics.get('top_failures', [])):
        sev = f['severity']
        sev_color = "#dc2626" if sev == 'critical' else "#ea580c"
        sev_label = "🚨 致命失效" if sev == 'critical' else "⚠️ 显著偏差"
        occ = f['occurrences']
        pct = (occ / n_students) * 100.0 if n_students > 0 else 0

        rx_list = "".join(f"<li style='margin-bottom: 2px;'>{r}</li>" for r in f['prescriptions'][:2])

        top_failures_html += f"""
        <div style="background: #ffffff; border-left: 4px solid {sev_color}; border: 1px solid #e2e8f0; border-left-width: 4px; border-radius: 6px; padding: 10px 14px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <strong style="color: #0f172a; font-size: 13px;">#{idx+1} 【{f['exp_id']}】{f['symptom']}</strong>
                <span style="background: {sev_color}15; color: {sev_color}; padding: 1px 8px; border-radius: 10px; font-size: 10.5px; font-weight: 700;">
                    {sev_label} · {occ} 人触发 ({pct:.0f}%)
                </span>
            </div>
            <div style="font-size: 11.5px; color: #475569; line-height: 1.4; margin-bottom: 6px;">
                <b>机理因果：</b>{f['physics_root_cause']}
            </div>
            <div style="font-size: 11px; color: #166534; background: #f0fdf4; padding: 4px 8px; border-radius: 4px;">
                <b>课堂讲评处方：</b>
                <ul style="margin: 2px 0 0 16px; padding: 0;">
                    {rx_list}
                </ul>
            </div>
        </div>
        """

    # 4. 嵌入一个默认的 A1 同屏对比
    sample_compare_html = render_side_by_side_comparison_html('A1_cutin_aeb')

    html = f"""
    <div style="background: #f8fafc; border: 1.5px solid #cbd5e1; border-radius: 14px; padding: 22px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.06);">
        <!-- 顶栏：教学大屏抬头与全班总体概况 -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
            <div>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 26px;">🎓</span>
                    <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 800;">
                        IEV CloudLab 教师多媒体演示中心与学情全景洞察看板
                    </h2>
                </div>
                <p style="margin: 4px 0 0 34px; color: #64748b; font-size: 13px;">
                    授课班级: <strong style="color: #1e293b;">{class_name}</strong> | 贯穿全课程 29 门专业实验与 Capstone 全域大作业
                </p>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 14px; text-align: center;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">在册学生</div>
                    <div style="font-size: 18px; font-weight: 800; color: #0f172a;">{n_students} <span style="font-size: 11px; font-weight: normal;">人</span></div>
                </div>
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 14px; text-align: center;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">课程平均分</div>
                    <div style="font-size: 18px; font-weight: 800; color: #2563eb;">{avg_score:.1f} <span style="font-size: 11px; font-weight: normal;">分</span></div>
                </div>
                <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 14px; text-align: center;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">平时完成率</div>
                    <div style="font-size: 18px; font-weight: 800; color: #10b981;">{mean_comp:.1f}%</div>
                </div>
                <div style="background: #ffffff; border: 1.5px solid #facc15; border-radius: 8px; padding: 6px 14px; text-align: center; background: #fefce8;">
                    <div style="font-size: 11px; color: #854d0e; font-weight: 700;">★ Capstone 通关</div>
                    <div style="font-size: 18px; font-weight: 800; color: #ca8a04;">{cap_pass_rate:.1f}%</div>
                </div>
            </div>
        </div>

        <!-- 中部：双栏布局（左侧 8 大能力热力矩阵，右侧 Top 5 易错高频失效讲评） -->
        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start; margin-bottom: 20px;">
            <div style="flex: 1 1 380px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 12px;">
                    <h4 style="margin: 0; font-size: 14px; font-weight: 700; color: #0f172a;">
                        📊 全班 8 大工程能力达成度分布
                    </h4>
                    <span style="font-size: 11px; color: #64748b;">按均分由低到高预警排序</span>
                </div>
                {skills_bars_html}
            </div>

            <div style="flex: 1 1 440px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 8px; margin-bottom: 12px;">
                    <h4 style="margin: 0; font-size: 14px; font-weight: 700; color: #0f172a;">
                        🚨 全班高频机理失效模式排行榜 (Top 5)
                    </h4>
                    <span style="font-size: 11px; color: #64748b;">重点备课与课堂讲评攻坚</span>
                </div>
                {top_failures_html if top_failures_html else '<p style="color: #10b981;">恭喜！全班实验运行均达工业标定基准，未检测到聚集性机理失效。</p>'}
            </div>
        </div>

        <!-- 底部：课堂同屏对标视窗 (优秀标定 vs 典型受阻) -->
        {sample_compare_html}
    </div>
    """
    return html


def show_teacher_presentation(all_results: Optional[Dict[str, Any]] = None):
    """供教师在 Jupyter Notebook 中一键运行的全屏教学演示中心"""
    from IPython.display import HTML, display
    display(HTML(render_teacher_live_dashboard_html(all_results)))


def export_teacher_debrief_markdown(
    all_results: Optional[Dict[str, Any]] = None,
    class_name: str = "智能网联新能源汽车专业 2026 级"
) -> str:
    """导出可直接复制为 PPT 或教学汇报的 Markdown 格式课堂讲评教案"""
    if all_results is None:
        all_results = _get_demo_class_results()

    grade_table = build_grade_table(all_results)
    stats = statistics(grade_table)
    analytics = compute_class_failure_analytics(all_results)

    lines = [
        f"# 🎓 {class_name} 实验教学全景学情与课堂讲评教案",
        "",
        "## 一、全班总体学情关键指标",
        f"- **在册学生人数**：{stats.get('n_students', 0)} 人",
        f"- **课程综合均分**：{stats.get('mean', 0.0):.1f} 分 (及格率 {stats.get('pass_rate', 0.0):.1f}%)",
        f"- **平时实验平均完成率**：{stats.get('mean_completion_rate', 0.0):.1f}%",
        f"- **Capstone 期末全域大作业通关率**：{stats.get('capstone_pass_rate', 0.0):.1f}%",
        "",
        "## 二、全班高频机理失效排行榜与讲评要点 (Top 5)",
        ""
    ]

    for idx, f in enumerate(analytics.get('top_failures', []), 1):
        lines.append(f"### {idx}. 【{f['exp_id']}】{f['symptom']}")
        lines.append(f"- **受影响人数**：{f['occurrences']} 人 (占比 {(f['occurrences']/len(all_results))*100:.1f}%)")
        lines.append(f"- **严重级别**：{f['severity'].upper()}")
        lines.append(f"- **物理第一性原理因果**：{f['physics_root_cause']}")
        lines.append(f"- **主机厂工程规范**：{f['oem_benchmark']}")
        lines.append("- **课堂调优处方建议**：")
        for p in f['prescriptions']:
            lines.append(f"  * {p}")
        lines.append("")

    lines.append("## 三、典型实验正反方案同屏对标板书")
    lines.append("- 详见 Jupyter 原生大屏中的动态对标组件 (`render_side_by_side_comparison_html('A1_cutin_aeb')`)")

    return "\n".join(lines)
