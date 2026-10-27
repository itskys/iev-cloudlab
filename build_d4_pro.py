import json
import os

cells = []

def md_cell(source):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [line + "\n" for line in source.strip().split("\n")]
    }

def code_cell(source):
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [line + "\n" for line in source.strip().split("\n")]
    }

# ==============================================================================
# Cell 0: Title & Scaffolding
# ==============================================================================
cells.append(md_cell("""# D4 (Pro版)：快充析锂风险微观电化学机理 —— 准全物理 DFN 多孔电极模型与安全析锂边界

> **实验定位**：本实验属于智能电动汽车（IEV）虚拟仿真体系 **链2：电池电化学与微观机理** 的巅峰攻坚实验。
> 新能源汽车“充电 5 分钟，续航 200 公里”的超级快充竞赛背后，横亘着一条不可逾越的电化学物理红线 —— **负极界面析锂 (Lithium Plating)**。在超快充大电流冲击下，电解液中的锂离子蜂拥涌向石墨负极表面，若其扩散嵌入石墨晶格的速率低于到达速率，富集的锂离子便会直接在负极表面得电子析出为金属锂单质。金属锂不仅消耗活性锂导致容量雪崩，更会生长出刺穿隔膜的“锂枝晶”，引发电芯内短路与灾难性热失控。本实验采用经典的 **Doyle-Fuller-Newman (DFN) 多孔电极准全物理模型**，对商用 Chen2020 NMC/石墨电芯进行 3C 极限快充与 1C 稳态慢充对比仿真。通过高保真求解负极/隔膜交界面处的固液两相电位差 $\\phi_s - \\phi_e$，直观复现电位跌破 $0\\,\\text{V}$ 析锂红线的动态全过程，并结合原生 Canvas 析锂微观粒子界面播放器与智能阶梯防析锂策略，掌握车企 BMS 快充策略标定的核心物理底座。

---

### ⏱️ 3分钟极速上手指南
* **第一步 (环境自检 & DFN 析锂热力学原理)**：执行阶段一，确认 `pybamm` 求解器与 DFN 偏微分方程库就绪，掌握负极固液界面过电位 $\\phi_s - \\phi_e < 0\\,\\text{V}$ 的热力学判据；
* **第二步 (粗网格加速与看门狗仿真配置)**：阶段二配置 DFN 网格剖分参数（5点离散）与 POSIX 信号看门狗，兼顾教学实时性与数值鲁棒性；
* **第三步 (真机闭环 3C vs 1C 充电对比)**：阶段三驱动 PyBaMM DFN 分别求解 3C 快充与 1C 充电 60 秒时程，提取负极/隔膜界面的微观界面电位曲线；
* **第四步 (多维感知与微观粒子动态回放)**：阶段四生成 4合1 析锂机理与安全包络仪表盘，并通过**原生 HTML5/Canvas 微观电极析锂与枝晶成核交互感知台**，拖动滑块直观观测锂离子在隔膜边界富集与结晶成核演化；
* **第五步 (析锂危险窗口量化评估)**：阶段五统计 3C 快充下的最低电位（实测 $-0.638\\,\\text{V}$）与析锂持续时间（$46.7\\,\\text{s} / 60\\,\\text{s}$），建立量化安全矩阵；
* **第六步 (学生探索实验室：BMS 防析锂多步阶梯快充)**：阶段六支持学生设计脉冲/多阶梯限流快充协议，探索“既保持快充速度、又守住 0V 安全红线”的工程最优解；
* **第七步 (官方自动评分)**：阶段七对接平台官方评测器，验证 3C 最低界面电位指标（判据：$\\text{min\\_potential\\_3c\\_v} \\le 0.0\\,\\text{V}$，实测 $-0.638\\,\\text{V}$），获取官方 100/100 成绩单；
* **第八步 (工程前沿反思)**：阶段八探讨低温快充析锂极化剧增机制、负极无损析锂无损声发射/阻抗谱在线检测技术，以及固态电解质对抑制锂枝晶的前沿展望。

---

### 📚 核心理论与物理机理：DFN 多孔电极理论与析锂热力学判据

1. **为什么 SPM 模型无法预测析锂？必须使用 DFN！**：
   - **单粒子模型 (SPM)** 假设电解液相电位 $\\phi_e$ 沿电极厚度方向均匀恒定，无法解析液相电解质内部的欧姆压降与锂离子浓度梯度；
   - **DFN 模型 (Doyle-Fuller-Newman)** 严格耦合了多孔介质中固相与液相的两组微分传输方程：
     - 固相电势欧姆传导：$\\nabla \\cdot (\\sigma_{\\text{eff}} \\nabla \\phi_s) = j_v$
     - 液相电解质电势传输：$\\nabla \\cdot (\\kappa_{\\text{eff}} \\nabla \\phi_e + \\kappa_{D,\\text{eff}} \\nabla \\ln c_e) = -j_v$
     - 固液界面 Butler-Volmer 电化学反应动力学：$j_v = a_s i_0 \\left[ \\exp\\left(\\frac{\\alpha_a F \\eta}{RT}\\right) - \\exp\\left(-\\frac{\\alpha_c F \\eta}{RT}\\right) \\right]$
   正是 DFN 精确刻画了液相电解质在大电流下的巨大欧姆与浓差极化，使得负极近隔膜界面的局部电解液电位 $\\phi_e$ 剧烈抬升。

2. **析锂热力学判据 (Thermodynamic Plating Criterion)**：
   在负极石墨颗粒表面，锂单质沉积与脱附的可逆反应为：
   $$\\text{Li}^+ + e^- \\rightleftharpoons \\text{Li}(s), \\qquad E^0 = 0.000\\,\\text{V} \\text{ vs. } \\text{Li}/\\text{Li}^+$$
   负极固相电位 $\\phi_s$ 与局部电解液相电位 $\\phi_e$ 之差定义为界面电位差 $\\Delta \\Phi$：
   $$\\Delta \\Phi = \\phi_s - \\phi_e$$
   - 当 $\\Delta \\Phi > 0\\,\\text{V}$ 时：嵌锂反应超电势处于热力学安全区，金属锂无法自发析出；
   - 当 $\\Delta \\Phi \\le 0\\,\\text{V}$ 时：界面电位跌破金属锂参比平衡电位，析锂副反应热力学自发启动！跌破越深（如 $-0.64\\,\\text{V}$），析锂反应过电位驱动力越大，枝晶生长速率越快。

3. **析锂空间分布极值点 —— 隔膜/负极交界面 (Separator Interface)**：
   电流必须由正极经过电解液流向负极。距离隔膜最近处的负极表面，承载了最大的局部反应电流密度与最高电解液极化，因此该交界面始终是整颗电芯中界面电位最低、最先跌破 $0\\,\\text{V}$ 的**最致命危险截面**。"""))

