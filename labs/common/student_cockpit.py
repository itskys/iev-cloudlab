"""IEV CloudLab 学生个人学习画像与自主诊断驾驶舱 | Student Cockpit

功能说明：
  为学生提供专属的自主学习自检看板，实现从“被动等待老师批改”到“自主目标驱动提升”的转变。

核心功能：
  1. 个人全课程 29 门实验进度与综合总评自动核算；
  2. 7 大工程能力维度雷达图实时绘制 (render_student_radar_svg)；
  3. 智能进阶推荐引擎 (Next-Step Recommendations)：
     - 识别当前尚未开展或得分偏低的能力维度，推荐优先突破实验；
  4. 实验报告提交前预审自检器 (pre_submit_report_check)：
     - 学生在将报告交给老师之前，一键运行自检，避免抄错数字或格式不合规被扣分。
"""

import json
import os
from typing import Dict, Any, List, Optional

try:
    from common.evaluator import GRADING_SPECS, grade_metrics
    from common.skills_profiler import compute_student_skill_profile, render_student_radar_svg, SKILL_DIMENSIONS
    from common.report_evaluator import evaluate_report_comprehensively, render_report_evaluation_card
    from common.report_checker import check_student_directory
except ImportError:
    try:
        from .evaluator import GRADING_SPECS, grade_metrics
        from .skills_profiler import compute_student_skill_profile, render_student_radar_svg, SKILL_DIMENSIONS
        from .report_evaluator import evaluate_report_comprehensively, render_report_evaluation_card
        from .report_checker import check_student_directory
    except ImportError:
        try:
            from evaluator import GRADING_SPECS, grade_metrics
            from skills_profiler import compute_student_skill_profile, render_student_radar_svg, SKILL_DIMENSIONS
            from report_evaluator import evaluate_report_comprehensively, render_report_evaluation_card
            from report_checker import check_student_directory
        except ImportError:
            GRADING_SPECS = {}
            SKILL_DIMENSIONS = {}
            compute_student_skill_profile = None
            render_student_radar_svg = None


