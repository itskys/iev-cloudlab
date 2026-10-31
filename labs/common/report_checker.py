"""IEV CloudLab 实验报告数字一致性自动核验工具 | Report Consistency Checker

功能说明：
  针对实验报告占总成绩 60% 的教学评定场景，自动核验学生提交的 Markdown 报告中
  所声称的实验数值与实际仿真运行归档文件 (labs/data/results/<exp_id>.json) 是否一致。

核心特性：
  1. 100% 规则驱动：纯正则与结构化文本解析，零外部大模型 API 调用，零网络依赖，毫秒级执行；
  2. 多格式自适应抽取：
     - Markdown 表格语法（| 指标 | 实验值 | 判据 |）
     - 行内键值对与列表（- 最小TTC: 1.85s / min_ttc = 1.85）
     - 叙述性文本（“车辆最小TTC达到了1.85秒，未发生碰撞...”）
  3. 智能指标映射与别名对齐（中英文双语识别，继承自 evaluator 判据体系）；
  4. 容差与防伪判断：
     - 浮点数相对容差 rtol (默认 5%) 与绝对容差 atol (默认 0.05)
     - 碰撞与成功状态布尔强校验（严防撞车假报无碰撞的学术不端行为）；
  5. 综合一致性评分 (0-100) 与教师/学生友好的 Markdown/HTML 视觉核验报告。
"""

import json
import math
import os
import re
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from common.evaluator import GRADING_SPECS, METRIC_ALIASES
except ImportError:
    try:
        from .evaluator import GRADING_SPECS, METRIC_ALIASES
    except ImportError:
        GRADING_SPECS = {}
        METRIC_ALIASES = {}

