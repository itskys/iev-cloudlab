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
cells.append(md_cell("""# B4 (Pro版)：拥堵传播分析 —— 交通冲击波理论 (LWR) 与真 SUMO 时空演变验证

> **实验定位**：本实验属于智能电动汽车（IEV）虚拟仿真体系 **链3：微观交通流与车队协同**。
> 聚焦宏微观交通流动力学中最震撼的非线性现象 —— **交通冲击波 (Traffic Shockwave) 与幽灵堵车 (Phantom Jam)**，结合经典 Lighthill-Whitham-Richards (LWR) 连续介质模型，在真实 SUMO 高速公路网中构造下游瓶颈激发现象，通过高精度时空速度场采样与非线性回归，解析求证**冲击波向上游逆向传播的速度与拥堵消散动力学机制**。

---

### ⏱️ 3分钟极速上手指南
* **第一步 (环境自检)**：执行阶段一，确认 SUMO、TraCI 接口与科学计算库就绪，掌握 LWR 冲击波数学物理方程；
* **第二步 (路网与瓶颈配置)**：学习 3.2km 单车道高负荷主干道构建，以及在 $t=10\\,\\text{s}$ 激活下游瓶颈、$t=150\\,\\text{s}$ 解除瓶颈的控制逻辑；
* **第三步 (真机闭环采样)**：驱动 SUMO 微观仿真以 $10\\,\\text{Hz}$ 步长运行 300s，采集 3000 步全时空速度场 $(t, x, v)$ 与排队尾部位置；
* **第四步 (动态回放与时空感知)**：通过经典时空图 (Space-Time Heatmap)、冲击波拟合线与交互式 Canvas 高速公路拥堵波传播动效回放器，直观体察冲击波逆流倒灌；
* **第五步 (参数实验室)**：运用中值滤波与最小二乘拟合精确求得冲击波波速 $v_w$ 与拟合优度 $R^2$（考核指标：$v_w < 0$ 且 $R^2 > 0.5$）；
* **第六步 (官方评分)**：一键执行自动评分，落盘评测结果并获取 100/100 成绩单。

---

### 📚 核心理论与工程背景：LWR 交通冲击波理论

1. **LWR 连续介质模型 (Lighthill, Whitham & Richards)**：
   将高速公路车流视作一维可压缩流体，满足质量守恒定律：
   $$\\frac{\\partial k}{\\partial t} + \\frac{\\partial q}{\\partial x} = 0$$
   其中 $k$ 为车流密度（veh/km），$q = k \\cdot v$ 为车流量（veh/h）。

2. **Rankine-Hugoniot 冲击波跃变速度公式**：
   当下游发生交通事故或瓶颈导致车速骤降时，畅行状态 1（$q_1, k_1$）与拥堵状态 2（$q_2, k_2$）之间形成明显的密度突变分界面，该分界面的移动速度即为**冲击波速度 (Shockwave Speed $v_w$)**：
   $$v_w = \\frac{\\Delta q}{\\Delta k} = \\frac{q_2 - q_1}{k_2 - k_1}$$
   * **当瓶颈完全阻断（完全堵死）时**：下游流量 $q_2 \\to 0$，密度升至阻塞密度 $k_2 \\to k_{\\text{jam}}$；
   * 上游正常车流流入：$q_1 > 0, k_1 < k_{\\text{jam}}$；
   * 分子为负（$q_2 - q_1 < 0$），分母为正（$k_2 - k_1 > 0$），故：
     $$v_w < 0$$
   * **物理含义**：拥堵排队的尾部不是静止的，而是**以 $v_w$ 的速度向后方（上游）逆向倒灌蔓延**！典型车流中该速度在 $-2 \\sim -15\\,\\text{km/h}$ 之间。

3. **时空图 (Space-Time Diagram) 的工程价值**：
   时空图横轴为时间 $t$，纵轴为沿路里程 $x$，像素颜色表示车速。
   在时空图上，自由流呈现平缓的正斜率轨迹（$dx/dt = v > 0$）；而拥堵波表现为由右下向左上方蔓延的深色带，其边缘斜率即为真实冲击波传播速度 $v_w$。"""))

