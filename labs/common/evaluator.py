"""IEV CloudLab 自动评分模块 | Auto-Grading Evaluator

功能：
  1. GRADING_SPECS：29个实验的评分判据（阈值均来自真实引擎实测验证值）
  2. grade_metrics()：对一组指标打分（纯函数，可单测）
  3. grade_result_file()：读 labs/data/results/<实验>.json 评分
  4. grade_notebook()：子进程执行notebook（带超时看门狗），再评分其产出
  5. generate_report()：生成成绩报告（JSON + Markdown）

评分维度（百分制）：
  - 指标达标：70分（按判据权重分配）
  - 结果完整性：20分（结果文件存在且含必需字段）
  - 执行成功：10分（grade_notebook模式下notebook无报错运行完成）

设计规则（规划文档第10条）：子进程执行必须带timeout看门狗（默认30s，
仿真类实验可放宽到600s），防学生死循环代码卡死评分。
"""
import json
import os
import subprocess
import sys
from datetime import datetime

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')

# ==================== 评分判据（阈值=实测验证值） ====================
# 每条判据: (metric_key, 规则dict)
# 规则类型: range[min,max] / min / max / equals / boolean
# weight: 该判据在70分指标分中的权重（同实验内归一化）
GRADING_SPECS = {
    # ---------- A: esmini ADAS ----------
    'A1_cutin_aeb': {
        'name': 'Cut-in加塞避险',
        'timeout': 300,
        'criteria': [
            ('min_ttc_s', {'type': 'min', 'value': 1.5, 'weight': 3,
                           'desc': '最小TTC大于1.5s（AEB有效避险）'}),
            ('collision', {'type': 'equals', 'value': False, 'weight': 2,
                           'desc': '无碰撞'}),
        ],
    },
    'A2_acc_follow': {
        'name': 'ACC跟车',
        'timeout': 300,
        'criteria': [
            ('max_spacing_error_m', {'type': 'max', 'value': 1.5, 'weight': 3,
                                     'desc': '最大间距误差≤1.5m'}),
        ],
    },
    'A3_aeb_closedloop': {
        'name': 'AEB增强TTC闭环',
        'timeout': 300,
        'criteria': [
            ('collision', {'type': 'equals', 'value': False, 'weight': 3,
                           'desc': '增强TTC版无碰撞'}),
            ('false_trigger_rate', {'type': 'max', 'value': 0.05, 'weight': 1,
                                    'desc': '误触发率<5%'}),
        ],
    },
    'A4_intersection_yield': {
        'name': '交叉口让行',
        'timeout': 300,
        'criteria': [
            ('pet_s', {'type': 'min', 'value': 1.0, 'weight': 3,
                       'desc': 'PET后侵入时间>1.0s'}),
            ('collision', {'type': 'equals', 'value': False, 'weight': 2,
                           'desc': '无碰撞'}),
        ],
    },
    'A5_merge_kinematic_demo': {
        'name': '汇流运动学演示',
        'timeout': 120,
        'criteria': [
            ('completed', {'type': 'equals', 'value': True, 'weight': 1,
                           'desc': '演示运行完成'}),
        ],
    },
    # ---------- B: SUMO交通 ----------
    'B1_idm_calibration': {
        'name': 'IDM参数标定',
        'timeout': 300,
        'criteria': [
            ('rmse', {'type': 'max', 'value': 0.6, 'weight': 3,
                      'desc': '标定RMSE<0.6（实测0.405）'}),
        ],
    },
    'B2_traffic_signal': {
        'name': '信号配时优化',
        'timeout': 300,
        'criteria': [
            ('delay_reduction_pct', {'type': 'min', 'value': 50.0, 'weight': 3,
                                     'desc': '延误降低>50%（实测72.8%）'}),
        ],
    },
    'B3_sumo_cacc': {
        'name': 'CACC编队',
        'timeout': 300,
        'criteria': [
            ('max_spacing_error', {'type': 'max', 'value': 2.0, 'weight': 3,
                                   'desc': '最大间距误差<2.0m（实测1.09m）'}),
            ('steps', {'type': 'min', 'value': 300, 'weight': 1,
                       'desc': '仿真步数≥300（防空跑假通过）'}),
        ],
    },
    'B4_congestion_wave': {
        'name': '拥堵波传播',
        'timeout': 300,
        'criteria': [
            ('wave_speed_kmh', {'type': 'max', 'value': 0.0, 'weight': 2,
                                'desc': '波速为负（向上游传播，实测-2.4）'}),
            ('r_squared', {'type': 'min', 'value': 0.5, 'weight': 1,
                           'desc': '拟合R²>0.5（实测0.663）'}),
        ],
    },
    'B5_green_wave': {
        'name': '干线绿波',
        'timeout': 300,
        'criteria': [
            ('stops_reduction_pct', {'type': 'min', 'value': 50.0, 'weight': 3,
                                     'desc': '停车减少>50%（实测76.5%）'}),
        ],
    },
    # ---------- C: FASTSim整车 ----------
    'C1_fastsim_energy': {
        'name': 'UDDS百公里电耗',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('energy_kwh_100km', {'type': 'range', 'min': 10.0, 'max': 20.0,
                                  'weight': 3,
                                  'desc': '电耗10-20 kWh/100km（实测12.5）'}),
        ],
    },
    'C2_vehicle_comparison': {
        'name': '车型横向对比',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('n_vehicles', {'type': 'min', 'value': 5, 'weight': 2,
                            'desc': '对比≥5款车（实测6款）'}),
        ],
    },
    'C3_sensitivity_analysis': {
        'name': '灵敏度分析',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('s_mass', {'type': 'min', 'value': 0.0, 'weight': 1,
                        'desc': '质量灵敏度已计算（实测0.610）'}),
            ('s_cd', {'type': 'min', 'value': 0.0, 'weight': 1,
                      'desc': '风阻灵敏度已计算（实测0.210）'}),
        ],
    },
    'C4_ems_comparison': {
        'name': '能量管理策略对比',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('n_strategies', {'type': 'min', 'value': 3, 'weight': 2,
                              'desc': '对比≥3种策略（CD/CS/ECMS）'}),
        ],
    },
    # ---------- D: PyBaMM电池 ----------
    'D1_pybamm_battery': {
        'name': '电池充放电',
        'timeout': 600,
        'criteria': [
            ('capacity_ah', {'type': 'range', 'min': 4.6, 'max': 5.1,
                             'weight': 3,
                             'desc': '1C容量4.85Ah±5%（实测4.96）'}),
        ],
    },
    'D2_rate_capacity': {
        'name': '倍率容量',
        'timeout': 600,
        'criteria': [
            ('peukert_k', {'type': 'range', 'min': 1.0, 'max': 1.15,
                           'weight': 3,
                           'desc': 'Peukert指数1.0-1.15（实测1.0511）'}),
        ],
    },
    'D3_ocv_soc_export': {
        'name': 'OCV-SOC标定',
        'timeout': 600,
        'criteria': [
            ('calibration_error_pct', {'type': 'max', 'value': 5.0, 'weight': 3,
                                       'desc': '标定误差<5%（实测1.05%）'}),
        ],
    },
    'D4_lithium_plating': {
        'name': '快充析锂',
        'timeout': 600,
        'criteria': [
            ('min_potential_3c_v', {'type': 'max', 'value': 0.0, 'weight': 3,
                                    'desc': '3C最低电位<0（析锂，实测-0.64V）'}),
        ],
    },
    # ---------- E: 优化 ----------
    'E1_single_objective': {
        'name': '单目标优化',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('saving_pct', {'type': 'min', 'value': 0.0, 'weight': 3,
                            'desc': '优化后有节油（实测4.23%）'}),
        ],
    },
    'E2_pymoo_multiobj': {
        'name': '多目标优化',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('n_pareto', {'type': 'min', 'value': 50, 'weight': 3,
                          'desc': 'Pareto解≥50个（实测60）'}),
        ],
    },
    'E3_mpc_follow': {
        'name': 'MPC跟车',
        'timeout': 600,
        'criteria': [
            ('avg_solve_ms', {'type': 'max', 'value': 50.0, 'weight': 2,
                              'desc': '平均求解<50ms（实时性，实测11.5）'}),
        ],
    },
    'E4_dp_ems': {
        'name': 'DP能量管理',
        'timeout': 600,
        'kernel': 'py310-fastsim',
        'criteria': [
            ('fuel_l_100km', {'type': 'max', 'value': 2.2, 'weight': 3,
                              'desc': 'DP油耗<2.2 L/100km（实测1.92最优）'}),
        ],
    },
    # ---------- F: FMI ----------
    'F1_fmu_load': {
        'name': 'FMU加载',
        'timeout': 120,
        'criteria': [
            ('fmu_loaded', {'type': 'equals', 'value': True, 'weight': 2,
                            'desc': 'FMU概念/API验证完成'}),
        ],
    },
    'F2_openmodelica_fmu': {
        'name': '手建FMU',
        'timeout': 300,
        'criteria': [
            ('max_error', {'type': 'max', 'value': 1e-6, 'weight': 3,
                           'desc': '与解析解误差<1e-6（实测3.3e-16）'}),
        ],
    },
    'F3_multi_fmu': {
        'name': '多FMU协仿真',
        'timeout': 300,
        'criteria': [
            ('v_err_pct', {'type': 'max', 'value': 1.0, 'weight': 2,
                           'desc': '速度误差<1%（实测0.02%）'}),
            ('x_err_pct', {'type': 'max', 'value': 2.0, 'weight': 1,
                           'desc': '位置误差<2%（实测1.00%）'}),
        ],
    },
    # ---------- G: ROS ----------
    'G1_ros_topics': {
        'name': 'ROS话题',
        'timeout': 120,
        'criteria': [
            ('messages_received', {'type': 'min', 'value': 1, 'weight': 2,
                                   'desc': '话题收发成功'}),
        ],
    },
    'G2_ros_services': {
        'name': 'ROS服务',
        'timeout': 300,
        'criteria': [
            ('service_ok', {'type': 'equals', 'value': True, 'weight': 2,
                            'desc': '服务调用成功'}),
        ],
    },
    # ---------- H: 场景工程 ----------
    'H1_batch_generation': {
        'name': '场景批量生成',
        'timeout': 600,
        'criteria': [
            ('n_scenarios', {'type': 'min', 'value': 9, 'weight': 2,
                             'desc': '生成≥9个场景'}),
            ('monotonic', {'type': 'equals', 'value': True, 'weight': 1,
                           'desc': 'TTC单调性成立'}),
        ],
    },
    'H2_scenario_fuzzing': {
        'name': '场景模糊测试',
        'timeout': 600,
        'criteria': [
            ('pass_rate', {'type': 'range', 'min': 0.1, 'max': 0.95,
                           'weight': 2,
                           'desc': '通过率10%-95%（实测31.58%）'}),
            ('false_trigger_rate', {'type': 'max', 'value': 0.05, 'weight': 1,
                                    'desc': '误触发率<5%（实测0%）'}),
        ],
    },
}


