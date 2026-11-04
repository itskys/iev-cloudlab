# 自动评分模块说明 | Auto-Grading

## 位置
`labs/common/evaluator.py`

## 学生自查与智能伴学诊断（在notebook末尾运行）
```python
from common.evaluator import grade_metrics, display_grade_card

# 1. 评分并自动触发机理失效诊断 (未达标时自动注入 diagnosis 与 diagnosis_html)
grade_res = grade_metrics('A1_cutin_aeb', {'collision': True, 'min_ttc_s': 0.8})
print(grade_res['score'], '分, 通过:', grade_res['passed'])

# 2. 以高保真工控卡片形式渲染成绩，并在下方联动弹出机理归因与调参处方矩阵
display_grade_card(grade_res)
```

## 教师批改与课堂大屏演示
```bash
# 评单个实验的结果文件
python -m common.evaluator C1_fastsim_energy

# 批量评所有已有结果（生成Markdown成绩单）
python -m common.evaluator --all

# 执行学生notebook后评分（带超时看门狗）
python -m common.evaluator /path/to/student_notebook.ipynb
```

```python
# 教师端启动投屏互动演示大屏与同屏对标视窗
from common.teacher_dashboard import show_teacher_presentation
show_teacher_presentation()
```

## 评分体系与 29+1 课程架构

平台采用 **29 门 V1.0 官方标准平时实验 + 1 项 Capstone 跨域综合大作业** 的双轨评分标准：
- **29 门平时实验（A1~H2）**：覆盖自动驾驶、交通流、整车能耗、电池、优化、中间件等核心模块，总评基准分母锁定 29 门（`REQUIRED_EXP_COUNT=29`），缺交记 0 分。
- **1 项 Capstone 期末大作业**：全域闭环多物理场集成验证，独立给出 Capstone 得分并直接挂钩第 16 周期末大作业考核（25% 权重）。

| 维度 | 分数 | 说明 |
|---|---|---|
| 指标达标 | 70 | 按判据权重，阈值为真实引擎实测物理真值 |
| 结果完整性 | 20 | 结果文件存在且非空 |
| 执行成功 | 10 | notebook无报错跑完（执行模式下） |

60分及格。判据覆盖 29 门标准实验与 1 项 Capstone 闭环。

## 自动化评测与师生协同流水线

1. **学生运行实验**：
   - 学生在 `notebooks/*_pro.ipynb` 中运行实验，末尾调用 `save_result(exp_id, metrics)`；
   - 结果原子写入 `/home/jovyan/labs/data/results/<exp_id>.json`，并在后台触发本地快照。
2. **全自动成绩收集与统计 (零手动干预)**：
   - 宿主机后台 Cron 定时任务每小时自动触发 `deploy/collect_grades.py`；
   - 扫描所有学生 Home 目录下的 `labs/data/results/*.json`，原子聚合至教师端 `grades/all_results.json`；
   - 教师打开 `teacher/dashboard.ipynb`（教师面板）即可一键查看全班成绩分布图、每实验均分、及格率与名册排位。
3. **学术诚信与智能防作弊**：
   - **AST 查重引擎**：自动加载官方母版指纹差分过滤，排除模板自带代码与纯标量参数微调，精准比对学生自主编写代码的 3-Gram Jaccard 相似度；
   - **报告数值一致性校验**：自动比对学生报告中的数据与底层 `results/*.json`，偏差 >5% 即高亮预警；
   - **B3 步数判据**：含 `steps≥300`，彻底阻断 0 步空跑假通过漏洞。
4. **全体系智能机理故障归因与调优导师 (Diagnostic Tutor)**：
   - 在 `grade_metrics()` 中无缝联动，实验未通过或数值异常时自动调用 `diagnose_experiment()`；
   - 覆盖全部 29 门实验 + Capstone，输出第一性原理物理因果剖析、结构化可执行调参矩阵与主机厂工程对标规范。
5. **教师课堂实时演示大屏与同屏对标视窗 (`teacher_dashboard.py`)**：
   - 教师端支持一键调用 `show_teacher_presentation()`；
   - 提供全班 KPI 态势、Top 5 机理失效排行榜、A1/B3/C1/D4/E3 标杆解 vs 翻车解同屏动态对标与复盘讲义导出。