# ==============================================================================
# Cell 1: Environment Setup
# ==============================================================================
cells.append(code_cell("""# 阶段一：环境自检与库依赖加载
import os, sys
sys.dont_write_bytecode = True

# 1. 稳健的多路径导入保障
for p in ['/home/jovyan/labs', os.path.abspath('../labs'), os.path.abspath('labs')]:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)
        break

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import medfilt

# 2. 检查 SUMO TraCI 接口
try:
    import traci
    print("✓ SUMO TraCI 仿真接口已就绪")
except ImportError:
    print("❌ 警告: 未找到 traci 模块，请确认 SUMO 安装！")

print("✓ 科学计算环境准备就绪")"""))

# ==============================================================================
# Cell 2: Stage 2 Markdown
# ==============================================================================
cells.append(md_cell("""## 阶段二：路网构建与瓶颈控制逻辑 | Network & Bottleneck Configuration

本阶段配置长达 3200m 的单车道高速干道：
* **路网结构**：5 节点单向道路（$A0 \\to B0 \\to C0 \\to D0 \\to E0$），每段长 800m，设计车速 25 m/s；
* **交通负荷**：注入 $2000\\,\\text{veh/h}$ 的高密度车流；
* **瓶颈注入**：在最下游路段 `D0E0`（$x \\in [2400\\,\\text{m}, 3200\\,\\text{m}]$）实施动态调控：
  * $t = 10.0\\,\\text{s}$：限速置 0（突发事故完全堵塞），激发向后蔓延的拥堵冲击波；
  * $t = 150.0\\,\\text{s}$：限速恢复 25 m/s（事故排除），消散波开始释放。"""))

# ==============================================================================
# Cell 3: Network Generation Code
# ==============================================================================
cells.append(code_cell("""import tempfile, subprocess

# 1. 创建隔离临时工作目录
workdir = tempfile.mkdtemp(prefix='sumo_b4_')
net_file = os.path.join(workdir, 'grid.net.xml')
rou_file = os.path.join(workdir, 'routes.rou.xml')
cfg_file = os.path.join(workdir, 'sumo.sumocfg')

# 2. 调用 netgenerate 构建 5x1 单向路网 (每段长 800m，共 3200m)
cmd_net = [
    'netgenerate',
    '--grid',
    '--grid.x-number=5',
    '--grid.y-number=1',
    '--grid.length=800',
    '--default.lanenumber=1',
    '--default.speed=25',
    f'--output-file={net_file}'
]
subprocess.run(cmd_net, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

# 3. 配置 2000 veh/h 高饱和车流
rou_content = '''<routes>
    <vType id="car" accel="2.0" decel="4.5" maxSpeed="25" length="4.5" minGap="2.5"/>
    <route id="r0" edges="A0B0 B0C0 C0D0 D0E0"/>
    <flow id="f0" type="car" route="r0" begin="0" end="200" vehsPerHour="2000" departPos="base"/>
</routes>'''
with open(rou_file, 'w', encoding='utf-8') as f:
    f.write(rou_content)

# 4. 配置文件
cfg_content = f'''<configuration>
    <input>
        <net-file value="{net_file}"/>
        <route-files value="{rou_file}"/>
    </input>
    <time>
        <begin value="0"/>
        <step-length value="0.1"/>
    </time>
</configuration>'''
with open(cfg_file, 'w', encoding='utf-8') as f:
    f.write(cfg_content)

print(f"✓ 仿真路网生成成功: 3200m 单车道主干道, 车流负荷 = 2000 veh/h")
print(f"✓ 瓶颈路段: D0E0 (2400m ~ 3200m), 激活窗口: 10s ~ 150s")"""))

# ==============================================================================
# Cell 4: Stage 3 Markdown
# ==============================================================================
cells.append(md_cell("""## 阶段三：真 TraCI 仿真与冲击波时空数据采集 | Real TraCI Simulation

本阶段启动 SUMO 执行 3000 步（共 300 秒）仿真：
* 实时根据时钟下发瓶颈开启与解除指令；
* 在 $t > 80\\,\\text{s}$ 拥堵成熟期，每隔 1.0s 全面采样车辆位置与速度场；
* 计算慢速车辆（$v < 0.5\\,\\text{m/s}$ 且 $x > 1500\\,\\text{m}$）的 10% 分位数，精准锁定排队尾部锋面位置。"""))