# 指标中英文语义映射表：用户在报告中的称谓 -> GRADING_SPECS 中的 canonical metric_key
METRIC_KEYWORD_MAP = {
    'min_ttc_s': [
        '最小ttc', '最小碰撞时间', 'min_ttc', 'ttc_min', 'ttc', '最小时距', '碰撞时间'
    ],
    'collision': [
        '碰撞状态', '是否碰撞', '发生碰撞', '碰撞', 'collision', '撞击'
    ],
    'max_spacing_error_m': [
        '最大间距误差', '间距误差', '跟车间距误差', 'max_spacing_error', 'spacing_error'
    ],
    'max_spacing_error': [
        '最大间距误差', '编队间距误差', 'cacc间距误差'
    ],
    'pet_s': [
        '后侵入时间', 'pet', 'post_encroachment_time', 'pet时间'
    ],
    'completed': [
        '演示运行完成', '运行完成', '演示完成', 'completed', '执行完成'
    ],
    'rmse': [
        '标定rmse', '均方根误差', 'rmse', '拟合误差'
    ],
    'delay_reduction_pct': [
        '延误降低', '延误改善', '延误降低率', 'delay_reduction', '延误优化'
    ],
    'steps': [
        '仿真步数', '总步数', 'steps', '仿真步长数'
    ],
    'wave_speed_kmh': [
        '拥堵波速', '波速', 'wave_speed', '传播速度', '拥堵传播速度'
    ],
    'r_squared': [
        '拟合r²', '拟合r2', 'r_squared', 'r2', '拟合优度', '决定系数', 'r^2'
    ],
    'stops_reduction_pct': [
        '停车减少', '停车改善', '停车次数降低', 'stops_reduction', '停车次数减少'
    ],
    'energy_kwh_100km': [
        '百公里电耗', '百公里耗电', '综合电耗', '电耗', 'energy_kwh_100km', 'kwh/100km', '百公里能量消耗'
    ],
    'n_vehicles': [
        '对比车型数', '车型数量', '测试车型数', 'n_vehicles'
    ],
    's_mass': [
        '质量灵敏度', '质量影响灵敏度', 's_mass'
    ],
    's_cd': [
        '风阻灵敏度', '迎风阻力灵敏度', 's_cd', '阻力系数灵敏度'
    ],
    'n_strategies': [
        '策略对比数', '对比策略数', '策略种类', 'n_strategies'
    ],
    'capacity_ah': [
        '1c容量', '电池容量', '实际容量', '标称容量', 'capacity_ah', '容量(ah)'
    ],
    'peukert_k': [
        'peukert指数', 'peukert系数', 'peukert_k', '培克特常数'
    ],
    'calibration_error_pct': [
        '标定误差', '最大标定误差', '平均标定误差', 'calibration_error', 'ocv误差'
    ],
    'min_potential_3c_v': [
        '3c最低电位', '析锂最低电位', '负极最低电位', 'min_potential', '最低电位'
    ],
    'saving_pct': [
        '节油率', '节油比例', '节油百分比', 'saving_pct', '油耗节省'
    ],
    'n_pareto': [
        'pareto解', '帕累托解', 'pareto解数量', 'pareto最优解', 'pareto前沿解'
    ],
    'avg_solve_ms': [
        '平均求解时间', '求解耗时', 'mpc求解时间', '单步求解时间', 'avg_solve_ms'
    ],
    'fuel_l_100km': [
        'dp油耗', '百公里油耗', '等效百公里油耗', 'fuel_consumption', 'fuel_l_100km'
    ],
    'fmu_loaded': [
        'fmu加载', 'fmu加载成功', 'fmu_loaded', 'api验证'
    ],
    'max_error': [
        '解析解误差', '与解析解误差', '最大解析误差', 'max_error'
    ],
    'v_err_pct': [
        '速度误差', '车速跟踪误差', '速度相对误差', 'v_err_pct'
    ],
    'x_err_pct': [
        '位置误差', '位移跟踪误差', '位置相对误差', 'x_err_pct'
    ],
    'messages_received': [
        '话题收发', '话题接收数', '消息接收数', 'messages_received'
    ],
    'service_ok': [
        '服务调用', '服务响应成功', 'service_ok', '服务成功'
    ],
    'n_scenarios': [
        '场景生成数', '生成场景数', '批量场景数', 'n_scenarios'
    ],
    'monotonic': [
        'ttc单调性', '单调性', '单调性成立', 'monotonic'
    ],
    'pass_rate': [
        '通过率', '场景通过率', '模糊测试通过率', 'pass_rate'
    ],
    'false_trigger_rate': [
        '误触发率', '虚警率', 'false_trigger_rate'
    ],
}


def _clean_str(s: str) -> str:
    """清理字符串以便模式匹配"""
    return re.sub(r'[\s_\-:*`#]+', '', s.lower())


def _parse_bool(val_str: str) -> Optional[bool]:
    """将文本解析为布尔值"""
    s = val_str.strip().lower()
    if s in ('false', '0', '否', '无', '无碰撞', '未发生', '未碰撞', '失败', '未发生碰撞', '不碰撞'):
        return False
    if s in ('true', '1', '是', '有', '发生', '发生碰撞', '成功', '达标', '单调', '已完成'):
        return True
    return None


def _parse_number(val_str: str) -> Optional[float]:
    """从文本中提取浮点数（支持正负号、百分号、科学计数法）"""
    # 提取常见带单位的数值，如 "1.85 s", "12.5 kWh", "-2.4 km/h", "72.8%", "3.3e-16"
    match = re.search(r'([+\-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+\-]?\d+)?)\s*(%?)', val_str.strip())
    if match:
        num_str, pct = match.groups()
        try:
            val = float(num_str)
            # 若包含百分号且原判据不是以百分比整数形式计量的，则根据需要处理
            return val
        except ValueError:
            return None
    return None