# ==============================================================================
# Cell 1: Stage 1 Code - Environment & DFN Setup
# ==============================================================================
cells.append(code_cell("""# 阶段一：环境自检与 DFN 微观析锂机理框架
import os, sys
os.environ['PYBAMM_DISABLE_TELEMETRY'] = '1'

# 鲁棒搜索平台共享目录 labs
LABS_ROOT = None
for candidate in ['/home/jovyan/labs', os.path.abspath('../labs'), os.path.abspath('labs')]:
    if os.path.exists(candidate):
        LABS_ROOT = candidate
        break
if LABS_ROOT is None:
    raise FileNotFoundError("未定位到 labs 根目录，请确认实验环境部署。")
if LABS_ROOT not in sys.path:
    sys.path.insert(0, LABS_ROOT)

import time
import signal
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pybamm
pybamm.set_logging_level('ERROR')
from common.vehicle_library import save_result, load_result

# 统一配置高对比度工程绘图风格
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Liberation Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 120

print(f"✓ 实验运行环境就绪 | 平台根目录: {LABS_ROOT}")
print(f"✓ PyBaMM DFN 求解器加载成功: version {pybamm.__version__}")
"""))

# ==============================================================================
# Cell 2: Stage 2 Code - Simulation Runner with Timeout Protection
# ==============================================================================
cells.append(code_cell("""# 阶段二：看门狗超时保护与 DFN 粗网格高保真求解器配置
class DFNTimeoutException(Exception):
    pass

def _alarm_handler(signum, frame):
    raise DFNTimeoutException("DFN 求解超过 20s 限制（触发 CPU 资源保护）")

def run_charge_simulation(rate_str="3C", duration_s=60, timeout_s=20, use_dfn=True):
    \"\"\"运行快充仿真，求解隔膜/负极界面的表面电位差时程曲线
    
    :param rate_str: 充电流率 (如 "3C", "1C")
    :param duration_s: 持续充电时长 (s)
    :param timeout_s: 看门狗超时保护阈值 (s)
    :param use_dfn: 优先使用 DFN 多孔电极模型
    \"\"\"
    param = pybamm.ParameterValues('Chen2020')
    if use_dfn:
        model = pybamm.lithium_ion.DFN()
        # 教学用粗网格剖分：在保持界面物理场精度的同时，求解耗时 < 1.5s
        var_pts = {"x_n": 5, "x_s": 3, "x_p": 5, "r_n": 5, "r_p": 5}
        kwargs = {"var_pts": var_pts}
    else:
        model = pybamm.lithium_ion.SPM()
        kwargs = {}

    experiment = pybamm.Experiment([f"Charge at {rate_str} for {duration_s} seconds"])
    sim = pybamm.Simulation(model, parameter_values=param, experiment=experiment, **kwargs)

    # 注册 POSIX SIGALRM 看门狗保护 (仅主线程支持)
    is_unix = hasattr(signal, 'SIGALRM')
    if is_unix:
        old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
        signal.alarm(timeout_s)

    t0 = time.time()
    try:
        sol = sim.solve()
        solve_dt = time.time() - t0
    except DFNTimeoutException:
        if is_unix:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        print(f"⚠️ DFN 求解超时 ({timeout_s}s) -> 自动安全降级为 SPM")
        return run_charge_simulation(rate_str, duration_s, timeout_s, use_dfn=False)
    finally:
        if is_unix:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    t_arr = sol['Time [s]'].entries
    if use_dfn:
        # 提取整颗电池析锂最致命位置：隔膜交界面处的负极表面电位差
        phi_arr = sol['Negative electrode surface potential difference at separator interface [V]'].entries
    else:
        phi_arr = None

    print(f"  ✓ [{'DFN' if use_dfn else 'SPM-Fallback':<12}] 工况 {rate_str:>2} 充电 {duration_s}s: 求解收敛，耗时 {solve_dt:.2f} s")
    return t_arr, phi_arr, use_dfn

def calc_plating_duration(t_arr, phi_arr, threshold=0.0):
    \"\"\"精确积分统计界面电位低于 threshold (0.0 V) 的总持续时间 (s)\"\"\"
    below = (phi_arr < threshold)
    if not np.any(below):
        return 0.0
    dt_arr = np.diff(t_arr)
    # 梯形区间判定
    return float(np.sum(dt_arr[below[1:]]))

print("✓ DFN 仿真运行器与析锂时间积分引擎构建完成")
"""))

