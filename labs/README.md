# IEV CloudLab Labs 目录结构

## 布局

```
labs/
├── common/              # 共享Python库
│   ├── controller.py    # BaseController基类
│   ├── esmini_env.py    # esmini闭环环境
│   ├── battery_adapter.py  # PyBaMM→FASTSim电池适配器
│   ├── fastsim_helper.py   # FASTSim辅助函数
│   └── vehicle_library.py  # NEW: 车辆/电池/结果库（打通三链）
├── scenarios/           # NEW: 标准化场景定义（与实验分离）
│   ├── A_esmini/        # esmini场景
│   │   ├── A1_cutin/    # cutin.xosc + cutin.xodr + scenario.yaml
│   │   ├── A2_follow/
│   │   └── A5_merge/
│   ├── B_sumo/          # SUMO场景
│   ├── C_fastsim/       # FASTSim车辆配置
│   ├── D_pybamm/        # PyBaMM电池配置
│   ├── E_opt/           # 优化问题定义
│   ├── F_fmu/           # FMU模型
│   ├── G_ros/           # ROS2配置
│   └── H_scengen/       # 场景生成器
└── data/                # NEW: 可串联的数据
    ├── vehicles/        # 车辆参数库（C输出→A输入）
    ├── batteries/       # 电池OCV-SOC库（D输出→C输入）
    └── results/         # 实验结果（上游→下游）
```

## 三条链的数据流

### 链1：车型设计链 D → C → A
```
D1 (PyBaMM仿真)
  → labs/data/batteries/ncm622_50ah.csv
  → [BatteryFASTSimAdapter]
C1 (FASTSim整车仿真)
  → labs/data/vehicles/bev_sedan.yaml
  → [vehicle_library.load_vehicle()]
A1/A2 (esmini闭环)
```

### 链2：算法开发链 Controller → 闭环 → 指标
```
common/controller.py (BaseController)
  → labs/scenarios/A_esmini/* (场景)
  → EsminiEnv.step() (闭环)
  → labs/data/results/A1_cutin_aeb.json (指标)
```

### 链3：能量管理链 E → C → 成绩单
```
E2 (pymoo多目标优化)
  → 最优参数
  → C1 (FASTSim验证)
  → labs/data/results/ (成绩单)
```

## 实验Notebook位置

`notebooks/` 下的教学实验引用 `labs/scenarios/` 和 `labs/data/`，
不要在notebook里hardcode场景路径。