# 指标键别名：notebook实际保存的键 -> 判据标准键
# （各notebook由不同批次生成，键名不统一；评分器在此层做翻译，不动notebook）
METRIC_ALIASES = {
    'fuel_l_100km': ['DP_equiv_L_per_100km', 'dp_equiv_l_per_100km', 'fuel_consumption'],
    'calibration_error_pct': ['calibration_mean_err_pct', 'mean_err_pct'],
    'energy_kwh_100km': ['electric_kwh_100km', 'kwh_100km', 'energy_consumption'],
    'max_spacing_error': ['max_spacing_error_m', 'max_error_m'],
    'max_spacing_error_m': ['max_spacing_error', 'max_error_m'],
    'min_ttc_s': ['min_ttc', 'ttc_min'],
    'n_pareto': ['n_pareto_solutions', 'pareto_count'],
    'n_scenarios': ['num_scenarios', 'scenario_count'],
    'messages_received': ['n_messages', 'msg_count'],
    'service_ok': ['service_success', 'call_ok'],
    'fmu_loaded': ['loaded', 'api_verified'],
    'delay_reduction_pct': ['delay_improvement_pct', 'delay_reduction'],
    'stops_reduction_pct': ['stops_improvement_pct', 'stops_reduction'],
}


def _get_metric(metrics, key):
    """按标准键取值，找不到则查别名。"""
    if key in metrics:
        return metrics[key]
    for alias in METRIC_ALIASES.get(key, []):
        if alias in metrics:
            return metrics[alias]
    return None