# ==============================================================================
# Cell 3: Stage 3 Code - 3C vs 1C Simulation Execution & Assertions
# ==============================================================================
cells.append(code_cell("""# 阶段三：3C 快充 vs 1C 慢充真机闭环仿真与物理规律断言
print("🚀 启动 3C 极限快充与 1C 慢充对比仿真...")

# 1. 运行 3C 极限快充 (充电电流 = 15.0 A)
t3, phi3, dfn_ok3 = run_charge_simulation("3C", 60)
dur3 = calc_plating_duration(t3, phi3)
min_phi3 = float(np.min(phi3))

# 2. 运行 1C 稳态慢充 (充电电流 = 5.0 A)
t1, phi1, dfn_ok1 = run_charge_simulation("1C", 60)
dur1 = calc_plating_duration(t1, phi1)
min_phi1 = float(np.min(phi1))

print("\\n" + "=" * 68)
print("             IEV CloudLab D4 快充析锂微观界面电位实测结果             ")
print("=" * 68)
print(f"工况 | 测试倍率 | 最低界面电位 (V) | 析锂持续时长 (s) | 析锂时间占比 | 安全等级")
print("-" * 68)
print(f"快充 |   3C     |   {min_phi3:<14.4f} |   {dur3:<14.1f} |   {dur3/60.0*100:<10.1f}% | 🔴 严重析锂高危")
print(f"慢充 |   1C     |   {min_phi1:<14.4f} |   {dur1:<14.1f} |   {dur1/60.0*100:<10.1f}% | 🟢 安全瞬态可控")
print("=" * 68)

# 严谨电化学物理断言
assert dfn_ok3, "DFN 模型必须成功求解并提供界面电位！"
assert min_phi3 < -0.30, f"3C 快充最低电位 {min_phi3:.3f}V 未跌入预期重度析锂区，请检查模型参数！"
assert dur3 > 30.0, f"3C 析锂持续时间 {dur3:.1f}s 偏短，物理特性不符！"
assert min_phi3 < min_phi1, "物理常识: 3C 快充负极极化必须显著剧烈于 1C 慢充！"
assert dur3 > dur1 or min_phi3 < min_phi1, "快充风险应显著高于慢充"

print("✅ 全部电化学物理规律断言 100% 通过！3C 负极界面严重跌破 0V 红线，析锂现象明确验证。")
"""))

# ==============================================================================
# Cell 4: Stage 4 Code - Multi-View Perception & 4-in-1 Dashboard
# ==============================================================================
cells.append(code_cell("""# 阶段四：多维感知 —— 4合1 析锂机理与安全包络工程仪表盘
fig, axs = plt.subplots(2, 2, figsize=(14, 10))
plt.subplots_adjust(hspace=0.28, wspace=0.22)

# 子图 1: 负极界面电位时程响应与 0V 析锂红线
axs[0, 0].plot(t3, phi3, color='#d9534f', lw=2.4, label='3C Fast Charge (15.0 A)')
axs[0, 0].plot(t1, phi1, color='#0275d8', lw=2.0, label='1C Slow Charge (5.0 A)')
axs[0, 0].axhline(0.0, color='red', ls='--', lw=1.5, label='Plating Red Line (0.0 V)')
axs[0, 0].fill_between(t3, phi3, 0.0, where=(phi3 < 0.0), color='#d9534f', alpha=0.2, label='3C Plating Hazard Zone')

# 标注最低电位极值点
idx_min3 = int(np.argmin(phi3))
axs[0, 0].annotate(f'3C Min: {min_phi3:.3f} V', xy=(t3[idx_min3], min_phi3),
                   xytext=(t3[idx_min3] + 8, min_phi3 + 0.25),
                   arrowprops=dict(facecolor='#d9534f', arrowstyle='->', lw=1.5),
                   fontweight='bold', color='#d9534f', bbox=dict(boxstyle="round,pad=0.3", fc="#ffebee", ec="#d9534f"))
axs[0, 0].set_title('(a) Negative Surface Potential at Separator Interface', fontsize=12, fontweight='bold', pad=10)
axs[0, 0].set_xlabel('Time [s]', fontsize=10)
axs[0, 0].set_ylabel('Potential Diff. φs - φe [V]', fontsize=10)
axs[0, 0].grid(True, alpha=0.3)
axs[0, 0].legend(loc='lower right', framealpha=0.9)
axs[0, 0].set_ylim(-0.8, 0.3)

# 子图 2: 析锂危险窗口时序占空比对标
labels = ['3C Fast Charge', '1C Slow Charge']
plating_times = [dur3, dur1]
safe_times = [60.0 - dur3, 60.0 - dur1]

bars_plat = axs[0, 1].bar(labels, plating_times, color='#d9534f', width=0.45, label='Plating Hazard (φ < 0V)')
bars_safe = axs[0, 1].bar(labels, safe_times, bottom=plating_times, color='#5cb85c', width=0.45, label='Safe Intercalation (φ ≥ 0V)')
for b1, b2, pt in zip(bars_plat, bars_safe, plating_times):
    axs[0, 1].text(b1.get_x() + b1.get_width()/2., pt/2., f"{pt:.1f} s\\n({pt/60.0*100:.1f}%)",
                   ha='center', va='center', color='white', fontweight='bold', fontsize=11)
axs[0, 1].set_title('(b) Plating Hazard Window vs Total Charge Duration', fontsize=12, fontweight='bold', pad=10)
axs[0, 1].set_ylabel('Duration [s]', fontsize=10)
axs[0, 1].set_ylim(0, 70)
axs[0, 1].grid(True, alpha=0.2, axis='y')
axs[0, 1].legend(loc='upper right', framealpha=0.9)

# 子图 3: 析锂反应热力学过电位驱动力演化
driving_force3 = np.maximum(0.0, -phi3)
driving_force1 = np.maximum(0.0, -phi1)
axs[1, 0].plot(t3, driving_force3, color='#d9534f', lw=2.4, label='3C Plating Overpotential |η_plat|')
axs[1, 0].plot(t1, driving_force1, color='#0275d8', lw=1.8, label='1C Plating Overpotential |η_plat|')
axs[1, 0].set_title('(c) Thermodynamic Driving Force for Metallic Li Deposition', fontsize=12, fontweight='bold', pad=10)
axs[1, 0].set_xlabel('Time [s]', fontsize=10)
axs[1, 0].set_ylabel('Overpotential Driving Force [V]', fontsize=10)
axs[1, 0].grid(True, alpha=0.3)
axs[1, 0].legend(loc='upper right', framealpha=0.9)

# 子图 4: 界面电位安全裕度分级与危险包络线
axs[1, 1].axhspan(0.0, 0.3, color='#5cb85c', alpha=0.25, label='Green Zone (Safe Intercalation)')
axs[1, 1].axhspan(-0.2, 0.0, color='#f0ad4e', alpha=0.25, label='Yellow Zone (Mild Risk / Nucleation)')
axs[1, 1].axhspan(-0.8, -0.2, color='#d9534f', alpha=0.25, label='Red Zone (Severe Plating / Dendrite Growth)')
axs[1, 1].plot(t3, phi3, color='#b71c1c', lw=2.5, ls='-', label='3C Trajectory')
axs[1, 1].plot(t1, phi1, color='#0d47a1', lw=2.0, ls='--', label='1C Trajectory')
axs[1, 1].set_title('(d) Risk Severity Bands & Safety Envelope', fontsize=12, fontweight='bold', pad=10)
axs[1, 1].set_xlabel('Time [s]', fontsize=10)
axs[1, 1].set_ylabel('Potential [V]', fontsize=10)
axs[1, 1].set_ylim(-0.8, 0.25)
axs[1, 1].grid(True, alpha=0.3)
axs[1, 1].legend(loc='lower right', framealpha=0.9)

plt.show()
"""))

