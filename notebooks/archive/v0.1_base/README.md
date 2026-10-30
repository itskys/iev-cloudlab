# IEV CloudLab V0.1 原始原型实验归档库 (Archived Base Prototypes)

> **归档时间**：2026-10-30  
> **归档说明**：本目录收录 IEV CloudLab 平台立项与早期的 29 个初代原型 Notebook（编号 A1–H2）。  
> **当前状态**：仅作教学历史回顾、基础算法基线比对与轻量原型参考。

---

## 为什么升级为 V1.0 (Pro)？

相较于 V0.1 原型，**V1.0 官方标准实验 (Pro版)** 实现了全方位的科研与工程教学跃升：
1. **六步进阶导学体系**：从第一性原理数理推导、算法控制核编写、高保真闭环仿真、3D 数字孪生回放、参数敏度探索，到自动化多维评分考核；
2. **工业级高保真工具链集成**：无缝驱动真实 SUMO TraCI、FASTSim Rust 内核、PyBaMM 电化学 DFN/SPM 模型、FMPy FMI 2.0 联合仿真与 ROS 2 通信中间件，彻底淘汰了玩具级虚拟数据；
3. **数据链闭环与时光机快照**：支持自动化评分（`evaluator.py`）、学生时光机代码快照（`snapshot_manager.py`）与班级天梯挑战（`leaderboard.py`）。

---

## 归档实验清单 (29 个)

- **模块 A · 智驾场景与控制**：A1_cutin_aeb, A2_acc_follow, A3_aeb_closedloop, A4_intersection_yield, A5_merge_kinematic_demo
- **模块 B · 交通流与网联协同**：B1_idm_calibration, B2_traffic_signal, B3_sumo_cacc, B4_congestion_wave, B5_green_wave
- **模块 C · 电动汽车能耗仿真**：C1_fastsim_energy, C2_vehicle_comparison, C3_sensitivity_analysis, C4_ems_comparison
- **模块 D · 动力电池电化学机理**：D1_pybamm_battery, D2_rate_capacity, D3_ocv_soc_export, D4_lithium_plating
- **模块 E · 优化与模型预测控制**：E1_single_objective, E2_pymoo_multiobj, E3_mpc_follow, E4_dp_ems
- **模块 F · FMI/FMU 协同仿真**：F1_fmu_load, F2_openmodelica_fmu, F3_multi_fmu
- **模块 G · ROS 2 软件中间件**：G1_ros_topics, G2_ros_services
- **模块 H · 场景生成与模糊测试**：H1_batch_generation, H2_scenario_fuzzing

> 💡 **使用建议**：如需运行正式实验，请返回 `notebooks/` 根目录打开对应的 `*_pro.ipynb`。