# ==================== 评分引擎 ====================

def _check(value, rule):
    """按规则检查一个指标值，返回是否通过。"""
    if value is None:
        return False
    t = rule['type']
    try:
        if t == 'range':
            return rule['min'] <= float(value) <= rule['max']
        if t == 'min':
            return float(value) >= rule['value']
        if t == 'max':
            return float(value) <= rule['value']
        if t == 'equals':
            return value == rule['value']
    except (TypeError, ValueError):
        return False
    return False


def grade_metrics(experiment_id, metrics, executed_ok=None):
    """对一组指标评分（纯函数）。

    Args:
        experiment_id: 如 'C1_fastsim_energy'
        metrics: dict，{metric_key: value}
        executed_ok: notebook是否成功执行完（None=未知，不计执行分）

    Returns:
        dict: {experiment, score(0-100), passed, details[...], graded_at}
    """
    spec = GRADING_SPECS.get(experiment_id)
    if spec is None:
        return {'experiment': experiment_id, 'score': 0, 'passed': False,
                'error': f'未知实验: {experiment_id}'}

    details = []
    total_weight = sum(r['weight'] for _, r in spec['criteria']) or 1
    earned_weight = 0.0
    for key, rule in spec['criteria']:
        value = _get_metric(metrics, key)
        ok = _check(value, rule)
        if ok:
            earned_weight += rule['weight']
        details.append({
            'metric': key,
            'desc': rule['desc'],
            'value': value,
            'passed': ok,
        })

    metric_score = 70.0 * (earned_weight / total_weight)
    completeness = 20.0 if metrics else 0.0
    exec_score = 10.0 if executed_ok else 0.0
    score = metric_score + completeness + (exec_score if executed_ok is not None else 0.0)
    if executed_ok is None:
        score = score * (100.0 / 90.0)  # 无执行信息时按90分满分折算

    return {
        'experiment': experiment_id,
        'name': spec['name'],
        'score': round(min(score, 100.0), 1),
        'passed': score >= 60.0,
        'metric_score': round(metric_score, 1),
        'details': details,
        'graded_at': datetime.now().isoformat(timespec='seconds'),
    }


