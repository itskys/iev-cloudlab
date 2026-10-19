# IEV CloudLab 实验手册

## 实验排序（共29个）

按模块循序渐进，建议按以下顺序学习：

### A. 自动驾驶场景测试（esmini）
| 编号 | 实验 | 难度 | 前置 |
|---|---|---|---|
| A1 | Cut-in加塞避险 | 中 | — |
| A2 | ACC跟车距离与舒适性 | 初 | A1 |
| A3 | AEB紧急制动Python闭环 | 高 | A1 |
| A4 | 交叉口让行LTAP-OD | 中 | A1 |
| A5 | 变道/汇流间隙评估（纯运动学演示） | 初 | — |

### B. 交通流与协同（SUMO）
| 编号 | 实验 | 难度 | 前置 |
|---|---|---|---|
| B1 | IDM跟车模型参数标定 | 初 | — |
| B2 | 信号灯配时优化 | 中 | B1 |
| B3 | CACC编队协同巡航 | 高 | B1 |
| B4 | 拥堵传播分析 | 初 | — |
| B5 | 干线绿波协调 | 中 | B2 |

### C. 整车能量（FASTSim）
| 编号 | 实验 | 难度 | 前置 | 内核 |
|---|---|---|---|---|
| C1 | UDDS百公里电耗 | 初 | — | py310-fastsim |
| C2 | 车型横向对比 | 初 | C1 | py310-fastsim |
| C3 | 载重/风阻灵敏度 | 中 | C1 | py310-fastsim |
| C4 | 能量管理策略对比 | 高 | C1 | py310-fastsim |

### D. 电池（PyBaMM）
| 编号 | 实验 | 难度 | 前置 |
|---|---|---|---|
| D1 | 恒流充放电曲线 | 初 | — |
| D2 | 倍率-容量衰减 | 中 | D1 |
| D3 | OCV-SOC标定导出→FASTSim | 中 | D1 |
| D4 | 快充析锂风险 | 高 | D1 |

### E. 优化与控制
| 编号 | 实验 | 难度 | 前置 | 内核 |
|---|---|---|---|---|
| E1 | 单目标参数优化入门 | 初 | — | py310-fastsim |
| E2 | 多目标权衡 | 中 | E1 | py310-fastsim |
| E3 | MPC跟车控制→esmini闭环 | 高 | A2+E1 | 默认 |
| E4 | 能量管理动态规划→FASTSim | 高 | C4+E1 | py310-fastsim |

### F. 模型交换（FMI）
| 编号 | 实验 | 难度 | 前置 |
|---|---|---|---|
| F1 | FMU加载与CS仿真 | 初 | — |
| F2 | OpenModelica建模→FMU→FMPy | 中 | F1 |
| F3 | 多FMU协仿真 | 高 | F2 |

### G. ROS 2基础
| 编号 | 实验 | 难度 | 前置 |
|---|---|---|---|
| G1 | 话题发布/订阅 | 初 | — |
| G2 | 服务调用与参数 | 初 | G1 |

### H. 场景生成
| 编号 | 实验 | 难度 | 前置 |
|---|---|---|---|
| H1 | 参数化场景批量生成→esmini批量跑 | 中 | A1 |
| H2 | 场景变异+通过判据 | 高 | H1 |

## 三条链（数据协同）

### 链1：车型设计链 D → C → A
```
D3 (PyBaMM标定)
  → labs/data/batteries/*.csv (OCV-SOC曲线)
  → [BatteryFASTSimAdapter]
C1/C2 (FASTSim整车)
  → labs/data/vehicles/*.yaml (整车参数)
  → [vehicle_library.load_vehicle()]
A1/A2/A3 (esmini场景)
```

### 链2：算法开发链 Controller → 闭环 → 指标
```
labs/common/controller.py (BaseController)
  → labs/scenarios/A_esmini/* 或 B_sumo/*
  → EsminiEnv.step() / TraCI (闭环)
  → labs/data/results/*.json (指标存档)
```

### 链3：能量管理链 E → C → 成绩单
```
E2/E4 (pymoo/DP优化)
  → 最优参数
  → C4 (FASTSim验证)
  → labs/data/results/ (成绩单)
```

## 数据文件位置

```
labs/
├── common/           # 共享Python库
│   └── vehicle_library.py  # 数据协同接口
├── scenarios/        # 标准化场景定义
│   ├── A_esmini/A1_cutin/   # cutin.xosc + cutin.xodr
│   ├── A_esmini/A3_aeb/
│   ├── A_esmini/A4_intersection/
│   └── ...
└── data/             # 协同数据
    ├── vehicles/     # bev_sedan.yaml, bev_suv.yaml
    ├── batteries/    # ncm622_50ah.csv, chen2020_nmc_75ah.csv
    └── results/      # 各实验输出的JSON
```

## 内核说明

- 默认Python 3.12：A/B/D/F/G/H模块
- `py310-fastsim`：C/E模块（FASTSim 2.1.5 + pymoo 0.6.2）
- 在JupyterLab右上角切换内核

## 诚实声明

- A1/A2/A3/A4：Target车辆在esmini ctypes模式下冻结（等价静态障碍物），Ego为Python运动学闭环。详见各notebook顶部的"架构诚实声明"。
- A5：纯Python运动学演示，未调用esmini引擎（标题已注明）。
- C2：FASTSim 2.1.5车辆库部分车型解析异常（已在排错表中说明）。
- F2：OpenModelica不在容器内（GPL），用手写FMU等效演示。