def extract_claims_from_markdown(markdown_text: str) -> Dict[str, Any]:
    """从 Markdown 报告中提取所有提及的量化指标和布尔状态。
    
    返回字典: {canonical_metric_key: parsed_value}
    """
    claims = {}
    lines = markdown_text.splitlines()

    # 1. 优先解析 Markdown 表格行：| 列1 | 列2 | ... |
    for line in lines:
        line_strip = line.strip()
        if line_strip.startswith('|') and line_strip.endswith('|'):
            cells = [c.strip() for c in line_strip.split('|')[1:-1]]
            if len(cells) >= 2:
                # 遍历可能的列，尝试找出指标名称和对应数值
                name_cell = cells[0]
                val_cell = cells[1]
                norm_name = _clean_str(name_cell)

                # 匹配 canonical key
                for canonical_key, keywords in METRIC_KEYWORD_MAP.items():
                    if any(_clean_str(kw) in norm_name for kw in keywords):
                        # 判断是否为布尔类型指标
                        if canonical_key in ('collision', 'completed', 'fmu_loaded', 'service_ok', 'monotonic'):
                            b_val = _parse_bool(val_cell)
                            if b_val is not None:
                                claims[canonical_key] = b_val
                                break
                        # 数值类型指标
                        num_val = _parse_number(val_cell)
                        if num_val is not None:
                            claims[canonical_key] = num_val
                            break

    # 2. 解析行内键值对与列表：- 最小TTC: 1.85s / min_ttc = 1.85 / 延误降低: 72.8%
    kv_pattern = re.compile(r'[-*•]?\s*([^:\n=]{2,25})\s*[:=：]\s*([^\n,，;；]+)')
    for match in kv_pattern.finditer(markdown_text):
        key_raw, val_raw = match.groups()
        norm_key = _clean_str(key_raw)

        for canonical_key, keywords in METRIC_KEYWORD_MAP.items():
            if canonical_key in claims:
                continue  # 表格提取优先
            if any(_clean_str(kw) in norm_key for kw in keywords):
                if canonical_key in ('collision', 'completed', 'fmu_loaded', 'service_ok', 'monotonic'):
                    b_val = _parse_bool(val_raw)
                    if b_val is not None:
                        claims[canonical_key] = b_val
                        break
                num_val = _parse_number(val_raw)
                if num_val is not None:
                    claims[canonical_key] = num_val
                    break

    # 3. 解析叙述性自然语言模式（针对高频核心指标的兜底）
    if 'min_ttc_s' not in claims:
        ttc_m = re.search(r'(?:最小ttc|ttc最小(?:值)?)[为达到是：:\s]*([0-9]+\.?[0-9]*)', markdown_text, re.I)
        if ttc_m:
            claims['min_ttc_s'] = float(ttc_m.group(1))

    if 'collision' not in claims:
        if re.search(r'(?:无碰撞|未发生碰撞|零碰撞|未碰撞|全程无撞击)', markdown_text):
            claims['collision'] = False
        elif re.search(r'(?:发生碰撞|造成碰撞|出现撞击|发生追尾)', markdown_text):
            claims['collision'] = True

    if 'energy_kwh_100km' not in claims:
        energy_m = re.search(r'(?:电耗|百公里电耗|百公里耗电)[为达到是：:\s]*([0-9]+\.?[0-9]*)\s*(?:kwh)?', markdown_text, re.I)
        if energy_m:
            claims['energy_kwh_100km'] = float(energy_m.group(1))

    return claims