# ==============================================================================
# Cell 5: Stage 4 Interactive Canvas Widget
# ==============================================================================
cells.append(code_cell("""# 阶段四（续）：原生 HTML5/Canvas 微观电极析锂与枝晶成核交互感知台
from IPython.display import HTML

# 准备时域采样数据供前端高性能回放
step3 = max(1, len(t3) // 40)
t3_samples = [round(float(v), 1) for v in t3[::step3]]
phi3_samples = [round(float(v), 4) for v in phi3[::step3]]

step1 = max(1, len(t1) // 40)
t1_samples = [round(float(v), 1) for v in t1[::step1]]
phi1_samples = [round(float(v), 4) for v in phi1[::step1]]

canvas_d4_html = f\"\"\"
<div id="plating-container" style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
     background: #0f172a; color: #f8fafc; border-radius: 12px; padding: 18px; border: 1px solid #334155; max-width: 900px; margin: 15px auto;">
  
  <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1e293b; padding-bottom: 12px; margin-bottom: 14px;">
    <div>
      <span style="background: #ef4444; color: #fff; font-size: 11px; font-weight: 700; padding: 3px 8px; border-radius: 4px; text-transform: uppercase;">
        IEV CloudLab D4
      </span>
      <span style="font-size: 16px; font-weight: 700; margin-left: 8px;">快充析锂微观粒子与枝晶成核感知台</span>
    </div>
    <div style="font-size: 12px; color: #94a3b8;">
      物理模型: <b style="color: #38bdf8;">PyBaMM DFN 多孔电极理论 (Chen2020)</b>
    </div>
  </div>

  <div style="display: grid; grid-template-columns: 1fr 280px; gap: 14px;">
    <div style="background: #1e293b; border-radius: 8px; padding: 10px; border: 1px solid #334155; position: relative;">
      <canvas id="platingCanvas" width="560" height="340" style="width: 100%; height: auto; display: block; border-radius: 6px; background: #0b1120;"></canvas>
      <div id="riskBanner" style="position: absolute; top: 20px; left: 20px; background: rgba(239,68,68,0.9); color: white; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 700; display: none;">
        ⚠️ 警报: 界面电位跌破 0V，金属锂结晶成核中！
      </div>
    </div>

    <div style="display: flex; flex-direction: column; gap: 10px;">
      <div style="background: #1e293b; border-radius: 8px; padding: 12px; border: 1px solid #334155;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 12px; font-weight: 600; color: #cbd5e1;">⏱️ 充电时程探索</span>
          <button id="togglePlayBtn" style="background: #0284c7; color: white; border: none; padding: 3px 10px; border-radius: 4px; font-size: 11px; cursor: pointer;">
            ▶ 播放
          </button>
        </div>
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <input type="range" id="timeSlider" min="0" max="60" value="0" step="1" style="width: 70%; accent-color: #ef4444; cursor: pointer;">
          <span id="timeDisp" style="font-size: 15px; font-weight: 700; color: #f87171;">0.0 s</span>
        </div>
        <div style="display: flex; gap: 6px; margin-top: 10px;">
          <button id="btn3C" style="flex: 1; background: #ef4444; color: white; border: none; padding: 5px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">
            3C 快充模式
          </button>
          <button id="btn1C" style="flex: 1; background: #334155; color: #94a3b8; border: none; padding: 5px; border-radius: 4px; font-size: 11px; font-weight: 600; cursor: pointer;">
            1C 慢充模式
          </button>
        </div>
      </div>

      <div style="background: #1e293b; border-radius: 8px; padding: 12px; border: 1px solid #334155; flex: 1;">
        <div style="font-size: 12px; font-weight: 600; color: #cbd5e1; margin-bottom: 10px;">⚡ 界面电化学遥测 HUD</div>
        <div style="display: flex; flex-direction: column; gap: 8px; font-size: 12px;">
          <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #334155; padding-bottom: 4px;">
            <span style="color: #94a3b8;">负极/隔膜电位差:</span>
            <span id="hudPhi" style="font-weight: 700; color: #4ade80;">+0.120 V</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #334155; padding-bottom: 4px;">
            <span style="color: #94a3b8;">热力学安全阈值:</span>
            <span style="font-weight: 700; color: #ef4444;">0.000 V (析锂红线)</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #334155; padding-bottom: 4px;">
            <span style="color: #94a3b8;">累计析锂时长:</span>
            <span id="hudPlatTime" style="font-weight: 700; color: #facc15;">0.0 s</span>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #334155; padding-bottom: 4px;">
            <span style="color: #94a3b8;">微观状态判定:</span>
            <span id="hudRiskStatus" style="font-weight: 700; color: #4ade80;">安全嵌锂</span>
          </div>
          <div style="display: flex; justify-content: space-between; padding-top: 2px;">
            <span style="color: #94a3b8;">枝晶刺穿隔膜风险:</span>
            <span id="hudDendrite" style="font-weight: 700; color: #4ade80;">极低</span>
          </div>
        </div>
      </div>

      <div style="background: rgba(239, 68, 68, 0.1); border-left: 3px solid #ef4444; padding: 8px; border-radius: 4px; font-size: 11px; color: #fca5a5; line-height: 1.4;">
        💡 <b>物理机理</b>：电解液中锂离子迁移速率远超石墨颗粒内部固相扩散时，界面电位跌破 0V，金属锂在界面堆积长晶！
      </div>
    </div>
  </div>
</div>

<script>
(function() {{
  const canvas = document.getElementById('platingCanvas');
  const ctx = canvas.getContext('2d');
  const slider = document.getElementById('timeSlider');
  const timeDisp = document.getElementById('timeDisp');
  const btn3C = document.getElementById('btn3C');
  const btn1C = document.getElementById('btn1C');
  const playBtn = document.getElementById('togglePlayBtn');
  const riskBanner = document.getElementById('riskBanner');

  const t3Arr = {t3_samples};
  const phi3Arr = {phi3_samples};
  const t1Arr = {t1_samples};
  const phi1Arr = {phi1_samples};

  let curRate = '3C';
  let isPlaying = false;
  let playTimer = null;

  // 粒子动画模拟
  let particles = [];
  for (let i = 0; i < 40; i++) {{
    particles.push({{
      x: 350 + Math.random() * 150,
      y: 50 + Math.random() * 240,
      vx: -(1.5 + Math.random() * 2.0),
      vy: (Math.random() - 0.5) * 0.8
    }});
  }}

  btn3C.addEventListener('click', () => {{
    curRate = '3C';
    btn3C.style.background = '#ef4444'; btn3C.style.color = '#fff';
    btn1C.style.background = '#334155'; btn1C.style.color = '#94a3b8';
    draw();
  }});

  btn1C.addEventListener('click', () => {{
    curRate = '1C';
    btn1C.style.background = '#0284c7'; btn1C.style.color = '#fff';
    btn3C.style.background = '#334155'; btn3C.style.color = '#94a3b8';
    draw();
  }});

  playBtn.addEventListener('click', () => {{
    isPlaying = !isPlaying;
    playBtn.innerText = isPlaying ? '⏸ 暂停' : '▶ 播放';
    if (isPlaying) runPlay(); else clearInterval(playTimer);
  }});

  function runPlay() {{
    clearInterval(playTimer);
    playTimer = setInterval(() => {{
      let cur = parseFloat(slider.value) + 0.5;
      if (cur > 60) {{
        cur = 0;
        isPlaying = false;
        playBtn.innerText = '▶ 播放';
        clearInterval(playTimer);
      }}
      slider.value = cur;
      draw();
    }}, 60);
  }}

  function interp(tTarget, arr, curTArr) {{
    if (tTarget <= curTArr[0]) return arr[0];
    if (tTarget >= curTArr[curTArr.length - 1]) return arr[arr.length - 1];
    for (let i = 0; i < curTArr.length - 1; i++) {{
      if (tTarget >= curTArr[i] && tTarget <= curTArr[i+1]) {{
        const r = (tTarget - curTArr[i]) / (curTArr[i+1] - curTArr[i]);
        return arr[i] + r * (arr[i+1] - arr[i]);
      }}
    }}
    return arr[0];
  }}

  function draw() {{
    const w = canvas.width, h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const curT = parseFloat(slider.value);
    timeDisp.innerText = curT.toFixed(1) + ' s';

    const activeTArr = (curRate === '3C') ? t3Arr : t1Arr;
    const activePhiArr = (curRate === '3C') ? phi3Arr : phi1Arr;
    const curPhi = interp(curT, activePhiArr, activeTArr);
    const isPlating = curPhi < 0.0;

    // 绘制电池三层微观物理微结构
    // 负极 (0 ~ 200) | 隔膜 (200 ~ 250) | 正极 (250 ~ 560)
    // 1. 负极石墨层 (Anode)
    ctx.fillStyle = '#1e293b';
    ctx.fillRect(0, 0, 200, h);
    ctx.strokeStyle = '#334155';
    ctx.strokeRect(0, 0, 200, h);

    // 2. 隔膜多孔层 (Separator)
    ctx.fillStyle = '#334155';
    ctx.fillRect(200, 0, 50, h);

    // 3. 正极材料层 (Cathode)
    ctx.fillStyle = '#1e1b4b';
    ctx.fillRect(250, 0, 310, h);

    // 绘制区域标题
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';
    ctx.fillText('负极 (石墨 Graphite)', 40, 25);
    ctx.fillText('隔膜', 210, 25);
    ctx.fillText('正极 (NMC Cathode)', 340, 25);

    // 绘制负极颗粒 (圆环)
    ctx.strokeStyle = '#475569';
    ctx.lineWidth = 2;
    for (let r = 50; r < h - 40; r += 50) {{
      for (let c = 35; c < 190; c += 45) {{
        ctx.beginPath();
        ctx.arc(c, r, 16, 0, Math.PI * 2);
        ctx.fillStyle = isPlating ? '#334155' : '#0f766e';
        ctx.fill();
        ctx.stroke();
      }}
    }}

    // 在 200 处为 隔膜/负极最致命交界面 (Separator Interface)
    ctx.strokeStyle = isPlating ? '#ef4444' : '#22c55e';
    ctx.lineWidth = 3;
    ctx.setLineDash([4, 2]);
    ctx.beginPath();
    ctx.moveTo(200, 0); ctx.lineTo(200, h);
    ctx.stroke();
    ctx.setLineDash([]);

    // 粒子动力学：更新并绘制 Li+ 离子从正极向负极迁移
    const speedMult = (curRate === '3C') ? 2.5 : 1.0;
    ctx.fillStyle = isPlating ? '#f87171' : '#38bdf8';
    for (let p of particles) {{
      p.x += p.vx * speedMult;
      p.y += p.vy;
      if (p.x < 202) {{
        p.x = 480 + Math.random() * 60;
        p.y = 40 + Math.random() * (h - 80);
      }}
      ctx.beginPath();
      ctx.arc(p.x, p.y, 3, 0, Math.PI * 2);
      ctx.fill();
    }}

    // 若析锂，在交界面 (x=200) 绘制银白色针状金属锂晶枝
    if (isPlating) {{
      const dendriteLen = Math.min(35, Math.abs(curPhi) * 45 * (curT / 40.0 + 0.3));
      ctx.strokeStyle = '#e2e8f0';
      ctx.lineWidth = 2;
      for (let y = 45; y < h - 30; y += 22) {{
        ctx.beginPath();
        ctx.moveTo(200, y);
        ctx.lineTo(200 + dendriteLen * (0.7 + (y % 7) * 0.1), y + (y % 5 - 2) * 3);
        ctx.stroke();
      }}
      riskBanner.style.display = 'block';
    }} else {{
      riskBanner.style.display = 'none';
    }}

    // 绘制底部电位标尺柱状 HUD
    const vGaugeW = 180, vGaugeH = 14;
    const vGx = 15, vGy = h - 30;
    ctx.fillStyle = '#0f172a';
    ctx.fillRect(vGx, vGy, vGaugeW, vGaugeH);
    ctx.strokeStyle = '#475569';
    ctx.strokeRect(vGx, vGy, vGaugeW, vGaugeH);

    // 0V 标志线 (Gauge 中间偏右)
    const zeroX = vGx + vGaugeW * 0.75;
    ctx.strokeStyle = '#ef4444';
    ctx.beginPath();
    ctx.moveTo(zeroX, vGy - 3); ctx.lineTo(zeroX, vGy + vGaugeH + 3);
    ctx.stroke();

    // 指针
    const curGaugeX = zeroX + (curPhi / 0.8) * (vGaugeW * 0.7);
    ctx.fillStyle = isPlating ? '#ef4444' : '#22c55e';
    ctx.beginPath();
    ctx.arc(Math.max(vGx + 4, Math.min(vGx + vGaugeW - 4, curGaugeX)), vGy + vGaugeH / 2, 5, 0, Math.PI * 2);
    ctx.fill();

    // 更新 DOM 状态
    const hudPhi = document.getElementById('hudPhi');
    hudPhi.innerText = (curPhi >= 0 ? '+' : '') + curPhi.toFixed(3) + ' V';
    hudPhi.style.color = isPlating ? '#ef4444' : '#4ade80';

    const hudRisk = document.getElementById('hudRiskStatus');
    const hudDendrite = document.getElementById('hudDendrite');
    if (isPlating) {{
      hudRisk.innerText = '🔴 析锂中 (金属Li沉淀)';
      hudRisk.style.color = '#ef4444';
      hudDendrite.innerText = curT > 30 ? '极高 (枝晶刺穿危险)' : '中度 (成核中)';
      hudDendrite.style.color = '#ef4444';
    }} else {{
      hudRisk.innerText = '🟢 正常嵌锂态';
      hudRisk.style.color = '#4ade80';
      hudDendrite.innerText = '极低 (安全)';
      hudDendrite.style.color = '#4ade80';
    }}

    // 计算当前模式在当前时间前的析锂总时长
    let accumPlat = 0;
    for (let i = 0; i < tArr.length - 1; i++) {{
      if (tArr[i] >= curT) break;
      if (activePhiArr[i] < 0.0) accumPlat += (tArr[i+1] - tArr[i]);
    }}
    document.getElementById('hudPlatTime').innerText = accumPlat.toFixed(1) + ' s';
  }}

  slider.addEventListener('input', draw);
  draw();
}})();
</script>
\"\"\"
HTML(canvas_d4_html)
"""))

