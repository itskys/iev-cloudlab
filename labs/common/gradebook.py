"""IEV CloudLab 成绩册 | Gradebook: 汇总 + 统计 + 可视化

数据来源：
  - 主机端汇总文件 grades/all_results.json（由 deploy/collect_grades.py
    扫描各学生home的 labs/data/results/*.json 生成）
  - 或直接传入 {username: {experiment_id: metrics}} 结构

输出：
  - grade_table(): 每生每实验得分表（调用evaluator判据）
  - statistics(): 全班统计（均分/中位数/及格率/每实验均分）
  - 图表（matplotlib英文标签）：分数分布直方图、每实验平均分柱状图、
    学生总分排名图，保存为PNG并返回路径

[公平性重构 - 2026-10-28 采纳 Muse 评审意见]：
  - 核心缺陷修复：原逻辑为 `sum(scores)/len(scores)`（只算已提交实验），导致挑做 3 门得 100 分者高居榜首、勤奋做 20 门得 85 分者排名垫底。
  - 新评分口径：全课程以 29 门必做实验为基准（`REQUIRED_EXP_COUNT = len(GRADING_SPECS)`）。
    * `total`: 综合总评成绩 = `sum(scores) / 29`（缺交实验按 0 分计入）
    * `submitted_avg`: 已提交实验均分 = `sum(scores) / n_done`
    * `n_done`: 已完成实验门数
    * `completion_rate`: 课程完成率 (%) = `n_done / 29 * 100`
"""
import os
import statistics as _stats

try:
    from common.evaluator import GRADING_SPECS, grade_metrics
except ImportError:
    from .evaluator import GRADING_SPECS, grade_metrics

CHART_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results', 'charts')
REQUIRED_EXP_COUNT = len(GRADING_SPECS)  # 29 门必做实验基准


def build_grade_table(all_results, required_count=None):
    """all_results: {username: {exp_id: metrics}} -> 得分表

    Returns: {
      username: {
        exp_id: score,
        ...,
        'total': 综合总评得分 (缺交记 0 分，按全量 29 门折算),
        'submitted_avg': 已提交实验均分,
        'n_done': 完成门数,
        'n_required': 必做总门数 (29),
        'completion_rate': 完成率 (%)
      }
    }
    """
    if required_count is None:
        required_count = REQUIRED_EXP_COUNT if REQUIRED_EXP_COUNT > 0 else 29

    table = {}
    for user, exps in all_results.items():
        row = {}
        scores = []
        for exp_id, metrics in exps.items():
            if exp_id not in GRADING_SPECS:
                continue
            r = grade_metrics(exp_id, metrics)
            row[exp_id] = r['score']
            scores.append(r['score'])

        n_done = len(scores)
        sum_scores = sum(scores)

        # 公平总评：未做实验按 0 分计入全课程 29 门基准分母
        total_score = round(sum_scores / required_count, 1)
        sub_avg = round(sum_scores / n_done, 1) if n_done > 0 else 0.0
        comp_rate = round((n_done / required_count) * 100.0, 1)

        row['total'] = total_score
        row['submitted_avg'] = sub_avg
        row['n_done'] = n_done
        row['n_required'] = required_count
        row['completion_rate'] = comp_rate

        table[user] = row
    return table


def statistics(table):
    """全班统计。table为build_grade_table的输出。"""
    if not table:
        return {'n_students': 0}

    totals = [r['total'] for r in table.values()]
    sub_avgs = [r['submitted_avg'] for r in table.values() if r.get('n_done', 0) > 0]
    comp_rates = [r['completion_rate'] for r in table.values()]
    submitted_students = [r for r in table.values() if r.get('n_done', 0) > 0]

    per_exp = {}
    for exp_id in GRADING_SPECS:
        vals = [r[exp_id] for r in table.values() if exp_id in r]
        if vals:
            per_exp[exp_id] = {
                'mean': round(_stats.mean(vals), 1),
                'n': len(vals),
                'pass_rate': round(sum(1 for v in vals if v >= 60) / len(vals) * 100, 1),
            }

    return {
        'n_students': len(table),
        'n_submitted': len(submitted_students),
        'mean': round(_stats.mean(totals), 1) if totals else 0.0,
        'submitted_mean': round(_stats.mean(sub_avgs), 1) if sub_avgs else 0.0,
        'mean_completion_rate': round(_stats.mean(comp_rates), 1) if comp_rates else 0.0,
        'median': round(_stats.median(totals), 1) if totals else 0.0,
        'stdev': round(_stats.pstdev(totals), 1) if len(totals) > 1 else 0.0,
        'pass_rate': round(sum(1 for v in totals if v >= 60) / len(totals) * 100, 1) if totals else 0.0,
        'max': max(totals) if totals else 0.0,
        'min': min(totals) if totals else 0.0,
        'per_experiment': per_exp,
    }


def _ensure_chart_dir():
    os.makedirs(CHART_DIR, exist_ok=True)
    return CHART_DIR


def chart_distribution(table, filename='score_distribution.png'):
    """分数分布直方图（按总评成绩统计）。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    totals = [r['total'] for r in table.values()]
    if not totals:
        return None

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(totals, bins=[0, 20, 40, 60, 70, 80, 90, 100],
            color='#42A5F5', edgecolor='white')
    ax.axvline(60, color='#F44336', ls='--', lw=1.5, label='Pass line (60)')
    ax.set_xlabel('Course Aggregate Score (Based on 29 Labs)')
    ax.set_ylabel('Number of students')
    ax.set_title('Course Grade Distribution (Fair 29-Lab Benchmark)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    path = os.path.join(_ensure_chart_dir(), filename)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def chart_per_experiment(stats, filename='per_experiment.png'):
    """每实验平均分柱状图（按均分排序，高亮<60的实验）。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    per = stats.get('per_experiment', {})
    if not per:
        return None

    items = sorted(per.items(), key=lambda kv: kv[1]['mean'])
    names = [k.split('_')[0] for k, _ in items]
    means = [v['mean'] for _, v in items]
    colors = ['#F44336' if m < 60 else '#66BB6A' for m in means]

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.bar(names, means, color=colors, edgecolor='white')
    ax.axhline(60, color='#F44336', ls='--', lw=1)
    ax.set_ylabel('Mean score')
    ax.set_title('Mean Score by Experiment (red: below pass line)')
    ax.set_ylim(0, 100)
    ax.grid(True, axis='y', alpha=0.3)
    path = os.path.join(_ensure_chart_dir(), filename)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def chart_ranking(table, filename='student_ranking.png'):
    """学生总分排名图（前20名）。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    rows = [(u, r['total']) for u, r in table.items()]
    if not rows:
        return None

    rows.sort(key=lambda x: x[1])
    rows = rows[-20:]

    fig, ax = plt.subplots(figsize=(8, max(3, len(rows) * 0.4)))
    ax.barh([u for u, _ in rows], [s for _, s in rows],
            color='#42A5F5', edgecolor='white')
    ax.set_xlabel('Course Aggregate Score (Based on 29 Labs)')
    ax.set_title('Student Ranking (Top 20)')
    ax.set_xlim(0, 100)
    ax.grid(True, axis='x', alpha=0.3)
    path = os.path.join(_ensure_chart_dir(), filename)
    fig.savefig(path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return path


def load_collected(path):
    """加载主机端汇总的 all_results.json。"""
    import json
    with open(path, encoding='utf-8') as f:
        return json.load(f)