def verify_report_consistency(
    markdown_content: str,
    actual_results: Union[Dict[str, Any], str],
    experiment_id: Optional[str] = None,
    rtol: float = 0.05,
    atol: float = 0.05,
) -> Dict[str, Any]:
    """核验学生 Markdown 报告声称的数值与实际仿真运行记录的一致性。

    :param markdown_content: 学生实验报告 Markdown 文本
    :param actual_results: 实际结果字典，或 labs/data/results/<exp_id>.json 路径
    :param experiment_id: 实验编号（如 'A1_cutin_aeb'），若未指定则尝试从 actual_results 或文本中推导
    :param rtol: 浮点数相对容差，默认 5% (0.05)
    :param atol: 浮点数绝对容差，默认 0.05 (针对近0数值)
    :return: 包含核验详情、一致性得分与评语的结构化报告字典
    """
    # 加载 actual_results
    if isinstance(actual_results, str):
        if not os.path.exists(actual_results):
            return {
                'verified': False,
                'error': f'Result file not found: {actual_results}',
                'consistency_score': 0.0,
                'verdict': 'FAIL_NO_RUN_RECORD',
            }
        with open(actual_results, 'r', encoding='utf-8') as f:
            actual_dict = json.load(f)
    else:
        actual_dict = dict(actual_results)

    # 提取实际运行中的指标项
    metrics_run = actual_dict.get('metrics', actual_dict)

    # 确定 experiment_id
    if not experiment_id:
        experiment_id = actual_dict.get('experiment_id', actual_dict.get('exp_id', actual_dict.get('experiment')))
    if not experiment_id:
        # 从文本寻找匹配的实验编号
        for exp_k in GRADING_SPECS.keys():
            if exp_k.lower() in markdown_content.lower():
                experiment_id = exp_k
                break

    # 从报告文本中提取学生陈述的所有数据
    report_claims = extract_claims_from_markdown(markdown_content)

    # 获取该实验预期的所有考评指标判据
    spec = GRADING_SPECS.get(experiment_id, {})
    criteria = spec.get('criteria', [])
    target_metric_keys = [c[0] for c in criteria]

    # 若判据中没有，则兜底检查 metrics_run 中的已有键
    if not target_metric_keys:
        target_metric_keys = list(metrics_run.keys())

    checks = []
    matched_count = 0
    severe_discrepancy = False

    for target_key in target_metric_keys:
        # 获取实际值（考虑别名）
        actual_val = None
        if target_key in metrics_run:
            actual_val = metrics_run[target_key]
        else:
            aliases = METRIC_ALIASES.get(target_key, [])
            for alias in aliases:
                if alias in metrics_run:
                    actual_val = metrics_run[alias]
                    break

        # 获取报告陈述值
        claimed_val = report_claims.get(target_key)
        if claimed_val is None:
            # 尝试通过别名寻找
            for alias in METRIC_ALIASES.get(target_key, []):
                if alias in report_claims:
                    claimed_val = report_claims[alias]
                    break

        item_result = {
            'metric': target_key,
            'claimed_val': claimed_val,
            'actual_val': actual_val,
            'status': 'UNKNOWN',
            'detail': '',
        }

        if actual_val is None:
            item_result['status'] = 'SKIPPED_NOT_IN_RUN'
            item_result['detail'] = '仿真未归档该指标'
            checks.append(item_result)
            continue

        if claimed_val is None:
            item_result['status'] = 'MISSING_IN_REPORT'
            item_result['detail'] = '报告中未明确陈述此项指标'
            checks.append(item_result)
            continue

        # 类型匹配与容差核对
        if isinstance(actual_val, bool):
            b_claimed = bool(claimed_val)
            if b_claimed == actual_val:
                item_result['status'] = 'MATCH'
                item_result['detail'] = f'状态完全一致 ({actual_val})'
                matched_count += 1
            else:
                item_result['status'] = 'CRITICAL_DISCREPANCY'
                item_result['detail'] = f'布尔状态颠倒: 报告称 {b_claimed}, 实际仿真为 {actual_val}'
                severe_discrepancy = True
        elif isinstance(actual_val, (int, float)):
            try:
                num_claimed = float(claimed_val)
                num_actual = float(actual_val)
                diff = abs(num_claimed - num_actual)
                rel_diff = diff / (abs(num_actual) + 1e-9)

                if diff <= atol or rel_diff <= rtol:
                    item_result['status'] = 'MATCH'
                    item_result['detail'] = f'数值吻合 (报告={num_claimed}, 实际={num_actual}, 相对误差={rel_diff:.2%})'
                    matched_count += 1
                elif rel_diff <= 0.20:
                    item_result['status'] = 'MINOR_DISCREPANCY'
                    item_result['detail'] = f'数值略有偏差 (报告={num_claimed}, 实际={num_actual}, 偏差={rel_diff:.2%})'
                else:
                    item_result['status'] = 'CRITICAL_DISCREPANCY'
                    item_result['detail'] = f'数值显著不符 (报告={num_claimed}, 实际={num_actual}, 偏差={rel_diff:.2%})'
                    severe_discrepancy = True
            except (ValueError, TypeError):
                item_result['status'] = 'PARSE_ERROR'
                item_result['detail'] = f'无法比对数值: claimed={claimed_val}, actual={actual_val}'
        else:
            # 字符串或枚举相等比较
            if str(claimed_val).strip().lower() == str(actual_val).strip().lower():
                item_result['status'] = 'MATCH'
                item_result['detail'] = '完全一致'
                matched_count += 1
            else:
                item_result['status'] = 'CRITICAL_DISCREPANCY'
                item_result['detail'] = f'不一致: 报告={claimed_val}, 实际={actual_val}'

        checks.append(item_result)

    # 计算一致性得分 (0 - 100)
    total_evaluable = sum(1 for c in checks if c['status'] in ('MATCH', 'MINOR_DISCREPANCY', 'CRITICAL_DISCREPANCY'))
    if total_evaluable == 0:
        consistency_score = 0.0
        verdict = 'INCONCLUSIVE_NO_METRICS_FOUND'
    else:
        raw_score = (matched_count / total_evaluable) * 100.0
        if severe_discrepancy:
            # 存在严重伪造或状态颠倒（如撞车谎称未碰撞），强力惩罚
            consistency_score = max(0.0, raw_score - 40.0)
            verdict = 'SUSPECTED_FABRICATION'
        elif matched_count == total_evaluable:
            consistency_score = 100.0
            verdict = 'VERIFIED_PERFECT'
        elif raw_score >= 80.0:
            consistency_score = round(raw_score, 1)
            verdict = 'VERIFIED_GOOD'
        else:
            consistency_score = round(raw_score, 1)
            verdict = 'DISCREPANCY_DETECTED'

    summary = {
        'experiment_id': experiment_id,
        'experiment_name': spec.get('name', experiment_id),
        'consistency_score': consistency_score,
        'verdict': verdict,
        'matched_count': matched_count,
        'total_evaluated': total_evaluable,
        'severe_discrepancy': severe_discrepancy,
        'checks': checks,
    }

    return summary