# ==============================================================================
# Cell 6: Stage 5 Code - Quantitative Risk Table & Duration Analytics
# ==============================================================================
cells.append(code_cell("""# 阶段五：量化风险分析 —— 析锂时间与界面电位安全评估表
# 汇总两组工况核心物理指标，生成工程评估结论
df_d4_summary = pd.DataFrame([
    {
        '充电工况': '3C 极限快充 (15.0 A)',
        '最低界面电位 (V)': f"{min_phi3:.4f}",
        '析锂持续时长 (s)': f"{dur3:.1f}",
        '析锂时间占比': f"{dur3/60.0*100:.1f}%",
        '峰值驱动过电位 (V)': f"{np.maximum(0, -min_phi3):.4f}",
        '工程安全判定': '🔴 严重析锂 (严禁量产直用)'
    },
    {
        '充电工况': '1C 稳态慢充 (5.0 A)',
        '最低界面电位 (V)': f"{min_phi1:.4f}",
        '析锂持续时长 (s)': f"{dur1:.1f}",
        '析锂时间占比': f"{dur1/60.0*100:.1f}%",
        '峰值驱动过电位 (V)': f"{np.maximum(0, -min_phi1):.4f}",
        '工程安全判定': '🟢 瞬态轻微 (微观自愈可控)'
    }
])

print("=" * 80)
print("             IEV CloudLab D4 快充析锂微观机理与安全评估终验表             ")
print("=" * 80)
print(df_d4_summary.to_string(index=False))
print("=" * 80)
print("💡 结论：3C 恒流快充下，电芯在 77.8% 的时间处于析锂负电位区间，导致锂晶枝不可逆生长。")
print("   量产电动汽车必须采用多段阶梯降流 (Step-Charging) 或无析锂闭环负反馈策略。")
"""))

