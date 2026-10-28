"""IEV CloudLab 实验报告综合质性语义评定与评语辅助 | Qualitative Report Evaluator

功能说明：
  配合 Tier 1 的数字一致性核验工具 (report_checker)，构建 100 分制高校级实验报告
  综合量化与质性评定体系。

评分细则与权重矩阵 (Rubric, 满分 100 分)：
  1. 仿真数据真实性与一致性 (Quantitative Integrity, 35%):
     - 调用 report_checker 核验报告数值与运行日志的吻合度，杜绝造假；
  2. 实验机理与工程背景 (Theoretical Foundation, 20%):
     - 考核工况定义、控制算法原理、电化学/动力学物理方程阐述完整度；
  3. 动力学响应与时序深入剖析 (Dynamic & Causal Analysis, 25%):
     - 考核各阶段时序划分、因果分析（如 TTC 下降触发制动、能量回收阶段流向）；
  4. 批判性工程思考与权衡改进 (Critical Reflection & Trade-offs, 20%):
     - 考核对安全 vs 舒适、虚警率 vs 漏警率、标定误差传递等工程妥协的深刻洞见。

输出产物：
  - 各维度细分得分与综合得分
  - 自动化智能评语草稿 (教师可一键采用或二次润色)
  - Jupyter Notebook 原生富文本质性评阅看板 (HTML)
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from common.report_checker import verify_report_consistency, extract_claims_from_markdown
    from common.evaluator import GRADING_SPECS
except ImportError:
    try:
        from .report_checker import verify_report_consistency, extract_claims_from_markdown
        from .evaluator import GRADING_SPECS
    except ImportError:
        try:
            from report_checker import verify_report_consistency, extract_claims_from_markdown
            from evaluator import GRADING_SPECS
        except ImportError:
            verify_report_consistency = None
            extract_claims_from_markdown = None
            GRADING_SPECS = {}


# 各专业模块的核心机理概念词库
DOMAIN_KEYWORDS = {
    'A': {  # 智能驾驶 ADAS / 纵向安全
        'theory': ['ttc', '碰撞时间', '时距', '安全距离', '阈值', '避险', 'aeb', 'acc', '运动学', '感知', '控制原理'],
        'dynamics': ['减速', '制动', '切入', '变道', '加塞', '时序', '加速度', '相对速度', '车距', '曲线', '轨迹'],
        'reflection': ['虚警', '漏警', '平顺', '舒适性', '追尾', '权衡', '改进', '鲁棒性', 'v2x', '车路协同', '传感器'],
    },
    'B': {  # 交通流 / SUMO
        'theory': ['idm', '跟驰模型', '交通流', '信号配时', '绿波', '编队', 'cacc', '激波', '微观仿真'],
        'dynamics': ['延误', '拥堵波', '排队', '通行能力', '波速', '上游', '下游', '时空图', '相变'],
        'reflection': ['瓶颈', '波动', '协同', '容量', '绿信比', '周期', '车路协同', '优化空间', '实际路网'],
    },
    'C': {  # FASTSim 整车能耗
        'theory': ['udds', 'wltc', '循环工况', '阻力', '滚阻', '风阻', '电机', '效率', '动力总成', '能量流'],
        'dynamics': ['电耗', '百公里', '再生制动', '回收', 'soc', '充放电', '功率', '做功', '里程'],
        'reflection': ['轻量化', '风阻系数', '传动比', '续航', '敏感性', '工况差异', '电池成组', '工程折中'],
    },
    'D': {  # 电池电化学 PyBaMM
        'theory': ['spm', '单粒子模型', 'ocv', 'soc', '电化学', '固相扩散', '液相', '极化', '锂离子'],
        'dynamics': ['倍率', '放电曲线', '内阻', '压降', '电位', '析锂', '容量衰减', '端电压', '标定误差'],
        'reflection': ['低温快充', '热失控', '寿命', '等效电路', '查表法', '跨尺度', '电池包成组', '安全性'],
    },
    'E': {  # 优化与能量管理
        'theory': ['动态规划', 'dp', '最优控制', 'pareto', '多目标', '目标函数', '约束条件', 'pymoo'],
        'dynamics': ['油耗', '等效', '状态转移', '逆向求解', '前向回溯', '收敛', '前沿解集', '折中解'],
        'reflection': ['实时性', '全局最优', '维数灾难', '工况先验', '在线应用', '规则基', '工程落地'],
    },
    'F': {  # FMI / 协仿真
        'theory': ['fmi', 'fmu', 'modelica', '联合仿真', '主控', '从属', '接口规范', '模型交换'],
        'dynamics': ['时间步长', '通信点', '数值积分', '代数环', '解耦', '误差传递', '同步'],
        'reflection': ['异构协同', '实时仿真', '跨域工具', '模型重用', '稳定性', '精度权衡'],
    },
    'G': {  # ROS 通信
        'theory': ['ros', 'dds', '话题', '服务', '发布', '订阅', '节点', '消息', '通信协议'],
        'dynamics': ['延迟', '吞吐', '回调', '异步', '同步调用', '丢包', '时间戳'],
        'reflection': ['中间件', '实时操作系统', '确定性', '带宽', '多机协同', '分布式架构'],
    },
    'H': {  # 场景工程与模糊测试
        'theory': ['openscenario', '场景', '泛化', '模糊测试', '测试用例', '参数空间', '覆盖率'],
        'dynamics': ['边界条件', '切入速度', '时距网格', '失效模式', '通过率', '临界工况'],
        'reflection': ['sotif', '预期功能安全', '边缘工况', '批量验证', '长尾问题', '测试充分性'],
    },
}


def _score_text_section(text: str, keywords: List[str], min_words: int = 30) -> Tuple[float, List[str]]:
    """基于语义词密度、逻辑连接词与论述篇幅打分 (0 - 100)"""
    if not text or len(text.strip()) < 10:
        return 0.0, []

    matched_kw = [kw for kw in keywords if kw.lower() in text.lower()]
    n_kw = len(matched_kw)
    char_len = len(text.strip())

    # 篇幅基础分 (0 - 40)
    len_score = min(40.0, (char_len / min_words) * 20.0)

    # 核心专业概念命中分 (0 - 40)
    kw_score = min(40.0, n_kw * 10.0)

    # 逻辑分析关联度加分 (0 - 20)
    logic_words = ['因为', '所以', '导致', '表明', '由于', '进而', '对比', '然而', '相比之下', '原因在于', '因此']
    n_logic = sum(1 for w in logic_words if w in text)
    logic_score = min(20.0, n_logic * 6.0)

    total = min(100.0, len_score + kw_score + logic_score)
    return round(total, 1), matched_kw


def evaluate_report_comprehensively(
    markdown_content: str,
    actual_results: Union[Dict[str, Any], str],
    experiment_id: str,
) -> Dict[str, Any]:
    """对学生实验报告进行 100 分制全面评估（35% 数据真值 + 65% 质性分析）。

    :param markdown_content: 学生提交的实验报告 Markdown
    :param actual_results: 运行结果字典或 JSON 文件路径
    :param experiment_id: 实验编号（如 'A1_cutin_aeb'）
    :return: 包含 4 大维度细分得分、综合总分及教师评语草稿的评估字典
    """
    # 1. 维度一：数据一致性核验 (满分 35 分)
    consistency_res = verify_report_consistency(markdown_content, actual_results, experiment_id)
    raw_cons_score = consistency_res['consistency_score']  # 0 - 100
    data_score = round((raw_cons_score / 100.0) * 35.0, 1)

    # 确定所属模块类型 (A-H)
    module_code = experiment_id[0].upper()
    domain = DOMAIN_KEYWORDS.get(module_code, DOMAIN_KEYWORDS['A'])

    # 文本分段解析
    # 提取：机理与背景部分、响应时序分析部分、工程反思改进部分
    lower_md = markdown_content.lower()

    # 2. 维度二：机理背景 (满分 20 分)
    theory_score_raw, theory_kw = _score_text_section(markdown_content, domain['theory'], min_words=60)
    theory_score = round((theory_score_raw / 100.0) * 20.0, 1)

    # 3. 维度三：动力学响应分析 (满分 25 分)
    dynamics_score_raw, dyn_kw = _score_text_section(markdown_content, domain['dynamics'], min_words=80)
    dynamics_score = round((dynamics_score_raw / 100.0) * 25.0, 1)

    # 4. 维度四：批判性工程反思 (满分 20 分)
    reflection_score_raw, ref_kw = _score_text_section(markdown_content, domain['reflection'], min_words=50)
    reflection_score = round((reflection_score_raw / 100.0) * 20.0, 1)

    # 综合总分 (0 - 100)
    total_score = round(data_score + theory_score + dynamics_score + reflection_score, 1)

    # 生成教师智能评语草稿
    strengths = []
    weaknesses = []

    if consistency_res['severe_discrepancy']:
        weaknesses.append("【严重预警】报告陈述数据与实际仿真日志存在重大出入或状态冲突，涉嫌造假！")
    elif data_score >= 32.0:
        strengths.append("仿真数据如实记录，关键测量值与仿真结果吻合度极高。")
    else:
        weaknesses.append("部分关键指标在报告中记录不完整或存在偏差。")

    if theory_score >= 16.0:
        strengths.append(f"实验背景与物理机理阐述清晰，准确运用了专业术语 ({', '.join(theory_kw[:4])})。")
    else:
        weaknesses.append("实验原理部分论述较为单薄，建议补充核心控制方程或工况标准定义。")

    if dynamics_score >= 20.0:
        strengths.append("时序动力学分析详实，能够准确梳理控制介入各阶段的因果演变。")
    else:
        weaknesses.append("对动力学时序曲线的变化原因缺乏深度剖析，停留在表面数据罗列。")

    if reflection_score >= 16.0:
        strengths.append("具有良好的工程思维，对参数敏感性与工程权衡做出了有深度的反思。")
    else:
        weaknesses.append("工程改进建议偏向空泛，建议结合实际量产应用场景给出具体优化策略。")

    feedback_draft = "【实验评语】"
    if strengths:
        feedback_draft += " " + "；".join(strengths) + "。"
    if weaknesses:
        feedback_draft += " 但需注意：" + "；".join(weaknesses)

    return {
        'experiment_id': experiment_id,
        'experiment_name': consistency_res.get('experiment_name', experiment_id),
        'total_score': total_score,
        'sections': {
            'data_integrity': {
                'name': '数据真实性核验',
                'score': data_score,
                'max_score': 35.0,
                'detail': consistency_res['verdict'],
                'consistency_summary': consistency_res,
            },
            'theory_background': {
                'name': '实验机理与工程背景',
                'score': theory_score,
                'max_score': 20.0,
                'matched_keywords': theory_kw,
            },
            'dynamics_analysis': {
                'name': '动力学响应时序分析',
                'score': dynamics_score,
                'max_score': 25.0,
                'matched_keywords': dyn_kw,
            },
            'critical_reflection': {
                'name': '批判性工程反思与改进',
                'score': reflection_score,
                'max_score': 20.0,
                'matched_keywords': ref_kw,
            },
        },
        'strengths': strengths,
        'weaknesses': weaknesses,
        'teacher_feedback_draft': feedback_draft,
    }


def render_report_evaluation_card(evaluation: Dict[str, Any]) -> str:
    """生成富文本质性评阅看板 (HTML)"""
    tot = evaluation['total_score']
    color = "#10b981" if tot >= 80 else ("#f59e0b" if tot >= 60 else "#ef4444")
    secs = evaluation['sections']

    rows = ""
    for sec_k, info in secs.items():
        s = info['score']
        max_s = info['max_score']
        pct = (s / max_s) * 100.0
        b_color = "#10b981" if pct >= 80 else ("#f59e0b" if pct >= 60 else "#ef4444")

        rows += f"""
        <tr style="border-bottom: 1px solid #f1f5f9;">
            <td style="padding: 8px 12px; font-weight: 600; color: #334155;">{info['name']}</td>
            <td style="padding: 8px 12px; font-weight: bold; color: {b_color};">{s:.1f} / {max_s:.0f}</td>
            <td style="padding: 8px 12px;">
                <div style="background: #e2e8f0; height: 6px; border-radius: 3px; overflow: hidden; width: 120px;">
                    <div style="background: {b_color}; width: {pct}%; height: 100%;"></div>
                </div>
            </td>
        </tr>
        """

    html = f"""
    <div style="background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px; margin: 12px 0; font-family: system-ui, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); max-width: 680px;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 12px;">
            <div>
                <h4 style="margin: 0; color: #0f172a; font-size: 16px;">
                    📝 实验报告综合评阅卡: {evaluation['experiment_name']}
                </h4>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 12px;">
                    综合评定评分（35% 数据真值 + 65% 质性工程洞察）
                </p>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 26px; font-weight: 800; color: {color};">{tot:.1f}</span>
                <span style="font-size: 12px; color: #64748b;">/ 100</span>
            </div>
        </div>

        <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 14px;">
            <thead>
                <tr style="background: #f8fafc; color: #475569; border-bottom: 1px solid #e2e8f0; text-align: left;">
                    <th style="padding: 6px 12px;">评价维度</th>
                    <th style="padding: 6px 12px;">得分</th>
                    <th style="padding: 6px 12px;">达成度</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>

        <div style="background: #f8fafc; border-left: 4px solid #3b82f6; padding: 10px 14px; border-radius: 4px;">
            <strong style="color: #1e40af; font-size: 12px; text-transform: uppercase;">智能评语草稿 (Teacher Feedback Draft):</strong>
            <p style="margin: 4px 0 0 0; font-size: 13px; color: #334155; line-height: 1.5;">
                {evaluation['teacher_feedback_draft']}
            </p>
        </div>
    </div>
    """
    return html