def format_verification_markdown(summary: Dict[str, Any]) -> str:
    """生成给教师和学生查看的 Markdown 报告一致性核验总结"""
    score = summary['consistency_score']
    verdict = summary['verdict']
    exp_name = summary.get('experiment_name', summary.get('experiment_id'))

    badge_status = 'PASS' if score >= 80 and not summary['severe_discrepancy'] else 'ALERT'
    badge_color = '🟢' if badge_status == 'PASS' else '🔴'

    lines = [
        f"### {badge_color} 实验报告数字一致性核验: {exp_name}",
        f"- **一致性得分**: `{score:.1f} / 100.0` ({summary['matched_count']}/{summary['total_evaluated']} 项指标核验一致)",
        f"- **核验结论**: `{verdict}`",
        "",
        "| 核查指标 (Metric) | 报告声称值 (Report) | 实际仿真值 (Actual) | 核验状态 | 详细诊断 |",
        "| :--- | :--- | :--- | :---: | :--- |",
    ]

    for c in summary['checks']:
        st = c['status']
        if st == 'MATCH':
            icon = '✅ 一致'
        elif st == 'MINOR_DISCREPANCY':
            icon = '⚠️ 微小偏差'
        elif st == 'CRITICAL_DISCREPANCY':
            icon = '❌ 严重不符'
        elif st == 'MISSING_IN_REPORT':
            icon = '❓ 报告未填'
        else:
            icon = '⚪ 跳过'

        lines.append(
            f"| `{c['metric']}` | `{c['claimed_val']}` | `{c['actual_val']}` | {icon} | {c['detail']} |"
        )

    if summary['severe_discrepancy']:
        lines.extend([
            "",
            "> ⚠️ **学术诚信预警**：检测到关键安全指标（如碰撞状态或核心性能）与实际仿真日志存在重大出入，请任课教师重点复核代码提交版本。",
        ])

    return "\n".join(lines)