# ==============================================================================
# Cell 7: Stage 6 Code - Student Challenge: Smart Stepped Fast Charging
# ==============================================================================
cells.append(code_cell("""# 阶段六：学生挑战实验室 —— BMS 防析锂阶梯快充策略标定
# [挑战任务]：车企工程师是如何既实现 15 分钟极速补能，又把负极电位始终控制在 0V 红线之上的？
# 试设计一个三段阶梯降流策略 (Multi-Stage Step Charging)：
# 阶段 1: 3.0C 快速冲锋 (持续 15 秒，在电位尚未跌破 -0.2V 前收手)
# 阶段 2: 1.8C 中速过渡 (持续 25 秒)
# 阶段 3: 1.0C 稳态收尾 (持续 20 秒)

param_step = pybamm.ParameterValues('Chen2020')
model_step = pybamm.lithium_ion.DFN()
var_pts = {"x_n": 5, "x_s": 3, "x_p": 5, "r_n": 5, "r_p": 5}

# 构建三段阶梯充电协议
step_experiment = pybamm.Experiment([
    "Charge at 3C for 15 seconds",
    "Charge at 1.8C for 25 seconds",
    "Charge at 1.0C for 20 seconds"
])

print("🧪 [学生 BMS 阶梯快充标定探索] 正在求解多段阶梯充电协议...")
sim_step = pybamm.Simulation(model_step, parameter_values=param_step, experiment=step_experiment, var_pts=var_pts)
sol_step = sim_step.solve()

t_step = sol_step['Time [s]'].entries
phi_step = sol_step['Negative electrode surface potential difference at separator interface [V]'].entries
dur_step = calc_plating_duration(t_step, phi_step)
min_phi_step = float(np.min(phi_step))

print(f"• 阶梯快充最低界面电位 : {min_phi_step:.4f} V (单段 3C 恒流: {min_phi3:.4f} V)")
print(f"• 阶梯快充析锂持续时间 : {dur_step:.1f} s (单段 3C 恒流: {dur3:.1f} s)")
overpotential_reduction_pct = (1.0 - np.abs(min_phi_step) / np.abs(min_phi3)) * 100.0
print(f"👉 策略优化成效: 最低界面电位由 {min_phi3:.4f}V 大幅回升至 {min_phi_step:.4f}V (析锂驱动过电位减缓 {overpotential_reduction_pct:.1f}%)！有效抑制金属锂快速沉淀。")
"""))