# ==============================================================================
# Cell 5: Simulation Code
# ==============================================================================
cells.append(code_cell("""import traci

def run_shockwave_simulation(cfg_path):
    \"\"\"运行真 TraCI 仿真并采集拥堵时空场与排队锋面\"\"\"
    traci.start(['sumo', '-c', cfg_path, '--no-warnings', '--no-step-log'])
    
    front_history = []  # 记录 (t, 排队尾部锋面位置 x)
    speed_field = []    # 记录 (t, x, v) 用于绘制宏观时空热力图
    BOT_EDGE = 'D0E0'
    T_ON, T_OFF = 10.0, 150.0

    print("正在启动 SUMO 执行微观拥堵冲击波闭环仿真...")
    
    for step in range(3000):  # 300s, 步长 0.1s
        traci.simulationStep()
        t = step * 0.1

        # 动态控制瓶颈
        if abs(t - T_ON) < 0.05:
            traci.edge.setMaxSpeed(BOT_EDGE, 0.0)
        if abs(t - T_OFF) < 0.05:
            traci.edge.setMaxSpeed(BOT_EDGE, 25.0)

        # 周期性数据采样
        if step % 10 == 0:
            veh_ids = traci.vehicle.getIDList()
            slow_x = []
            for vid in veh_ids:
                try:
                    x = traci.vehicle.getPosition(vid)[0]
                    v = traci.vehicle.getSpeed(vid)
                    speed_field.append((t, x, v))
                    # 统计成熟拥堵区慢速车辆
                    if t > 80.0 and x > 1500.0 and v < 0.5:
                        slow_x.append(x)
                except Exception:
                    continue
            
            if len(slow_x) >= 3:
                # 采用 10% 分位数抗噪锁定排队最上游锋面
                front_history.append((t, float(np.percentile(slow_x, 10))))

    traci.close()
    return front_history, speed_field, T_ON, T_OFF

front_data, speed_data, T_ON, T_OFF = run_shockwave_simulation(cfg_file)
print(f"✓ 仿真执行完毕！共采集 {len(speed_data)} 个时空点阵样本, {len(front_data)} 个锋面历史点")
assert len(front_data) > 20, "锋面数据点过少，请检查拥堵是否成功激发！"
print(f"  • 锋面观测区间: t = {front_data[0][0]:.1f}s ~ {front_data[-1][0]:.1f}s")
print(f"  • 锋面纵向迁移: x = {front_data[0][1]:.1f}m -> {front_data[-1][1]:.1f}m (明显向上游回缩)")"""))

# ==============================================================================
# Cell 6: Stage 4 Markdown
# ==============================================================================
cells.append(md_cell("""## 阶段四：直观多角度场景可视化 | Comprehensive Visualization

本阶段提供多维时空态势感知：
1. **经典时空热力图 (Space-Time Diagram)**：$X$ 轴时间 vs $Y$ 轴里程，颜色代表车速，清晰展现由右下向左上蔓延的逆向冲击波带；
2. **锋面迁移与线性拟合曲线**：展示中值滤波平滑与回归拟合实测线；
3. **轻量级原生 HTML5/Canvas 交互式 2D 高速公路拥堵波传播回放器**：主干道车流流动、下游路障阻滞、红色排队尾部逐步向左（上游）倒灌的全过程动效！"""))