def format_verification_html(summary: Dict[str, Any]) -> str:
    """生成可直接嵌入 Jupyter Notebook 的交互式 HTML 校验看板"""
    score = summary['consistency_score']
    is_pass = score >= 80 and not summary['severe_discrepancy']
    bg_color = "#f0fdf4" if is_pass else "#fef2f2"
    border_color = "#22c55e" if is_pass else "#ef4444"
    title_color = "#15803d" if is_pass else "#b91c1c"

    rows = ""
    for c in summary['checks']:
        st = c['status']
        if st == 'MATCH':
            badge = '<span style="color:#16a34a; font-weight:bold;">✅ MATCH</span>'
        elif st == 'MINOR_DISCREPANCY':
            badge = '<span style="color:#d97706; font-weight:bold;">⚠️ MINOR</span>'
        elif st == 'CRITICAL_DISCREPANCY':
            badge = '<span style="color:#dc2626; font-weight:bold;">❌ MISMATCH</span>'
        else:
            badge = '<span style="color:#6b7280;">⚪ N/A</span>'

        rows += f"""
        <tr style="border-bottom: 1px solid #e5e7eb;">
            <td style="padding: 6px 12px; font-family: monospace;">{c['metric']}</td>
            <td style="padding: 6px 12px; font-weight: 500;">{c['claimed_val']}</td>
            <td style="padding: 6px 12px; font-family: monospace; color: #1e40af;">{c['actual_val']}</td>
            <td style="padding: 6px 12px; text-align: center;">{badge}</td>
            <td style="padding: 6px 12px; font-size: 12px; color: #4b5563;">{c['detail']}</td>
        </tr>
        """

    html = f"""
    <div style="background: {bg_color}; border: 1px solid {border_color}; border-radius: 8px; padding: 16px; margin: 12px 0; font-family: system-ui, sans-serif;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
                <h4 style="margin: 0; color: {title_color}; font-size: 16px; font-weight: 600;">
                    🛡️ IEV 实验报告数字一致性核验看板: {summary.get('experiment_name', summary.get('experiment_id'))}
                </h4>
                <p style="margin: 4px 0 0 0; font-size: 12px; color: #6b7280;">
                    判定状态: <strong>{summary['verdict']}</strong> | 核验通过率: {summary['matched_count']}/{summary['total_evaluated']}
                </p>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 24px; font-weight: 700; color: {title_color};">{score:.1f}</span>
                <span style="font-size: 12px; color: #6b7280;">/ 100</span>
            </div>
        </div>
        <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 6px; overflow: hidden; font-size: 13px;">
            <thead>
                <tr style="background: #f8fafc; border-bottom: 2px solid #e2e8f0; text-align: left; color: #475569;">
                    <th style="padding: 8px 12px;">指标名 (Metric)</th>
                    <th style="padding: 8px 12px;">报告陈述 (Report)</th>
                    <th style="padding: 8px 12px;">仿真真值 (Actual)</th>
                    <th style="padding: 8px 12px; text-align: center;">核验结果</th>
                    <th style="padding: 8px 12px;">诊断说明</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
    </div>
    """
    return html