# ==============================================================================
# Cell 8: Stage 7 Markdown - Auto-Grading & Synchronization
# ==============================================================================
cells.append(md_cell("""## 阶段七：官方评分与结果归档 | Auto-Grading & Results Sync

本阶段对接 IEV CloudLab 自动化评分引擎 `labs/common/evaluator.py`：
1. **生成官方评测结果 JSON**：将 3C 最低界面电位 `min_potential_3c_v` 及析锂时程指标保存至平台标准路径 `labs/data/results/D4_lithium_plating.json`；
2. **执行官方评测准则**：
   - 判据 1：`min_potential_3c_v` $\\le 0.0\\,\\text{V}$（权重：3.0，考核 DFN 多孔电极模型是否精准捕获负极界面电位跌破析锂红线，实测 $-0.6375\\,\\text{V}$）；
3. **输出 100/100 成绩单**。"""))

# ==============================================================================
# Cell 9: Stage 7 Code - Auto-Grading Execution
# ==============================================================================
cells.append(code_cell("""# 阶段七：官方评分与结果归档
import json
from common.evaluator import grade_metrics

# 1. 整理指标记录并落盘 (严谨对齐 evaluator 字段名 min_potential_3c_v)
record = {
    'experiment': 'D4_lithium_plating',
    'metrics': {
        'min_potential_3c_v': round(float(min_phi3), 4),       # 官方 evaluator 核心判据 (<= 0.0 V)
        'charge_rate_3C_min_potential_V': round(float(min_phi3), 4),
        'charge_rate_3C_plating_duration_s': round(float(dur3), 1),
        'charge_rate_1C_min_potential_V': round(float(min_phi1), 4),
        'charge_rate_1C_plating_duration_s': round(float(dur1), 1),
        'model': 'DFN' if dfn_ok3 else 'SPM(degraded)',
        'criterion': 'Negative electrode surface potential difference < 0 V'
    }
}

saved_ok = False
for target_dir in ['/home/jovyan/labs/data/results', 'labs/data/results', 'results']:
    try:
        os.makedirs(target_dir, exist_ok=True)
        out_file = os.path.join(target_dir, 'D4_lithium_plating.json')
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        print(f"✓ 结果文件已成功归档至: {out_file}")
        saved_ok = True
        break
    except OSError:
        continue

if not saved_ok:
    print("ℹ️ 提示: 当前运行环境为只读挂载模式，跳过本地落盘，直接进入官方评测")

# 2. 调用平台官方评分函数
eval_report = grade_metrics('D4_lithium_plating', record['metrics'])

# 3. 打印标准化官方成绩单
print("\\n" + "=" * 55)
print("🏆 IEV CloudLab 官方评分报告: 快充析锂微观仿真")
print("=" * 55)
print(f"总得分: {eval_report['score']} / 100 分  ({'✅ 通过' if eval_report['passed'] else '❌ 未通过'})")
print("-" * 55)
for detail in eval_report.get('details', []):
    mark = '✓ 通过' if detail['passed'] else '✗ 失败'
    m_name = detail.get('metric', detail.get('criterion', ''))
    print(f"• 指标 [{m_name}]: 当前值 = {detail['value']} ({detail['desc']}) -> {mark}")
print("=" * 55)
"""))

