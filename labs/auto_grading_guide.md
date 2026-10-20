# 自动评分模块说明 | Auto-Grading

## 位置
`labs/common/evaluator.py`

## 学生自查（在notebook末尾运行）
```python
from common.evaluator import grade_metrics
score = grade_metrics('C1_fastsim_energy', {'energy_kwh_100km': 12.5})
print(score['score'], '分')  # 100.0
```

## 教师批改
```bash
# 评单个实验的结果文件
python -m common.evaluator C1_fastsim_energy

# 批量评所有已有结果（生成Markdown成绩单）
python -m common.evaluator --all

# 执行学生notebook后评分（带超时看门狗）
python -m common.evaluator /path/to/student_notebook.ipynb
```

## 评分构成（百分制）
| 维度 | 分数 | 说明 |
|---|---|---|
| 指标达标 | 70 | 按判据权重，阈值为真实引擎实测值 |
| 结果完整性 | 20 | 结果文件存在且非空 |
| 执行成功 | 10 | notebook无报错跑完（执行模式下） |

60分及格。判据覆盖29/29实验。

## 原理
1. 学生运行实验 → `save_result()` 存指标到 `labs/data/results/<实验>.json`
2. 评分器读结果 → 按 `GRADING_SPECS` 判据逐项核对 → 出分+未达标项清单
3. 键名不统一由 `METRIC_ALIASES` 翻译层处理

## 防作弊设计
- B3判据含 `steps≥300`：防止"车辆没生成、0步假通过"（曾真实发生）
- 执行模式带超时（默认300s，仿真类600s）：防死循环卡死评分
- 阈值均有余量（如B3实测1.09m、判据2.0m）：正常波动不误判，作弊/未做必现形

## 局限（诚实声明）
- 当前为**结果文件评分**：依赖notebook调用`save_result`。未存结果的实验评0分并提示"先运行实验"
- 尚未接入JupyterHub API（成绩自动回传/排行榜属Stage 3）；现阶段教师手动跑CLI出成绩单