def check_student_directory(student_home: str, user_metrics: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """扫描指定学生主目录下的报告 Markdown 文件，并与结果 JSON 进行核验。

    :param student_home: 学生主目录路径（如 /home/jovyan 或 /opt/ievlab/home/testuser）
    :return: {experiment_id: verification_summary}
    """
    results_dir = os.path.join(student_home, 'labs', 'data', 'results')
    verified_results = {}

    # 常见报告存放目录
    search_dirs = [
        student_home,
        os.path.join(student_home, 'notebooks'),
        os.path.join(student_home, 'reports'),
    ]

    # 系统保留排除文件名
    ignore_files = {'readme.md', 'teacher_guide.md', 'syllabus_16weeks.md',
                    '学生快速上手指南.md', '教师指导手册.md', '课程大纲_16周.md', '实验手册.md', '自动评分说明.md'}

    candidate_files = []
    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            for fname in os.listdir(s_dir):
                if fname.lower().endswith('.md') and fname.lower() not in ignore_files:
                    full_p = os.path.join(s_dir, fname)
                    if os.path.isfile(full_p):
                        candidate_files.append(full_p)

    for md_path in candidate_files:
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            continue

        # 匹配对应实验编号
        matched_exp = None
        base_name = os.path.basename(md_path).lower()
        for exp_k in GRADING_SPECS.keys():
            prefix = exp_k.split('_')[0].lower()  # 如 'a1', 'b1', 'd3'
            if exp_k.lower() in base_name or (prefix in base_name and 'report' in base_name):
                matched_exp = exp_k
                break
            if exp_k.lower() in content.lower():
                matched_exp = exp_k
                break

        if not matched_exp:
            continue

        # 寻找对应的仿真结果 JSON 或从传入的已归档字典提取
        target_res = None
        target_json = os.path.join(results_dir, f"{matched_exp}.json")
        if os.path.exists(target_json):
            target_res = target_json
        else:
            target_export = os.path.join(results_dir, f"{matched_exp}_export.json")
            if os.path.exists(target_export):
                target_res = target_export
            elif user_metrics and matched_exp in user_metrics:
                target_res = user_metrics[matched_exp]

        if target_res is not None:
            summary = verify_report_consistency(content, target_res, experiment_id=matched_exp)
            summary['report_path'] = md_path
            verified_results[matched_exp] = summary

    return verified_results


def check_class_reports(home_base_dir: str = '/opt/ievlab/home') -> Dict[str, Dict[str, Any]]:
    """全班实验报告批量核验。支持直接扫描 /opt/ievlab/home，或在单用户容器内自动回退至已归档的 submitted_reports 目录。

    :param home_base_dir: 学生 home 根目录
    :return: {username: {exp_id: summary}}
    """
    class_summaries = {}

    # 加载已汇聚的全班成绩数据 (备用对齐)
    all_results = {}
    for res_candidate in [
        '/home/jovyan/grades/all_results.json',
        '/opt/ievlab/home/teacher/grades/all_results.json',
        os.path.expanduser('~/grades/all_results.json')
    ]:
        if os.path.isfile(res_candidate):
            try:
                with open(res_candidate, 'r', encoding='utf-8') as f:
                    all_results = json.load(f)
                break
            except Exception:
                pass

    # 1. 尝试直接扫描主目录 (如教师容器已挂载 /opt/ievlab/home 或在宿主机运行)
    if os.path.isdir(home_base_dir):
        for user in os.listdir(home_base_dir):
            if user in ('admin', 'lost+found') or user.startswith('.'):
                continue
            u_home = os.path.join(home_base_dir, user)
            if os.path.isdir(u_home):
                u_metrics = all_results.get(user)
                user_reports = check_student_directory(u_home, user_metrics=u_metrics)
                if user_reports:
                    class_summaries[user] = user_reports
        if class_summaries:
            return class_summaries

    # 2. 容器沙箱回退：扫描 collect_grades 自动归档的 submitted_reports 目录
    for rep_base in [
        '/home/jovyan/grades/submitted_reports',
        '/opt/ievlab/home/teacher/grades/submitted_reports',
        os.path.expanduser('~/grades/submitted_reports')
    ]:
        if os.path.isdir(rep_base):
            for user in os.listdir(rep_base):
                if user.startswith('.'):
                    continue
                u_rep_dir = os.path.join(rep_base, user)
                if os.path.isdir(u_rep_dir):
                    u_metrics = all_results.get(user)
                    user_reports = check_student_directory(u_rep_dir, user_metrics=u_metrics)
                    if user_reports:
                        class_summaries[user] = user_reports

    return class_summaries