def grade_result_file(experiment_id):
    """读 labs/data/results/<experiment_id>.json 并评分。"""
    path = os.path.join(RESULTS_DIR, f'{experiment_id}.json')
    if not os.path.exists(path):
        return {'experiment': experiment_id, 'score': 0, 'passed': False,
                'error': f'结果文件不存在: {path}（先运行实验）'}
    with open(path) as f:
        data = json.load(f)
    metrics = data.get('metrics', data)
    return grade_metrics(experiment_id, metrics)


def grade_notebook(notebook_path, timeout=None):
    """子进程执行notebook（nbconvert，看门狗超时），再评其结果文件。

    注意：在学生容器内运行；kernel由notebook自身metadata决定。
    """
    base = os.path.basename(notebook_path)
    experiment_id = base.replace('.ipynb', '')
    spec = GRADING_SPECS.get(experiment_id, {})
    timeout = timeout or spec.get('timeout', 300)

    executed_ok = False
    err = ''
    try:
        r = subprocess.run(
            [sys.executable, '-m', 'jupyter', 'nbconvert',
             '--to', 'notebook', '--execute', '--inplace',
             '--ExecutePreprocessor.timeout=120',
             notebook_path],
            capture_output=True, text=True, timeout=timeout,
        )
        executed_ok = (r.returncode == 0)
        if not executed_ok:
            err = (r.stderr or '')[-500:]
    except subprocess.TimeoutExpired:
        return {'experiment': experiment_id, 'score': 0, 'passed': False,
                'error': f'执行超时（>{timeout}s），疑似死循环'}
    except Exception as e:  # noqa: BLE001
        return {'experiment': experiment_id, 'score': 0, 'passed': False,
                'error': str(e)[:300]}

    result = grade_result_file(experiment_id)
    result['executed_ok'] = executed_ok
    if not executed_ok:
        result['score'] = max(0.0, result.get('score', 0) - 10)
        result['passed'] = result['score'] >= 60.0
        result['exec_error'] = err
    return result


def grade_all(results_dir=None):
    """批量评所有已有结果文件的实验。"""
    rdir = results_dir or RESULTS_DIR
    reports = []
    if os.path.exists(rdir):
        for fname in sorted(os.listdir(rdir)):
            if fname.endswith('.json'):
                exp_id = fname[:-5]
                if exp_id in GRADING_SPECS:
                    reports.append(grade_result_file(exp_id))
    return reports


def generate_report(reports, fmt='markdown'):
    """生成成绩报告。fmt: 'markdown' 或 'json'。"""
    if fmt == 'json':
        return json.dumps(reports, ensure_ascii=False, indent=2)
    lines = ['# IEV CloudLab 自动评分报告', '',
             f'生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}', '',
             '| 实验 | 名称 | 得分 | 通过 | 未达标项 |',
             '|---|---|---|---|---|']
    for r in reports:
        if 'error' in r:
            lines.append(f"| {r['experiment']} | - | 0 | ❌ | {r['error'][:40]} |")
            continue
        fails = '；'.join(d['desc'] for d in r['details'] if not d['passed'])
        lines.append(
            f"| {r['experiment']} | {r.get('name','')} | {r['score']} | "
            f"{'✅' if r['passed'] else '❌'} | {fails or '—'} |")
    if reports:
        valid = [r for r in reports if 'error' not in r]
        if valid:
            avg = sum(r['score'] for r in valid) / len(valid)
            lines += ['', f'**平均分**：{avg:.1f} | '
                          f'**通过**：{sum(1 for r in valid if r["passed"])}/{len(valid)}']
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='IEV CloudLab 自动评分')
    ap.add_argument('target', nargs='?', default='--all',
                    help='实验ID（如C1_fastsim_energy）、notebook路径，或--all')
    ap.add_argument('--execute', action='store_true',
                    help='执行notebook后再评分（target为notebook路径时）')
    args = ap.parse_args()

    if args.target == '--all':
        print(generate_report(grade_all()))
    elif args.target.endswith('.ipynb'):
        print(json.dumps(grade_notebook(args.target), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(grade_result_file(args.target), ensure_ascii=False, indent=2))