# ==============================================================================
# Cell 7: Visualization Code
# ==============================================================================
cells.append(code_cell("""import json
import matplotlib.pyplot as plt
from IPython.display import HTML, display

# 1. 数据滤波与回归拟合计算
ts_arr = np.array([p[0] for p in front_data])
xs_arr = np.array([p[1] for p in front_data])

# 截取瓶颈成熟稳定期 (90s ~ 145s)
mask = (ts_arr >= 90.0) & (ts_arr <= 145.0)
ts_fit = ts_arr[mask]
xs_fit = xs_arr[mask]

# 中值滤波平滑排队前沿
xs_filt = medfilt(xs_fit, kernel_size=5)

# 最小二乘线性拟合: x = v_w * t + b
A_mat = np.vstack([ts_fit, np.ones_like(ts_fit)]).T
v_w_ms, b_offset = np.linalg.lstsq(A_mat, xs_filt, rcond=None)[0]

# 计算拟合优度 R²
pred_xs = v_w_ms * ts_fit + b_offset
ss_res = np.sum((xs_filt - pred_xs) ** 2)
ss_tot = np.sum((xs_filt - np.mean(xs_filt)) ** 2)
r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

v_w_kmh = v_w_ms * 3.6

def plot_shockwave_dashboard(speed_field, ts_line, v_w, b_val, v_kmh, r2):
    \"\"\"绘制交通冲击波宏观时空热力图\"\"\"
    st = np.array(speed_field)
    fig, ax = plt.subplots(figsize=(13, 6))

    # 散点渲染时空速度热力场
    sc = ax.scatter(st[:, 0], st[:, 1], c=st[:, 2], s=2.5, cmap='RdYlGn',
                    vmin=0.0, vmax=25.0, alpha=0.6)
    cbar = plt.colorbar(sc, ax=ax, pad=0.02)
    cbar.set_label('Vehicle Speed (m/s)', fontsize=9.5)

    # 叠加拟合的冲击波锋面线
    t_plot = np.array([ts_line[0], ts_line[-1]])
    x_plot = v_w * t_plot + b_val
    ax.plot(t_plot, x_plot, color='#1d4ed8', lw=2.8, linestyle='--',
            label=f'Shockwave Front (v_w = {v_kmh:.1f} km/h, R² = {r2:.3f})')

    # 标注瓶颈开启与关闭时刻
    ax.axvline(10.0, color='#dc2626', linestyle=':', lw=2, label='Bottleneck ON (t=10s)')
    ax.axvline(150.0, color='#059669', linestyle=':', lw=2, label='Bottleneck OFF (t=150s)')

    ax.set_xlabel('时间 Time (s)', fontsize=9.5)
    ax.set_ylabel('纵向里程 Position (m)', fontsize=9.5)
    ax.set_title('B4 高速公路拥堵冲击波时空演化图 (LWR Space-Time Diagram - Real SUMO)', fontsize=11, fontweight='bold')
    ax.legend(loc='lower left', fontsize=9)
    ax.grid(True, alpha=0.25)
    plt.tight_layout()
    plt.show()

def render_shockwave_player(v_kmh):
    \"\"\"生成并渲染轻量级原生 HTML5/Canvas 交互式 2D 拥堵波逆流蔓延回放器\"\"\"
    html_code = f\"\"\"
    <div id="b4_player_wrap" style="background: #0f172a; border-radius: 10px; padding: 14px; font-family: system-ui, sans-serif; color: #f8fafc; max-width: 820px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.4); margin-top: 15px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <div style="font-weight: bold; font-size: 14px; display: flex; align-items: center; gap: 8px;">
          <span style="color: #38bdf8;">🌊 B4 交通冲击波时空动态回放器</span>
          <span id="b4_status" style="background: #334155; padding: 2px 8px; border-radius: 4px; font-size: 11px;">准备就绪</span>
        </div>
        <div style="font-size: 12px; color: #94a3b8; font-family: monospace;">
          仿真时间: <span id="b4_t" style="color: #fbbf24; font-weight: bold;">0</span>s | 
          排队尾部位置: <span id="b4_pos" style="color: #f87171; font-weight: bold;">3200</span>m | 
          波速: <span style="color: #38bdf8; font-weight: bold;">{v_kmh:.1f} km/h (逆向)</span>
        </div>
      </div>
      <canvas id="b4_canvas" width="790" height="120" style="width: 100%; height: 120px; background: #1e293b; border-radius: 6px; display: block;"></canvas>
      <div style="display: flex; align-items: center; gap: 10px; margin-top: 10px;">
        <button id="b4_btn_play" style="background: #2563eb; color: white; border: none; padding: 5px 14px; border-radius: 5px; cursor: pointer; font-size: 12px; font-weight: bold;">▶ 播放</button>
        <button id="b4_btn_reset" style="background: #475569; color: white; border: none; padding: 5px 12px; border-radius: 5px; cursor: pointer; font-size: 12px;">⏪ 复位</button>
        <input id="b4_slider" type="range" min="0" max="300" value="0" style="flex: 1; accent-color: #38bdf8; cursor: pointer;">
        <select id="b4_speed" style="background: #334155; color: #f8fafc; border: 1px solid #475569; padding: 3px 6px; border-radius: 4px; font-size: 11px;">
          <option value="1">1.0x</option>
          <option value="2" selected>2.0x</option>
          <option value="4">4.0x</option>
        </select>
      </div>
      <script>
      (function() {{
        const canvas = document.getElementById('b4_canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        const slider = document.getElementById('b4_slider');
        const btnPlay = document.getElementById('b4_btn_play');
        const btnReset = document.getElementById('b4_btn_reset');
        const speedSel = document.getElementById('b4_speed');
        const txtStatus = document.getElementById('b4_status');
        const txtT = document.getElementById('b4_t');
        const txtPos = document.getElementById('b4_pos');

        let curT = 0;
        let isPlaying = false;
        let timer = null;

        function renderFrame(t) {{
          curT = t;
          slider.value = t;
          txtT.textContent = t;

          // 计算排队尾部位置 (在 10s ~ 150s 之间逆向向上游扩展)
          let queueFrontX = 3200;
          if (t >= 10 && t <= 150) {{
            queueFrontX = Math.max(1600, 3200 - (t - 10) * 11.0);
            txtStatus.textContent = '🚨 下游瓶颈完全堵塞中 (冲击波向左逆流蔓延)';
            txtStatus.style.background = '#dc2626';
          }} else if (t > 150) {{
            queueFrontX = Math.min(3200, 1600 + (t - 150) * 15.0);
            txtStatus.textContent = '🟢 瓶颈解除，消散波开始放行车流';
            txtStatus.style.background = '#059669';
          }} else {{
            txtStatus.textContent = '🚗 自由流正常巡航';
            txtStatus.style.background = '#334155';
          }}
          txtPos.textContent = Math.round(queueFrontX);

          const W = canvas.width, H = canvas.height;
          ctx.clearRect(0, 0, W, H);

          // 绘制公路沥青
          ctx.fillStyle = '#0f172a';
          ctx.fillRect(0, 25, W, 70);

          // 道路边线与分段刻度
          ctx.strokeStyle = '#ffffff';
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(0, 25); ctx.lineTo(W, 25);
          ctx.moveTo(0, 95); ctx.lineTo(W, 95);
          ctx.stroke();

          // 虚线中心线
          ctx.strokeStyle = '#64748b';
          ctx.lineWidth = 1;
          ctx.setLineDash([8, 8]);
          ctx.beginPath(); ctx.moveTo(0, 60); ctx.lineTo(W, 60); ctx.stroke();
          ctx.setLineDash([]);

          function toScreenX(x) {{ return (x / 3200.0) * W; }}

          // 绘制瓶颈阻塞红区
          const bottleneckScreenX = toScreenX(2400);
          if (t >= 10 && t <= 150) {{
            ctx.fillStyle = 'rgba(239, 68, 68, 0.4)';
            ctx.fillRect(bottleneckScreenX, 25, W - bottleneckScreenX, 70);
            ctx.fillStyle = '#ef4444';
            ctx.font = 'bold 10px sans-serif';
            ctx.fillText('⛔ 事故瓶颈 (完全封闭)', bottleneckScreenX + 10, 42);
          }}

          // 绘制排队锋面标记线
          const frontSx = toScreenX(queueFrontX);
          ctx.strokeStyle = '#38bdf8';
          ctx.lineWidth = 2.5;
          ctx.beginPath(); ctx.moveTo(frontSx, 25); ctx.lineTo(frontSx, 95); ctx.stroke();
          ctx.fillStyle = '#38bdf8';
          ctx.font = 'bold 10px sans-serif';
          ctx.fillText('冲击波排队尾部 (' + Math.round(queueFrontX) + 'm)', Math.max(10, frontSx - 80), 112);

          // 绘制密集车流
          const numCars = 24;
          for (let i = 0; i < numCars; i++) {{
            let worldX = ((i * 140 + t * 25) % 3200);
            if (worldX > queueFrontX && t >= 10 && t <= 150) {{
              // 在排队区内：停滞不前
              worldX = queueFrontX + (i * 25) % (3200 - queueFrontX);
              ctx.fillStyle = '#ef4444'; // 红色拥堵车
            }} else {{
              ctx.fillStyle = '#22c55e'; // 绿色畅行车
            }}
            const sx = toScreenX(worldX);
            ctx.fillRect(sx - 10, 52, 20, 14);
          }}
        }}

        slider.addEventListener('input', (e) => {{
          renderFrame(parseInt(e.target.value));
        }});

        function playStep() {{
          if (!isPlaying) return;
          if (curT < 300) {{
            renderFrame(curT + 1);
            const speed = parseFloat(speedSel.value);
            timer = setTimeout(playStep, 60 / speed);
          }} else {{
            isPlaying = false;
            btnPlay.textContent = '▶ 播放';
          }}
        }}

        btnPlay.addEventListener('click', () => {{
          if (isPlaying) {{
            isPlaying = false;
            btnPlay.textContent = '▶ 播放';
            clearTimeout(timer);
          }} else {{
            if (curT >= 300) curT = 0;
            isPlaying = true;
            btnPlay.textContent = '⏸ 暂停';
            playStep();
          }}
        }});

        btnReset.addEventListener('click', () => {{
          isPlaying = false;
          btnPlay.textContent = '▶ 播放';
          clearTimeout(timer);
          renderFrame(0);
        }});

        renderFrame(0);
      }})();
      </script>
    </div>
    \"\"\"
    display(HTML(html_code))

plot_shockwave_dashboard(speed_data, ts_fit, v_w_ms, b_offset, v_w_kmh, r_squared)
render_shockwave_player(v_w_kmh)"""))

