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
"""
import os
import statistics as _stats

# [健壮性优化 - 2026-10-25 给 Muse 说明]：
# 增加包内相对导入回退机制，确保无论从 labs 外部还是 common 模块内部引用，均能正确解析 evaluator。
try:
    from common.evaluator import GRADING_SPECS, grade_metrics
except ImportError:
    from .evaluator import GRADING_SPECS, grade_metrics

CHART_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results',
                         'charts')


def build_grade_table(all_results):
    """all_results: {username: {exp_id: metrics}} -> 得分表

    Returns: {username: {exp_id: score, ..., 'total': 平均分}}
    """
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
        row['total'] = round(sum(scores) / len(scores), 1) if scores else 0.0
        row['n_done'] = len(scores)
        table[user] = row
    return table


def statistics(table):
    """全班统计。table为build_grade_table的输出。"""
    if not table:
        return {'n_students': 0}
    totals = [r['total'] for r in table.values() if r.get('n_done')]
    per_exp = {}
    for exp_id in GRADING_SPECS:
        vals = [r[exp_id] for r in table.values() if exp_id in r]
        if vals:
            per_exp[exp_id] = {
                'mean': round(_stats.mean(vals), 1),
                'n': len(vals),
                'pass_rate': round(
                    sum(1 for v in vals if v >= 60) / len(vals) * 100, 1),
            }
    return {
        'n_students': len(table),
        'n_submitted': len(totals),
        'mean': round(_stats.mean(totals), 1) if totals else 0.0,
        'median': round(_stats.median(totals), 1) if totals else 0.0,
        'stdev': round(_stats.pstdev(totals), 1) if len(totals) > 1 else 0.0,
        'pass_rate': round(
            sum(1 for v in totals if v >= 60) / len(totals) * 100, 1) if totals else 0.0,
        'max': max(totals) if totals else 0.0,
        'min': min(totals) if totals else 0.0,
        'per_experiment': per_exp,
    }


def _ensure_chart_dir():
    os.makedirs(CHART_DIR, exist_ok=True)
    return CHART_DIR


def chart_distribution(table, filename='score_distribution.png'):
    """分数分布直方图。"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    totals = [r['total'] for r in table.values() if r.get('n_done')]
    if not totals:
        return None
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(totals, bins=[0, 20, 40, 60, 70, 80, 90, 100],
            color='#42A5F5', edgecolor='white')
    ax.axvline(60, color='#F44336', ls='--', lw=1.5, label='Pass line (60)')
    ax.set_xlabel('Average score')
    ax.set_ylabel('Number of students')
    ax.set_title('Score Distribution')
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
    fig, ax = plt.subplots(figsize=(10, 4))
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
    rows = [(u, r['total']) for u, r in table.items() if r.get('n_done')]
    if not rows:
        return None
    rows.sort(key=lambda x: x[1])
    rows = rows[-20:]
    fig, ax = plt.subplots(figsize=(8, max(3, len(rows) * 0.4)))
    ax.barh([u for u, _ in rows], [s for _, s in rows],
            color='#42A5F5', edgecolor='white')
    ax.set_xlabel('Average score')
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
    with open(path) as f:
        return json.load(f)