def scan_personal_results(results_dir: Optional[str] = None) -> Dict[str, Any]:
    """扫描学生本地 labs/data/results/ 下所有已完成的实验结果并评分。"""
    if results_dir is None:
        results_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')

    personal_scores = {}
    if not os.path.exists(results_dir):
        return personal_scores

    for fname in os.listdir(results_dir):
        if not fname.endswith('.json') or fname.startswith('test_'):
            continue
        exp_id = fname[:-5]
        # 兼容 export 命名
        canonical_exp = exp_id
        if canonical_exp not in GRADING_SPECS and f"{canonical_exp}_export" in GRADING_SPECS:
            canonical_exp = f"{canonical_exp}_export"

        fpath = os.path.join(results_dir, fname)
        try:
            with open(fpath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            metrics = data.get('metrics', data)
            if canonical_exp in GRADING_SPECS:
                graded = grade_metrics(canonical_exp, metrics)
                personal_scores[canonical_exp] = graded['score']
        except Exception:
            continue

    return personal_scores


def get_student_study_progress(results_dir: Optional[str] = None) -> Dict[str, Any]:
    """生成学生个人全方位的学习进度与能力发展统计。"""
    scores = scan_personal_results(results_dir)
    n_required = len(GRADING_SPECS) if GRADING_SPECS else 29
    n_done = len(scores)

    sum_scores = sum(scores.values())
    fair_total = round(sum_scores / n_required, 1) if n_required > 0 else 0.0
    submitted_avg = round(sum_scores / n_done, 1) if n_done > 0 else 0.0
    comp_rate = round((n_done / n_required) * 100.0, 1) if n_required > 0 else 0.0

    skill_profile = compute_student_skill_profile(scores)

    # 智能攻坚建议 (找完成度低或均分低的能力)
    recommendations = []
    for dim_k, dim_data in sorted(skill_profile['dimensions'].items(), key=lambda x: x[1]['score']):
        if dim_data['completion_pct'] < 100.0:
            uncompleted = [e for e, s in dim_data['exps'].items() if s is None]
            if uncompleted:
                recommendations.append({
                    'dimension_name': dim_data['name'],
                    'color': dim_data['color'],
                    'current_score': dim_data['score'],
                    'completion_pct': dim_data['completion_pct'],
                    'suggested_exps': uncompleted[:2],
                    'desc': dim_data['desc'],
                })

    return {
        'n_done': n_done,
        'n_required': n_required,
        'completion_rate': comp_rate,
        'fair_total_score': fair_total,
        'submitted_avg_score': submitted_avg,
        'skill_profile': skill_profile,
        'recommendations': recommendations[:3],  # 推荐前 3 个薄弱维度
        'scores': scores,
    }


def render_student_cockpit_html(progress: Dict[str, Any], student_name: str = "同学") -> str:
    """生成高保真个人学习仪表盘看板 (HTML)"""
    n_done = progress['n_done']
    n_req = progress['n_required']
    rate = progress['completion_rate']
    total_score = progress['fair_total_score']
    sub_avg = progress['submitted_avg_score']
    p = progress['skill_profile']

    radar_svg = render_student_radar_svg(p, student_name=student_name, width=480, height=360)

    # 推荐列表 HTML
    rec_items = ""
    for r in progress['recommendations']:
        exps_badges = " ".join(
            f'<code style="background: #e0e7ff; color: #3730a3; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{e}</code>'
            for e in r['suggested_exps']
        )
        rec_items += f"""
        <div style="background: #f8fafc; border-left: 4px solid {r['color']}; padding: 10px 14px; border-radius: 6px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <strong style="color: #0f172a; font-size: 13px;">{r['dimension_name']}</strong>
                <span style="font-size: 11px; color: #64748b;">当前达成: {r['completion_pct']:.0f}% (均分 {r['current_score']:.1f})</span>
            </div>
            <p style="margin: 4px 0 6px 0; font-size: 12px; color: #475569;">推荐优先挑战: {exps_badges}</p>
            <p style="margin: 0; font-size: 11px; color: #94a3b8;">{r['desc']}</p>
        </div>
        """

    html = f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 14px; margin-bottom: 16px;">
            <div>
                <h3 style="margin: 0; color: #0f172a; font-size: 18px; font-weight: 700;">
                    🚀 {student_name} 的个人工程能力画像与学习自检驾驶舱
                </h3>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">
                    数据驱动闭环，实时观测自身 7 大核心工程能力演进轨迹
                </p>
            </div>
            <div style="display: flex; gap: 14px; text-align: center;">
                <div style="background: #f8fafc; padding: 6px 14px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">已完成实验</div>
                    <div style="font-size: 18px; font-weight: 700; color: #2563eb;">{n_done} <span style="font-size: 12px; color: #94a3b8;">/ {n_req}</span></div>
                </div>
                <div style="background: #f8fafc; padding: 6px 14px; border-radius: 8px; border: 1px solid #e2e8f0;">
                    <div style="font-size: 11px; color: #64748b; font-weight: 600;">课程总评成绩</div>
                    <div style="font-size: 18px; font-weight: 700; color: #10b981;">{total_score:.1f} <span style="font-size: 12px; color: #94a3b8;">分</span></div>
                </div>
            </div>
        </div>

        <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: flex-start;">
            <div style="flex: 1 1 450px;">
                {radar_svg}
            </div>
            <div style="flex: 1 1 300px;">
                <h4 style="margin: 0 0 10px 0; color: #0f172a; font-size: 14px; font-weight: 600;">
                    🎯 智能攻坚建议 (Personalized Action Plan)
                </h4>
                {rec_items if rec_items else '<p style="color: #10b981; font-weight: 600;">恭喜！您已圆满完成全课程所有维度的实验挑战！</p>'}
            </div>
        </div>
    </div>
    """
    return html


def pre_submit_report_check(report_md_path: str, exp_id: Optional[str] = None):
    """供学生在 Notebook 中运行的一键报告预检与评阅自测工具"""
    from IPython.display import HTML, display

    if not os.path.exists(report_md_path):
        print(f"❌ 未找到报告文件: {report_md_path}")
        return

    with open(report_md_path, 'r', encoding='utf-8') as f:
        md_text = f.read()

    results_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
    if exp_id is None:
        # 自动推导
        for k in GRADING_SPECS.keys():
            if k.lower() in report_md_path.lower() or k.lower() in md_text.lower():
                exp_id = k
                break

    if not exp_id:
        print("⚠️ 未能从文件名或内容推导出目标实验编号，请手动传入 exp_id='A1_cutin_aeb'")
        return

    json_path = os.path.join(results_dir, f"{exp_id}.json")
    if not os.path.exists(json_path):
        json_path = os.path.join(results_dir, f"{exp_id}_export.json")

    eval_result = evaluate_report_comprehensively(md_text, json_path, exp_id)
    display(HTML(render_report_evaluation_card(eval_result)))
