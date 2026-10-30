#!/usr/bin/env python3
"""
IEV CloudLab 实验版本归档与标准版标记工具
1. 将 29 个 V0.1 Base 原型 Notebook 标记归档横幅并移至 notebooks/archive/v0.1_base/
2. 在 30 个 Pro Notebook 中注入 IEV CloudLab V1.0 官方标准实验权威徽标
3. 归档 labs/ad2026 至 labs/archive/legacy_ad2026/
"""

import os
import glob
import json
import shutil

REPO_DIR = "/Users/christingking/dev/iev-cloudlab"
NB_DIR = os.path.join(REPO_DIR, "notebooks")
ARCHIVE_BASE_DIR = os.path.join(NB_DIR, "archive", "v0.1_base")
os.makedirs(ARCHIVE_BASE_DIR, exist_ok=True)

# 1. 归档 29 个 Base Notebook
base_files = sorted(glob.glob(os.path.join(NB_DIR, "[A-H][1-5]_*.ipynb")))
base_non_pro = [f for f in base_files if not f.endswith("_pro.ipynb")]

banner_base = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "> ⚠️ **历史版本归档 (Archived V0.1)**: 本实验为 IEV CloudLab V0.1 原始原型版本，仅供历史技术对照与教学基线参考。\n",
        "> 🌟 **正式教学与考核**：请统一使用根目录下对应的 **IEV CloudLab V1.0 官方标准实验 (`*_pro.ipynb`)**。\n"
    ]
}

print(f"--- 步骤 1: 归档 {len(base_non_pro)} 个 Base Notebook 到 {ARCHIVE_BASE_DIR} ---")
for fpath in base_non_pro:
    fname = os.path.basename(fpath)
    with open(fpath, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    
    first_src = "".join(nb_data["cells"][0].get("source", [])) if nb_data.get("cells") else ""
    if "历史版本归档 (Archived V0.1)" not in first_src:
        nb_data["cells"].insert(0, banner_base)
    
    dst_path = os.path.join(ARCHIVE_BASE_DIR, fname)
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, ensure_ascii=False, indent=1)
    
    os.remove(fpath)
    print(f"  [V0.1 归档成功] {fname}")

# 2. 生成 v0.1_base/README.md
readme_content = """# IEV CloudLab V0.1 原始原型实验归档库 (Archived Base Prototypes)

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
"""

with open(os.path.join(ARCHIVE_BASE_DIR, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme_content)
print(f"  [README 生成] {os.path.join(ARCHIVE_BASE_DIR, 'README.md')}")

# 3. 标记 30 个 Pro Notebook 为 V1.0 官方标准实验
pro_files = sorted(glob.glob(os.path.join(NB_DIR, "*_pro.ipynb")))
print(f"\n--- 步骤 2: 为 {len(pro_files)} 个 Pro Notebook 注入 V1.0 官方标准认证徽章 ---")

badge_text = "> 🌟 **版本认证**：**IEV CloudLab V1.0 官方标准实验 (Official Standard Lab)**\n"

for ppath in pro_files:
    pname = os.path.basename(ppath)
    with open(ppath, "r", encoding="utf-8") as f:
        nb_data = json.load(f)
    
    cells = nb_data.get("cells", [])
    if not cells:
        continue
    
    first_cell = cells[0]
    if first_cell.get("cell_type") == "markdown":
        src = first_cell.get("source", [])
        combined = "".join(src)
        if "IEV CloudLab V1.0 官方标准实验" not in combined:
            # 找到首个标题行，在其下方插入徽章
            new_src = []
            inserted = False
            for line in src:
                new_src.append(line)
                if not inserted and line.startswith("#"):
                    new_src.append("\n")
                    new_src.append(badge_text)
                    new_src.append("\n")
                    inserted = True
            if not inserted:
                new_src.insert(0, badge_text + "\n")
            first_cell["source"] = new_src
    
    with open(ppath, "w", encoding="utf-8") as f:
        json.dump(nb_data, f, ensure_ascii=False, indent=1)
    print(f"  [V1.0 认证成功] {pname}")

# 4. 归档 labs/ad2026
ad2026_src = os.path.join(REPO_DIR, "labs", "ad2026")
ad2026_dst = os.path.join(REPO_DIR, "labs", "archive", "legacy_ad2026")
if os.path.isdir(ad2026_src):
    os.makedirs(os.path.dirname(ad2026_dst), exist_ok=True)
    if os.path.exists(ad2026_dst):
        shutil.rmtree(ad2026_dst)
    shutil.move(ad2026_src, ad2026_dst)
    print(f"\n--- 步骤 3: 归档 labs/ad2026 到 {ad2026_dst} ---")
    with open(os.path.join(REPO_DIR, "labs", "archive", "README.md"), "w", encoding="utf-8") as f:
        f.write("# labs/archive 平台历史资源归档\n\n本目录包含平台早期的历史工具与原型资产，不在正式环境分发与运行。\n")

print("\n=== 全部归档与 V1.0 认证标记完成 ===")