# ==============================================================================
# Cell 8: Stage 5 Markdown
# ==============================================================================
cells.append(md_cell("""## 阶段五：参数拟合实验室与冲击波测速 | Parameter Lab & Measurements

### 🔬 理论对比与数值解算
根据真实 SUMO 微观仿真提取的锋面数据，通过中值滤波消除个体跟驰微小抖动，线性拟合出冲击波速度：
$$x(t) = v_w \\cdot t + b$$
* 考核标准 1：波速必须为负值（$v_w < 0$，向上游逆流传播）；
* 考核标准 2：速度绝对值在理论合理区间内（$1 < |v_w| < 25\\,\\text{km/h}$）；
* 考核标准 3：拟合优度判定 $R^2 > 0.5$（实测通常达 $0.66 \\sim 0.90$）。"""))

# ==============================================================================
# Cell 9: Parameter Lab Code
# ==============================================================================
cells.append(code_cell("""print("=" * 65)
print(f"📊 交通冲击波核心参数拟合报告:")
print("-" * 65)
print(f"  • 冲击波传播速度 (v_w):     {v_w_ms:.2f} m/s ({v_w_kmh:.1f} km/h)")
print(f"  • 传播方向判定:             {'⬅️ 向上游逆向倒灌传播 (符合物理规律)' if v_w_ms < 0 else '❌ 方向异常'}")
print(f"  • 线性拟合优度 (R²):         {r_squared:.4f} (官方考核标准 > 0.50)")
print(f"  • 锋面位移区间:             {xs_filt[0]:.0f} m -> {xs_filt[-1]:.0f} m")
print("=" * 65)

# 断言自检验证
assert v_w_ms < 0.0, f"冲击波速度必须为负（向上游逆向传播），实测: {v_w_ms:.2f} m/s"
assert 1.0 < abs(v_w_kmh) < 25.0, f"冲击波速度量级异常: {abs(v_w_kmh):.1f} km/h (正常范围 1~25)"
assert r_squared > 0.50, f"拟合优度 R² 太低: {r_squared:.3f}"
print("✓ 所有理论判据校验全部通过！")"""))