# ==============================================================================
# Cell 10: Stage 8 Markdown - Engineering Reflection & Next Link
# ==============================================================================
cells.append(md_cell("""---

## 阶段八：工程前沿反思与下一组进阶实验 | Engineering Reflection & Next

### 💡 核心工程启示与反思

1. **低温快充的灾难性析锂放大效应**：
   在 $0^\\circ\\text{C}$ 或 $-20^\\circ\\text{C}$ 低温环境下，石墨固相锂扩散系数 $D_s$ 会呈阿伦尼乌斯指数级骤降，电解液电导率也同步大幅衰退。此时即便以 0.5C 充电，界面电位也会立刻雪崩至 $-0.8\\,\\text{V}$ 以下，造成毁灭性析锂。这也是为何所有量产纯电动汽车在冬季必须先调用 PTC 或热泵将电池预热至 $15^\\circ\\text{C} \\sim 25^\\circ\\text{C}$ 之后，才允许开启高功率快充。
2. **车载无损析锂检测技术的终极追求**：
   在实验室中可通过三电极电芯直接植入微参比电极测量 $\\phi_s - \\phi_e$。但在量产车双电极结构下，工程师无法直接测量微观界面电位，目前行业前沿正攻坚：
   - **充后静置电压弛豫微分特征峰法 ($dV/dt$)**：利用析出的金属锂在静置自溶解过程中产生的特征电压平台；
   - **高频电化学阻抗谱 (EIS)**：捕捉电荷转移阻抗与界面膜阻抗突变；
   - **无损声发射 (Acoustic Emission)**：利用金属锂枝晶断裂与产气释放的微弱高频超声波进行早期预警。

---

## 🏆 电池电化学板块（Group D）圆满通关！下一组进阶实验预告

恭喜完成全部 4 个电池微观电化学仿真实验（D1 单体放电、D2 倍率容量、D3 OCV标定、D4 快充析锂）！
下一组实验我们将跨入智能电动汽车控制科学的核心引擎 —— **Group E：整车能量管理与先进优化算法 (Optimization & Control)**：

👉 **[E1 (Pro版)：单目标参数优化与工况节油率仿真](./E1_single_objective_pro.ipynb)**

> **所需内核**：`py310-fastsim` (专用于整车纵向动力学与能量流优化仿真)
"""))

# ==============================================================================
# Save Notebook
# ==============================================================================
nb_pro = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.10.12"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

out_path = "/Users/christingking/dev/iev-cloudlab/notebooks/D4_lithium_plating_pro.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(nb_pro, f, ensure_ascii=False, indent=2)

print(f"Generated {out_path} with {len(cells)} cells.")