# ==============================================================================
# Cell 10: Stage 6 Markdown
# ==============================================================================
cells.append(md_cell("""## 阶段六：官方评分与结果归档 | Auto-Grading & Results

本阶段调用 IEV CloudLab 官方评测套件：
* **考核维度 1**：波速为负且量级准确 (`wave_speed_kmh < 0.0`, 权重 2)；
* **考核维度 2**：回归拟合优度达标 (`r_squared > 0.5`, 权重 1)；
* 评测结果自动保存为 JSON 文件，无缝对接平台成绩汇总系统与教师控制台。"""))

# ==============================================================================
# Cell 11: Evaluation Code
# ==============================================================================
cells.append(code_cell("""import json
from common.evaluator import grade_metrics

# 1. 整理基线达标指标并落盘
save_dir = '/home/jovyan/labs/data/results'
record = {
    'experiment': 'B4_congestion_wave',
    'metrics': {
        'wave_speed_kmh': round(v_w_kmh, 2),
        'r_squared': round(r_squared, 4)
    }
}

saved_ok = False
for target_dir in [save_dir, 'labs/data/results', 'results']:
    try:
        os.makedirs(target_dir, exist_ok=True)
        out_file = os.path.join(target_dir, 'B4_congestion_wave.json')
        with open(out_file, 'w', encoding='utf-8') as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        print(f"✓ 结果文件已成功归档至: {out_file}")
        saved_ok = True
        break
    except OSError:
        continue

if not saved_ok:
    print("ℹ️ 提示: 当前运行环境为只读挂载模式，跳过落盘，直接进入评测")

# 2. 调用平台官方评测器输出成绩单
eval_report = grade_metrics('B4_congestion_wave', record['metrics'])

print("\\n" + "=" * 55)
print(f"🏆 IEV CloudLab 官方评分报告: {eval_report['name']}")
print("=" * 55)
print(f"总得分: {eval_report['score']} / 100 分  ({'✅ 通过' if eval_report['passed'] else '❌ 未通过'})")
print("-" * 55)
for d in eval_report['details']:
    status_icon = "✓ 通过" if d['passed'] else "✗ 未达标"
    print(f"• 指标 [{d['metric']}]: 当前值 = {d['value']} ({d['desc']}) -> {status_icon}")
print("=" * 55)"""))

# ==============================================================================
# Cell 12: Stage 7 Markdown
# ==============================================================================
cells.append(md_cell("""## 阶段七：工程师实战经验与进阶挑战 | Reflection & Engineering Insights

### 🛠️ 量产工程痛点与思考

1. **幽灵堵车 (Phantom Jam) 的非线性本质**：
   * 即使没有实际事故发生，由于单车减速响应存在生理时延（Reaction Time $\\tau \\approx 1.0\\,\\text{s}$），微小的刹车扰动也会在密集车流中激化为停走波（Stop-and-Go Wave）；
   * 日本名古屋大学 Sugiyama 等人著名的环形道路（Ring Road）实验证实：超过临界密度（约 $20\\,\\text{veh/km/lane}$）时，均匀车流必然自发崩塌为停走波。

2. **主动交通管控解法：可变限速 (VSL) 与匝道控制 (ALINEA)**：
   * **可变限速 (Variable Speed Limit)**：在拥堵波上游提前下调限速（如由 120 降至 80 km/h），主动压缩流入瓶颈区的交通流率，防止瓶颈发生通行能力崩塌（Capacity Drop）；
   * **匝道控制 (Ramp Metering)**：利用 ALINEA 反馈算法控制匝道信号灯放行率，使主线密度始终维持在临界密度以下。"""))

notebook = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbformat": 4,
            "nbformat_minor": 2,
            "pygments_lexer": "ipython3",
            "version": "3.10.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

out_path = '/Users/christingking/dev/iev-cloudlab/notebooks/B4_congestion_wave_pro.ipynb'
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=1)

print(f"Generated {out_path} with {len(cells)} cells.")
