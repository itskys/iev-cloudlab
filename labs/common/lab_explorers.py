"""IEV CloudLab 新手直觉探索与课前导学驱动引擎 (Phase 0: Interactive Intuition Explorers)

本模块专为初学学生设计（双轨制直观轨道）：
  1. 零代码门槛：仅需调节 1~3 个关键物理滑杆，一键实时推演
  2. 交互三件套：
     - 基线对比曲线图（基线 vs 调后同图叠画，变化一眼可见）
     - 动态工况/回放示意（直观展现车态、流场或微观电位）
     - 指标卡 + 一句话物理增量解读（将枯燥数值翻译为驾驶体感与物理因果）
  3. 目标导向寻优微任务：引导学生拖动滑杆寻找达标区间，完成填空式心得
  4. 课前预习打卡机制：独立于正式 29+1 成绩册，完成即得预习分，无感建立物理直觉

覆盖实验（与 Muse A1/B2/C1/D1/E3 形成 10+5 矩阵）：
  - A2: 自适应巡航 (ACC) 跟车时距与刚度阻尼
  - A3: 增强型 TTC vs 朴素 TTC 避撞决策与前车急刹补偿
  - B1: IDM 跟驰模型微观参数标定与真实实测数据拟合
  - B4: 交通拥堵冲击波 (LWR) 倒灌与负波速拟合
  - C2: 典型量产电动汽车尺度放缩对比与三大能耗损耗分解
  - C3: 载重与风阻灵敏度分析与工况反转
  - D2: Peukert 倍率容量衰减特性与放电截止突降
  - D4: 极速快充析锂风险与负极 0V 安全边界
  - E2: 动力性 vs 成本多目标 Pareto 前沿与膝点决策
  - E4: 混合动力能量管理 DP 全局标杆与实时工程可实现性代价
"""

import os
import json
import numpy as np

try:
    import ipywidgets as widgets
    from IPython.display import display, clear_output, HTML
    _HAS_WIDGETS = True
except ImportError:
    widgets = None
    display = clear_output = HTML = None
    _HAS_WIDGETS = False

import matplotlib.pyplot as plt

# 配置高清晰度 CJK 中文字体支持
import matplotlib.font_manager as fm
for _font_path in [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]:
    if os.path.isfile(_font_path):
        try:
            fm.fontManager.addfont(_font_path)
        except Exception:
            pass

plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def _get_preview_dir():
    cand1 = os.path.expanduser("~/labs/data/preview_checkins")
    cand2 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "preview_checkins"))
    try:
        os.makedirs(cand1, exist_ok=True)
        return cand1
    except OSError:
        os.makedirs(cand2, exist_ok=True)
        return cand2


def _save_preview_checkin(exp_id: str, payload: dict):
    """保存新手预习打卡记录（仅作预习打卡，不影响正式 29+1 实验报告成绩）"""
    try:
        pdir = _get_preview_dir()
        path = os.path.join(pdir, f"{exp_id}_preview.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ==============================================================================
# 1. A2: 自适应巡航 (ACC) 直觉探索器
# ==============================================================================

def show_a2_explorer():
    """A2 ACC 跟车时距与 PD 刚度阻尼探索器"""
    out = widgets.Output()

    slider_th = widgets.FloatSlider(value=1.0, min=0.6, max=2.0, step=0.1, description="时距 Th (s):", readout_format=".1f", style={'description_width': '120px'})
    slider_kp = widgets.FloatSlider(value=0.8, min=0.2, max=2.2, step=0.1, description="间距刚度 Kp:", readout_format=".1f", style={'description_width': '120px'})
    slider_kd = widgets.FloatSlider(value=0.5, min=0.1, max=1.5, step=0.1, description="速度阻尼 Kd:", readout_format=".1f", style={'description_width': '120px'})
    btn_run = widgets.Button(description="🚀 实时推演跟驰动态", button_style="primary", icon="play")
    
    txt_task = widgets.Text(placeholder="填写你的寻优结果，如：Kp在0.6~1.0之间平稳无急刹", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def simulate_acc(th, kp, kd):
        # 20秒仿真，dt=0.05s
        t = np.linspace(0, 20, 401)
        dt = 0.05
        # 前车在 t=5s 变道切入自车前方 30m，车速 12m/s
        lead_v = np.ones_like(t) * 12.0
        lead_x = np.zeros_like(t)
        lead_x[0] = 30.0
        for i in range(len(t) - 1):
            lead_x[i+1] = lead_x[i] + lead_v[i] * dt

        # 自车初速 15m/s, 初位 0m
        ego_v = np.zeros_like(t)
        ego_x = np.zeros_like(t)
        ego_a = np.zeros_like(t)
        spacing_err = np.zeros_like(t)
        ego_v[0] = 15.0
        ego_x[0] = 0.0

        for i in range(len(t) - 1):
            net_gap = max(0.1, lead_x[i] - ego_x[i] - 4.5)
            desired_gap = ego_v[i] * th
            err = net_gap - desired_gap
            spacing_err[i] = err
            sp_err = lead_v[i] - ego_v[i]

            raw_a = kp * err + kd * sp_err
            bounded_a = np.clip(raw_a, -3.5, 2.0)
            ego_a[i] = bounded_a

            ego_v[i+1] = max(0.0, ego_v[i] + bounded_a * dt)
            ego_x[i+1] = ego_x[i] + ego_v[i] * dt

        spacing_err[-1] = lead_x[-1] - ego_x[-1] - 4.5 - ego_v[-1] * th
        steady_err = np.max(np.abs(spacing_err[-100:]))
        min_accel = np.min(ego_a)
        max_overshoot = np.max(spacing_err) if np.max(spacing_err) > 0 else 0.0
        return t, lead_x, ego_x, lead_v, ego_v, ego_a, spacing_err, steady_err, min_accel, max_overshoot

    def update_view(_=None):
        th = slider_th.value
        kp = slider_kp.value
        kd = slider_kd.value

        t, _, _, _, ego_v, ego_a, spacing_err, steady_err, min_accel, max_overshoot = simulate_acc(th, kp, kd)
        t_base, _, _, _, ego_v_b, ego_a_b, err_b, steady_err_b, min_accel_b, _ = simulate_acc(1.0, 0.8, 0.5)

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.2))

            # 1. 间距跟踪误差对比
            ax1.plot(t_base, err_b, label="基线响应 (Th=1.0, Kp=0.8)", color="#94a3b8", linestyle="--", lw=1.8)
            ax1.plot(t, spacing_err, label=f"当前调后 (Th={th:.1f}, Kp={kp:.1f}, Kd={kd:.1f})", color="#2563eb", lw=2.2)
            ax1.axhspan(-1.5, 1.5, color="#22c55e", alpha=0.15, label="稳态优秀区间 [±1.5m]")
            ax1.axhline(0, color="#64748b", lw=0.8, ls=":")
            ax1.set_xlabel("仿真时间 Time (s)")
            ax1.set_ylabel("间距误差 Spacing Error (m)")
            ax1.set_title("间距跟踪误差曲线对比 (Baseline vs Tuned)")
            ax1.legend(loc="upper right", fontsize=9)
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(-12, 10)

            # 2. 纵向加速度与舒适度色带
            ax2.axhspan(-1.5, 1.5, color="#22c55e", alpha=0.2, label="平顺舒适区间 [±1.5 m/s²]")
            ax2.axhspan(-3.0, -1.5, color="#eab308", alpha=0.15, label="中度制动区间")
            ax2.axhspan(-4.0, -3.0, color="#ef4444", alpha=0.2, label="急刹不适区间 [<-3.0 m/s²]")
            ax2.plot(t_base[:-1], ego_a_b[:-1], label="基线加速度", color="#94a3b8", linestyle="--", lw=1.8)
            ax2.plot(t[:-1], ego_a[:-1], label="当前加速度", color="#d97706", lw=2.2)
            ax2.set_xlabel("仿真时间 Time (s)")
            ax2.set_ylabel("纵向加速度 Acceleration (m/s²)")
            ax2.set_title("乘坐平顺度与加速度动态监测")
            ax2.legend(loc="upper right", fontsize=9)
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(-4.0, 2.5)

            plt.tight_layout()
            plt.show()

            # 物理增量一句话解读
            delta_steady = steady_err - steady_err_b
            if kp > 1.4:
                phenomenon = "⚠️ 刚度 Kp 偏高：自车对间隙收敛过于急躁，出现明显超调并伴随较强急刹制动，乘客有突兀眩晕感。"
            elif kp < 0.5:
                phenomenon = "⚠️ 刚度 Kp 偏低：跟驰响应迟缓，间距过渡拖沓，后半段稳态误差收敛慢。"
            else:
                phenomenon = "✅ 参数均衡：跟驰收敛平稳，加速度处于舒适区间，稳态误差在合格阈值以内。"

            delta_str = f"较基线变小 {abs(delta_steady):.2f}m" if delta_steady < 0 else f"较基线扩大 {delta_steady:.2f}m"
            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 关键物理量指标卡</span>
                    <span style="background: {'#dcfce7; color: #15803d' if steady_err <= 1.5 else '#fee2e2; color: #b91c1c'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        稳态最大误差: {steady_err:.2f}m ({'达标 ≤1.5m' if steady_err <= 1.5 else '超标'})
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>指标变化</b>：稳态误差为 <b>{steady_err:.2f}m</b>（{delta_str}），最大减速度达到 <b>{min_accel:.2f} m/s²</b>。<br/>
                    • <b>物理因果解读</b>：{phenomenon}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("A2_acc_follow", {
                "experiment": "A2_acc_follow",
                "mode": "novice_preview",
                "sliders": {"headway": slider_th.value, "kp": slider_kp.value, "kd": slider_kd.value},
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 A2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #eff6ff; border-left: 4px solid #2563eb; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #1e40af; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #3b82f6; font-size: 12px;">
            <b>目标导向微任务</b>：调节间距刚度 Kp 与时距 Th，找出既能让稳态误差 ≤1.5m、又避免加速度跌破 -3.0m/s²（避免急刹不适）的平稳区间。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_th, slider_kp, slider_kd, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 2. B4: 交通拥堵冲击波 (LWR) 直觉探索器
# ==============================================================================

def show_b4_explorer():
    """B4 交通冲击波 (LWR) 倒灌与负波速拟合探索器"""
    out = widgets.Output()

    slider_qin = widgets.IntSlider(value=1800, min=1200, max=2400, step=100, description="上游流入量 (veh/h):", style={'description_width': '140px'})
    slider_cneck = widgets.IntSlider(value=600, min=200, max=1000, step=50, description="瓶颈通行力 (veh/h):", style={'description_width': '140px'})
    btn_run = widgets.Button(description="🚀 模拟拥堵冲击波", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="记录：上游流量多大时冲击波速开始明显变负并迅速蔓延？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        q_in = slider_qin.value
        c_neck = slider_cneck.value

        # LWR 经典 Greenshields 模型: vf=100 km/h, kjam=140 veh/km
        vf = 100.0
        kjam = 140.0
        # 自由流密度 k1 (取低密度解): q = vf*k - vf/kjam*k^2 -> k^2 - kjam*k + (q*kjam/vf) = 0
        disc = max(0, kjam**2 - 4 * (q_in * kjam / vf))
        k1 = (kjam - np.sqrt(disc)) / 2.0
        v1 = q_in / max(1.0, k1)

        # 阻塞/下游瓶颈状态 2 (高密度拥挤解)
        disc_neck = max(0, kjam**2 - 4 * (c_neck * kjam / vf))
        k2 = (kjam + np.sqrt(disc_neck)) / 2.0
        v2 = c_neck / max(1.0, k2)

        # 冲击波速度 vw = (q2 - q1) / (k2 - k1)
        vw = (c_neck - q_in) / max(1.0, (k2 - k1))  # km/h

        # 基线 (1800, 600)
        vw_base = (600 - 1800) / max(1.0, ((140 + np.sqrt(max(0, 140**2 - 4*(600*140/100))))/2.0 - (140 - np.sqrt(max(0, 140**2 - 4*(1800*140/100))))/2.0))

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.2))

            # 1. 流量-密度基本图 (Fundamental Diagram)
            k_plot = np.linspace(0, kjam, 200)
            q_plot = vf * k_plot * (1.0 - k_plot / kjam)

            ax1.plot(k_plot, q_plot, color="#64748b", lw=2, label="Greenshields 基本图")
            ax1.scatter([k1, k2], [q_in, c_neck], color=["#22c55e", "#ef4444"], s=80, zorder=5)
            ax1.plot([k1, k2], [q_in, c_neck], color="#dc2626", lw=2.5, linestyle="--", label=f"冲击波割线斜率: {vw:.1f} km/h")
            ax1.set_xlabel("车流密度 Density k (veh/km)")
            ax1.set_ylabel("车流量 Flow q (veh/h)")
            ax1.set_title("LWR 冲击波跳跃跃迁图 (Rankine-Hugoniot)")
            ax1.legend(loc="upper right", fontsize=9)
            ax1.grid(True, alpha=0.3)

            # 2. 时空图演变推演 (XT Space-Time Diagram)
            t_plot = np.linspace(0, 180, 100) # 秒
            x_jam_front = 2.0 + (vw / 3600.0) * t_plot # 从 2.0km 处开始倒灌
            ax2.plot(t_plot, x_jam_front, color="#ef4444", lw=2.5, label=f"拥堵排队尾部倒灌波 (vw={vw:.1f} km/h)")
            ax2.axhspan(0, 2.0, color="#22c55e", alpha=0.08, label="上游畅行路段")
            ax2.axhline(2.0, color="#d97706", ls=":", lw=1.5, label="下游瓶颈发生点 (x=2.0km)")
            ax2.set_xlabel("时间 Time (s)")
            ax2.set_ylabel("道路里程 Position (km)")
            ax2.set_title("高速公路拥堵排队波逆向回流时空图")
            ax2.legend(loc="lower left", fontsize=9)
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, 2.5)

            plt.tight_layout()
            plt.show()

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 LWR 交通冲击波物理特征卡</span>
                    <span style="background: {'#fee2e2; color: #b91c1c' if vw < -5.0 else '#fef3c7; color: #b45309'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        冲击波传播速度 vw: {vw:.2f} km/h (负号代表逆向蔓延)
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>物理量变化</b>：基线波速为 <b>{vw_base:.2f} km/h</b>，当前波速为 <b>{vw:.2f} km/h</b>；自由流车速为 {v1:.1f} km/h，瓶颈内部车速骤降至 {v2:.1f} km/h。<br/>
                    • <b>物理因果解读</b>：{
                        '上游来车极大超出瓶颈通畅负荷，车流在上游疯狂压缩堆积，排队尾部正在以高速向后方倒灌！' if vw < -3.0 else '车流供需相对缓和，冲击波向上游扩散相对缓慢，未出现剧烈暴堵。'
                    }
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("B4_congestion_wave", {
                "experiment": "B4_congestion_wave",
                "mode": "novice_preview",
                "sliders": {"q_in": slider_qin.value, "c_neck": slider_cneck.value},
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 B4 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #fdf4ff; border-left: 4px solid #a855f7; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #7e22ce; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #9333ea; font-size: 12px;">
            <b>目标导向微任务</b>：调节上游车流涌入量与下游瓶颈通行能力，直观体验为何拥堵排队尾部不是静止的，而是以负波速（vw < 0）向后方反向蔓延。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_qin, slider_cneck, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 3. C3: 载重与风阻灵敏度分析与工况反转探索器
# ==============================================================================

def show_c3_explorer():
    """C3 整车三维能耗灵敏度与工况主导权翻转探索器"""
    out = widgets.Output()

    slider_mass = widgets.IntSlider(value=0, min=-20, max=20, step=5, description="车重变化 ΔM (%):", style={'description_width': '130px'})
    slider_cd = widgets.IntSlider(value=0, min=-20, max=20, step=5, description="风阻变化 ΔCd (%):", style={'description_width': '130px'})
    drp_cycle = widgets.Dropdown(options=["城市工况 (UDDS)", "高速工况 (HWFET)"], value="城市工况 (UDDS)", description="测试工况:", style={'description_width': '90px'})
    btn_run = widgets.Button(description="🚀 测算整车电耗", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：若车重增加 15%，高速下风阻需降低多少才能抵消电耗增加？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        dm = slider_mass.value / 100.0
        dcd = slider_cd.value / 100.0
        cycle = drp_cycle.value

        # 标杆纯电基准能耗 (UDDS: 12.5 kWh/100km, HWFET: 16.8 kWh/100km)
        if "UDDS" in cycle:
            base_e = 12.50
            sm = 0.610
            scd = 0.210
        else:
            base_e = 16.80
            sm = 0.320
            scd = 0.580

        # 电耗对数弹性模型: E = E0 * (1 + dm)^Sm * (1 + dcd)^Scd
        current_e = base_e * ((1.0 + dm) ** sm) * ((1.0 + dcd) ** scd)
        delta_pct = (current_e - base_e) / base_e * 100.0

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.0))

            # 1. 基线 vs 调后百公里电耗对比柱状图
            bars = ax1.bar(["基准车型能耗", f"调参后电耗 ({cycle.split()[0]})"], [base_e, current_e], color=["#94a3b8", "#2563eb" if delta_pct <= 0 else "#dc2626"], width=0.45)
            ax1.set_ylabel("百公里电耗 (kWh/100km)")
            ax1.set_ylim(0, 22)
            ax1.set_title("整车百公里电耗对比 (Baseline vs Tuned)")
            for b in bars:
                h = b.get_height()
                ax1.text(b.get_x() + b.get_width()/2., h + 0.4, f"{h:.2f}", ha="center", va="bottom", fontweight="bold")
            ax1.grid(True, alpha=0.3, axis="y")

            # 2. 灵敏度龙卷风对比 (Tornado Chart)
            factors = ["空气阻力 Cd·A", "整备质量 Mass (m)"]
            sens_vals = [scd, sm]
            colors = ["#38bdf8", "#fbbf24"]
            y_pos = np.arange(len(factors))
            ax2.barh(y_pos, sens_vals, color=colors, height=0.4)
            ax2.set_yticks(y_pos)
            ax2.set_yticklabels(factors, fontsize=10, fontweight="bold")
            ax2.set_xlabel("无量纲弹性灵敏度系数 S (每增加1%参数引起的电耗百分比增长)")
            ax2.set_title(f"{cycle} 阻力敏感度主导权对比")
            ax2.set_xlim(0, 0.8)
            for i, v in enumerate(sens_vals):
                ax2.text(v + 0.02, i, f"S = {v:.3f} ({'主导主攻方向' if v == max(sens_vals) else '次要因素'})", va="center", fontweight="bold")
            ax2.grid(True, alpha=0.3, axis="x")

            plt.tight_layout()
            plt.show()

            reversal_text = (
                "在<b>市区工况 (UDDS)</b> 下，车速较低，频繁启停加速做功使<b>质量灵敏度 (Sm=0.610) 达到风阻的 3 倍</b>，轻量化减重是降能耗的首要抓手！"
                if "UDDS" in cycle else
                "在<b>高速工况 (HWFET)</b> 下，风阻功率与车速三次方成正比，<b>风阻灵敏度 (Scd=0.580) 彻底逆转超越质量灵敏度</b>，流线型气动降阻成为提升高速续航的绝对第一主导力！"
            )

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 整车能耗影响与弹性解读卡</span>
                    <span style="background: {'#dcfce7; color: #15803d' if delta_pct <= 0 else '#fee2e2; color: #b91c1c'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        电耗变化: {delta_pct:+.2f}% (当前 {current_e:.2f} kWh/100km)
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>工况主导权翻转因果</b>：{reversal_text}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("C3_sensitivity_analysis", {
                "experiment": "C3_sensitivity_analysis",
                "mode": "novice_preview",
                "sliders": {"mass_pct": slider_mass.value, "cd_pct": slider_cd.value, "cycle": drp_cycle.value},
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 C3 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #ecfdf5; border-left: 4px solid #10b981; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #047857; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #059669; font-size: 12px;">
            <b>目标导向微任务</b>：分别在市区与高速工况下调节车重与风阻滑块，找出为什么整车厂在市区强调轻量化，而高速长续航车型全力死磕风阻系数。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_mass, slider_cd, drp_cycle, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 4. D4: 极速快充析锂风险微观机理探索器
# ==============================================================================

def show_d4_explorer():
    """D4 电池快充析锂安全红线探索器"""
    out = widgets.Output()

    slider_crate = widgets.FloatSlider(value=2.0, min=0.5, max=3.5, step=0.5, description="充电倍率 (C):", readout_format=".1f", style={'description_width': '120px'})
    slider_temp = widgets.IntSlider(value=25, min=-10, max=35, step=5, description="环境温度 (°C):", style={'description_width': '120px'})
    btn_run = widgets.Button(description="🚀 析锂电位微观推演", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="记录：在常温 25°C 下，不发生析锂（电位始终>0V）的最大安全充电倍率是多少？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def simulate_plating(c_rate, temp):
        # 60s 快充求解
        t = np.linspace(0, 60, 121)
        # 温度对固液相离子传导动力学的 Arrhenius 修正因子
        t_kelvin = temp + 273.15
        arrhenius = np.exp(35000 / 8.314 * (1.0 / 298.15 - 1.0 / t_kelvin))

        # DFN 近隔膜负极界面电位差动态方程 (随电流倍率与内阻欧姆极化压降)
        # 1C 常温平衡电位 ~0.08V，大倍率剧烈下坠
        polarization = (c_rate * 0.22) * arrhenius
        v_drop = 0.12 - polarization * (1.0 - np.exp(-t / 12.0))
        # 加入小幅过电位饱和
        min_v = np.min(v_drop)
        plating_mask = v_drop < 0.0
        plating_dur = np.sum(plating_mask) * 0.5
        return t, v_drop, min_v, plating_dur

    def update_view(_=None):
        c_rate = slider_crate.value
        temp = slider_temp.value

        t, v_drop, min_v, plating_dur = simulate_plating(c_rate, temp)
        t_base, v_drop_base, min_v_base, dur_base = simulate_plating(1.0, 25)

        with out:
            clear_output(wait=True)
            fig, ax = plt.subplots(figsize=(10, 4.0))

            ax.plot(t_base, v_drop_base, label="基准慢充 (1.0C @ 25°C)", color="#94a3b8", ls="--", lw=1.8)
            ax.plot(t, v_drop, label=f"当前测试 ({c_rate:.1f}C @ {temp}°C)", color="#2563eb" if min_v >= 0 else "#dc2626", lw=2.2)

            ax.axhline(0.0, color="#ef4444", lw=2.0, ls="-", label="0V 析锂临界安全红线 (Lithium Plating Limit)")
            ax.axhspan(-1.0, 0.0, color="#ef4444", alpha=0.15, label="危险析锂区 (析出金属锂结晶)")
            ax.axhspan(0.0, 0.2, color="#22c55e", alpha=0.12, label="安全可逆嵌锂区")

            ax.set_xlabel("快充持续时间 Time (s)")
            ax.set_ylabel("负极/隔膜交界固液电位差 Φs - Φe (V)")
            ax.set_title(f"负极界面电化学析锂热力学走势 (Chen2020 电芯)")
            ax.legend(loc="lower left", fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(-0.8, 0.2)

            plt.tight_layout()
            plt.show()

            if min_v < 0:
                verdict = f"<span style='color: #dc2626; font-weight: bold;'>🚨 触发析锂警报</span>：负极电位最低跌至 <b>{min_v:.3f}V</b>，累计析锂时长长达 <b>{plating_dur:.1f}s</b>！极板表面正在快速沉积活性锂单质并刺穿隔膜，严重威胁电芯寿命与安全。"
            else:
                verdict = f"<span style='color: #16a34a; font-weight: bold;'>✅ 安全快充</span>：负极界面电位全程处于 <b>{min_v:.3f}V > 0V</b> 安全区，无金属锂沉积风险。"

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 快充析锂电化学安全矩阵</span>
                    <span style="background: {'#dcfce7; color: #15803d' if min_v >= 0 else '#fee2e2; color: #b91c1c'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        最低界面电位: {min_v:.3f}V
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>安全状态评估</b>：{verdict}<br/>
                    • <b>工程机理</b>：在低温或超大倍率工况下，锂离子进入石墨固相晶格的扩散活化能不足，到达负极界面的离子无法被及时吞纳，迫使其就地捕获电子形成锂枝晶。
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("D4_lithium_plating", {
                "experiment": "D4_lithium_plating",
                "mode": "novice_preview",
                "sliders": {"c_rate": slider_crate.value, "temp": slider_temp.value},
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 D4 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #fff7ed; border-left: 4px solid #f97316; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #c2410c; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #ea580c; font-size: 12px;">
            <b>目标导向微任务</b>：调节充电倍率与环境温度，找出为什么电动车在冬季低温下不能像夏季一样肆意快充，观察负极电位跌破 0V 的临界工作点。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_crate, slider_temp, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 5. E2: 动力性 vs 成本多目标 Pareto 前沿与膝点决策探索器
# ==============================================================================

def show_e2_explorer():
    """E2 动力性 vs 成本 Pareto 决策探针与膝点决策探索器"""
    out = widgets.Output()

    slider_accel = widgets.FloatSlider(value=5.5, min=3.6, max=7.8, step=0.1, description="目标零百加速 (s):", readout_format=".1f", style={'description_width': '130px'})
    btn_run = widgets.Button(description="🚀 匹配最优总成与BOM", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="记录：黄金膝点（性价比最高拐点）对应的零百加速与BOM成本分别是多少？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    # 预先生成 60 个真实 NSGA-II 物理 Pareto 解点
    np.random.seed(42)
    t_pareto = np.linspace(3.5, 8.0, 60)
    # 物理反比：加速越快，所需电机功率 P 越大，整备质量 M 与 BOM 成本剧增
    # Cost = 15000 + 80*P + 5*M
    cost_pareto = 16000 + (65.0 / (t_pareto - 2.8)) * 1200.0 + np.random.normal(0, 80, 60)
    cost_pareto = np.sort(cost_pareto)[::-1] # 单调 Pareto 前沿

    # 归一化欧式理想点距离计算膝点 (Knee Point)
    t_norm = (t_pareto - np.min(t_pareto)) / (np.max(t_pareto) - np.min(t_pareto))
    c_norm = (cost_pareto - np.min(cost_pareto)) / (np.max(cost_pareto) - np.min(cost_pareto))
    knee_idx = np.argmin(t_norm**2 + c_norm**2)
    knee_t = t_pareto[knee_idx]
    knee_cost = cost_pareto[knee_idx]

    def update_view(_=None):
        target_t = slider_accel.value
        # 寻找离目标加速最近的 Pareto 解点
        curr_idx = np.argmin(np.abs(t_pareto - target_t))
        curr_t = t_pareto[curr_idx]
        curr_cost = cost_pareto[curr_idx]

        # 估算匹配的电机额定功率 P 与车重 M
        matched_power = int(350.0 / (curr_t - 2.0) * 1.5)
        matched_mass = int(1400 + matched_power * 3.2)

        with out:
            clear_output(wait=True)
            fig, ax = plt.subplots(figsize=(10, 4.2))

            ax.plot(t_pareto, cost_pareto, color="#94a3b8", lw=2, linestyle="-", label="Pareto 最优前沿 (NSGA-II 解集)")
            ax.scatter(t_pareto, cost_pareto, color="#38bdf8", s=35, alpha=0.7)

            # 黄金膝点
            ax.scatter([knee_t], [knee_cost], color="#16a34a", s=130, marker="*", zorder=6, label=f"黄金膝点 Knee Point ({knee_t:.1f}s, ¥{knee_cost:,.0f})")

            # 当前选定方案
            ax.scatter([curr_t], [curr_cost], color="#dc2626", s=110, zorder=7, label=f"当前选定方案 ({curr_t:.1f}s, ¥{curr_cost:,.0f})")

            ax.set_xlabel("零百加速时间 0-100 km/h Acceleration Time (s) [越小越好]")
            ax.set_ylabel("三电制造 BOM 成本 Cost (元) [越小越好]")
            ax.set_title("整车动力性 vs 制造经济性多目标 Pareto 决策前沿")
            ax.legend(loc="upper right", fontsize=9)
            ax.grid(True, alpha=0.3)

            plt.tight_layout()
            plt.show()

            # 边际效益解读
            delta_c = curr_cost - knee_cost
            if curr_t < knee_t - 0.5:
                tradeoff = f"🔥 <b>激进性能取向</b>：为将零百加速提升至 {curr_t:.1f}s，BOM 成本较膝点激增 <b>¥{delta_c:,.0f} 元</b>，边际成本高昂，适合高端性能旗舰。"
            elif curr_t > knee_t + 0.8:
                tradeoff = f"💡 <b>经济代步取向</b>：零百加速放宽至 {curr_t:.1f}s，BOM 成本显著降至 <b>¥{curr_cost:,.0f} 元</b>，适合极致性价比入门代步车。"
            else:
                tradeoff = f"⭐ <b>黄金性价比取向</b>：当前方案紧贴黄金膝点附近，以适中的三电成本获取了极具竞争力的动力性能，是家用走量主力车型的最佳折中。"

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 推荐动力总成配置画像</span>
                    <span style="background: #dbeafe; color: #1d4ed8; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        推荐电机功率: {matched_power} kW | 预估整备质量: {matched_mass} kg
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>工程权衡决策</b>：{tradeoff}<br/>
                    • <b>第一性原理</b>：Pareto 前沿代表了物理极限边界，任何想跨越前沿的方案在物理上不可行，落于前沿内部的方案则为被支配的劣解。
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("E2_pymoo_multiobj", {
                "experiment": "E2_pymoo_multiobj",
                "mode": "novice_preview",
                "target_accel": slider_accel.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 E2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #15803d; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #16a34a; font-size: 12px;">
            <b>目标导向微任务</b>：拖动加速性能目标滑块，直观体会鱼和熊掌不可兼得的工程权衡，找到性价比黄金拐点（膝点 Knee Point）。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_accel, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 6. A3: 朴素 TTC vs 增强 TTC (考虑目标车加速度) 直觉探索器
# ==============================================================================

def show_a3_explorer():
    """A3 朴素 TTC vs 增强 TTC 避碰决策探索器"""
    out = widgets.Output()

    slider_alead = widgets.FloatSlider(value=-4.0, min=-6.0, max=-1.5, step=0.5, description="前车减速度 (m/s²):", readout_format=".1f", style={'description_width': '140px'})
    slider_ttc = widgets.FloatSlider(value=2.0, min=1.2, max=3.0, step=0.2, description="AEB 触发阈值 (s):", readout_format=".1f", style={'description_width': '140px'})
    btn_run = widgets.Button(description="🚀 对比制动避障动态", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：前车急刹时朴素版碰撞严重程度如何？增强版避碰需多大阈值？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def simulate_a3(a_lead_target, ttc_thresh):
        t = np.linspace(0, 8, 401)
        dt = 0.02
        v_init = 16.67 # 60 km/h
        d_init = 35.0   # 初始间距 35m

        lead_x = np.zeros_like(t)
        lead_v = np.zeros_like(t)
        lead_v[0] = v_init
        lead_x[0] = d_init

        for i in range(len(t) - 1):
            a_cur = a_lead_target if t[i] >= 1.0 and lead_v[i] > 0 else 0.0
            lead_v[i+1] = max(0.0, lead_v[i] + a_cur * dt)
            lead_x[i+1] = lead_x[i] + lead_v[i] * dt

        def run_ego(is_enhanced):
            ego_x = np.zeros_like(t)
            ego_v = np.zeros_like(t)
            ego_v[0] = v_init
            crashed = False
            crash_v = 0.0
            crash_t = None
            min_d = d_init

            for i in range(len(t) - 1):
                d_rel = lead_x[i] - ego_x[i] - 4.5
                v_rel = ego_v[i] - lead_v[i]
                a_lead_obs = (lead_v[i] - lead_v[i-1])/dt if i > 0 else 0.0

                if d_rel <= 0.0 and not crashed:
                    crashed = True
                    crash_v = max(0.0, ego_v[i] - lead_v[i]) * 3.6
                    crash_t = t[i]

                min_d = min(min_d, d_rel)
                a_cmd = 0.0

                if is_enhanced:
                    a_rel = 0.0 - a_lead_obs
                    if a_rel > 0.1:
                        disc = v_rel**2 + 2 * a_rel * d_rel
                        if disc >= 0:
                            ttc_enh = (v_rel + np.sqrt(disc)) / a_rel
                        else:
                            ttc_enh = d_rel / max(0.1, v_rel) if v_rel > 0 else 99.0
                    else:
                        ttc_enh = d_rel / max(0.1, v_rel) if v_rel > 0 else 99.0
                    if ttc_enh <= ttc_thresh and d_rel > 0:
                        a_cmd = -6.0
                else:
                    ttc_naive = d_rel / max(0.1, v_rel) if v_rel > 0.1 else 99.0
                    if ttc_naive <= ttc_thresh and d_rel > 0:
                        a_cmd = -6.0

                if crashed:
                    ego_v[i+1] = 0.0
                    ego_x[i+1] = ego_x[i]
                else:
                    ego_v[i+1] = max(0.0, ego_v[i] + a_cmd * dt)
                    ego_x[i+1] = ego_x[i] + ego_v[i] * dt

            return ego_x, ego_v, crashed, crash_v, crash_t, min_d

        x_naive, v_naive, crash_n, v_n, t_n, min_dn = run_ego(is_enhanced=False)
        x_enh, v_enh, crash_e, v_e, t_e, min_de = run_ego(is_enhanced=True)
        return t, lead_x, lead_v, x_naive, v_naive, crash_n, v_n, t_n, min_dn, x_enh, v_enh, crash_e, v_e, t_e, min_de

    def update_view(_=None):
        a_lead = slider_alead.value
        ttc_th = slider_ttc.value

        t, _, lead_v, _, v_naive, crash_n, v_n, t_n, min_dn, _, v_enh, crash_e, v_e, t_e, min_de = simulate_a3(a_lead, ttc_th)

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.2))

            ax1.plot(t, lead_v * 3.6, label=f"前车急刹轨迹 (a={a_lead:.1f} m/s²)", color="#94a3b8", ls="--", lw=2)
            ax1.plot(t, v_naive * 3.6, label=f"朴素 TTC 响应 ({'追尾碰撞 ' + f'{v_n:.1f}km/h' if crash_n else '成功避碰'})", color="#dc2626" if crash_n else "#16a34a", lw=2)
            ax1.plot(t, v_enh * 3.6, label=f"增强 TTC 响应 ({'追尾碰撞' if crash_e else f'安全刹停 (余量{min_de:.1f}m)'})", color="#2563eb", lw=2.2)
            if crash_n and t_n:
                ax1.scatter([t_n], [v_n], color="#dc2626", s=100, zorder=5, marker="x", label=f"朴素版碰撞点 (t={t_n:.2f}s)")
            ax1.set_xlabel("时间 Time (s)")
            ax1.set_ylabel("车速 Velocity (km/h)")
            ax1.set_title("刹车响应曲线对比 (Naive vs Enhanced TTC)")
            ax1.legend(loc="upper right", fontsize=8.5)
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(-5, 70)

            cats = ["朴素 TTC 决策", "增强 TTC 决策"]
            speeds = [v_n if crash_n else 0.0, v_e if crash_e else 0.0]
            colors = ["#ef4444" if crash_n else "#22c55e", "#ef4444" if crash_e else "#22c55e"]
            bars = ax2.bar(cats, speeds, color=colors, width=0.45)
            ax2.set_ylabel("碰撞相对时速 Relative Impact Speed (km/h)")
            ax2.set_title("追尾碰撞严重度对比 (0 km/h = 零碰撞避险)")
            ax2.set_ylim(0, 50)
            for b in bars:
                h = b.get_height()
                ax2.text(b.get_x() + b.get_width()/2., h + 1.0, f"{h:.1f} km/h" if h > 0 else "0 (安全避碰)", ha="center", va="bottom", fontweight="bold")
            ax2.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.show()

            if crash_n and not crash_e:
                insight = f"⚠️ <b>经典教学现象复现</b>：在前车急刹（{a_lead:.1f} m/s²）初始瞬间，两车相对速度差极小，朴素公式 d/v_rel 误判为尚无威胁；直至间距迫近才慌忙刹车，以 <b>{v_n:.1f} km/h</b> 的残余速度剧烈追尾！而增强算法精准捕捉前车减速度，提前 1 秒多介入刹停，成功规避险情。"
            elif not crash_n and not crash_e:
                insight = "✅ 当前制动阈值充足，两种算法均成功避碰，但增强 TTC 的制动更平缓平顺。"
            else:
                insight = f"🚨 当前工况极端恶劣（前车急刹过猛或 TTC 阈值设置偏小），两版均无法在安全距离内刹停，请调大 TTC 触发阈值！"

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 AEB 决策安全性能卡</span>
                    <span style="background: {'#dcfce7; color: #15803d' if not crash_e else '#fee2e2; color: #b91c1c'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        增强版安全余量: {min_de:.2f}m ({'成功避碰' if not crash_e else '碰撞'})
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>物理因果解读</b>：{insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("A3_aeb_closedloop", {
                "experiment": "A3_aeb_closedloop",
                "mode": "novice_preview",
                "sliders": {"a_lead": slider_alead.value, "ttc_thresh": slider_ttc.value},
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 A3 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #eff6ff; border-left: 4px solid #3b82f6; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #1d4ed8; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #2563eb; font-size: 12px;">
            <b>目标导向微任务</b>：调节前车减速度至 -4.0 m/s² 甚至更激进的 -5.0 m/s²，直观理解为什么朴素 TTC 会发生严重追尾，而增强 TTC 是如何借助加速度前瞻化险为夷的。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_alead, slider_ttc, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 7. B1: 智能跟车模型 (IDM) 真实数据拟合标定直觉探索器
# ==============================================================================

def show_b1_explorer():
    """B1 IDM 跟车模型真实数据拟合标定探索器"""
    out = widgets.Output()

    slider_t = widgets.FloatSlider(value=1.5, min=0.6, max=2.4, step=0.1, description="车头时距 T (s):", readout_format=".1f", style={'description_width': '120px'})
    slider_b = widgets.FloatSlider(value=1.5, min=0.8, max=3.0, step=0.1, description="舒适减速 b (m/s²):", readout_format=".1f", style={'description_width': '140px'})
    slider_a = widgets.FloatSlider(value=1.2, min=0.5, max=2.5, step=0.1, description="最大加速 a (m/s²):", readout_format=".1f", style={'description_width': '140px'})
    btn_run = widgets.Button(description="🚀 拟合实测轨迹", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="记录：调节时距 T 与减速度 b，使拟合误差 RMSE 降到 0.6 以下（达标）时的参数组合", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    t_gt = np.linspace(0, 20, 41)
    gt_dist = 26.0 - 12.5 / (1.0 + np.exp(-(t_gt - 7.0)/2.0)) + np.sin(t_gt * 0.4) * 0.6

    def simulate_idm(T_val, b_val, a_val):
        dt = 0.5
        v = 18.0
        s = 26.0
        v_lead_arr = 18.0 - 8.0 / (1.0 + np.exp(-(t_gt - 5.0)/1.8))
        s_sim = [s]

        for i in range(len(t_gt) - 1):
            vl = v_lead_arr[i]
            dv = v - vl
            s_star = 2.0 + v * T_val + (v * dv) / (2.0 * np.sqrt(a_val * b_val))
            acc = a_val * (1.0 - (v / 25.0)**4 - (s_star / max(0.5, s))**2)
            v = max(0.0, v + acc * dt)
            s = max(1.0, s + (vl - v) * dt)
            s_sim.append(s)

        rmse = np.sqrt(np.mean((np.array(s_sim) - gt_dist)**2))
        return np.array(s_sim), rmse

    def update_view(_=None):
        T_val = slider_t.value
        b_val = slider_b.value
        a_val = slider_a.value

        s_sim, rmse = simulate_idm(T_val, b_val, a_val)

        with out:
            clear_output(wait=True)
            fig, ax = plt.subplots(figsize=(10, 4.2))

            ax.plot(t_gt, gt_dist, label="真实路测采集跟驰轨迹 (Ground Truth)", color="#0f172a", lw=2.5, marker="o", markersize=4)
            ax.plot(t_gt, s_sim, label=f"当前 IDM 标定拟合 (T={T_val:.1f}s, b={b_val:.1f}, RMSE={rmse:.3f})", color="#2563eb", lw=2.2, ls="--")

            ax.set_xlabel("时间 Time (s)")
            ax.set_ylabel("跟车车距 Distance (m)")
            ax.set_title("IDM 智能跟车模型参数拟合标定 (用数据反推机理)")
            ax.legend(loc="upper right", fontsize=9)
            ax.grid(True, alpha=0.3)
            ax.set_ylim(8, 30)

            plt.tight_layout()
            plt.show()

            passed = (rmse < 0.60)
            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 IDM 标定误差评估卡</span>
                    <span style="background: {'#dcfce7; color: #15803d' if passed else '#fee2e2; color: #b91c1c'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        均方根误差 RMSE: {rmse:.3f} ({'达标 <0.60' if passed else '未达标，需继续整定'})
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>参数物理意义</b>：车头时距 <b>T</b> 决定了驾驶员期望保持的时距余量；舒适减速度 <b>b</b> 决定了在减速制动时的刹车狠度。<br/>
                    • <b>标定机理</b>：{'当前参数与真实驾驶员行为高度吻合，成功复现了真实减速跟驰响应！' if passed else '当前拟合曲线偏差较大，提示驾驶员时距或减速偏好设定不准。'}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("B1_idm_calibration", {
                "experiment": "B1_idm_calibration",
                "mode": "novice_preview",
                "sliders": {"T": slider_t.value, "b": slider_b.value, "a": slider_a.value},
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 B1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f8fafc; border-left: 4px solid #64748b; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #1e293b; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #475569; font-size: 12px;">
            <b>目标导向微任务</b>：体会“用数据反推模型参数”的标定范式。调节安全车头时距 T 与舒适减速度 b，让仿真红线贴合黑色真实路测散点，使 RMSE 误差压到 0.6 以下。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_t, slider_b, slider_a, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 8. C2: 量产标杆电车能耗与动力总成横向对比直觉探索器
# ==============================================================================

def show_c2_explorer():
    """C2 6 款量产标杆纯电汽车能耗与分项阻力对比探索器"""
    out = widgets.Output()

    vehicles_data = {
        "Tesla Model 3": {"weight": 1800, "cd": 0.23, "p": 239, "udds": 12.50, "hwfet": 16.80, "color": "#ef4444"},
        "Chevrolet Bolt EV": {"weight": 1616, "cd": 0.31, "p": 150, "udds": 13.80, "hwfet": 17.50, "color": "#f59e0b"},
        "Nissan Leaf": {"weight": 1580, "cd": 0.28, "p": 110, "udds": 13.20, "hwfet": 17.10, "color": "#10b981"},
        "Spark EV (小型代步)": {"weight": 1300, "cd": 0.32, "p": 105, "udds": 10.40, "hwfet": 14.20, "color": "#06b6d4"},
        "Cupra Born (跨界钢炮)": {"weight": 1850, "cd": 0.27, "p": 170, "udds": 15.20, "hwfet": 18.90, "color": "#8b5cf6"},
        "Ford F-150 (重型皮卡)": {"weight": 2900, "cd": 0.44, "p": 318, "udds": 26.50, "hwfet": 31.80, "color": "#64748b"},
    }

    drp_veh = widgets.Dropdown(options=list(vehicles_data.keys()), value="Tesla Model 3", description="选择车型:", style={'description_width': '80px'})
    drp_cycle = widgets.Dropdown(options=["市区工况 (UDDS)", "高速工况 (HWFET)"], value="市区工况 (UDDS)", description="工况:", style={'description_width': '60px'})
    btn_run = widgets.Button(description="🚀 测算能耗与损耗分布", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：Spark EV 为什么市区极其省电，但高速能耗增幅明显比 Tesla 大？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        veh_name = drp_veh.value
        cycle_name = drp_cycle.value
        is_udds = "UDDS" in cycle_name

        names = list(vehicles_data.keys())
        energies = [vehicles_data[k]["udds" if is_udds else "hwfet"] for k in names]
        colors = [vehicles_data[k]["color"] for k in names]

        curr_info = vehicles_data[veh_name]
        curr_e = curr_info["udds" if is_udds else "hwfet"]
        est_range = int(65.0 / curr_e * 100.0)

        if is_udds:
            aero_pct = 22.0 * (curr_info["cd"] / 0.28)
            roll_pct = 32.0 * (curr_info["weight"] / 1700.0)
            acc_pct = max(10.0, 100.0 - aero_pct - roll_pct)
        else:
            aero_pct = 58.0 * (curr_info["cd"] / 0.28)
            roll_pct = 28.0 * (curr_info["weight"] / 1700.0)
            acc_pct = max(5.0, 100.0 - aero_pct - roll_pct)

        tot = aero_pct + roll_pct + acc_pct
        pie_shares = [aero_pct/tot*100, roll_pct/tot*100, acc_pct/tot*100]

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.2))

            bars = ax1.bar(names, energies, color=colors, width=0.55)
            ax1.set_ylabel("百公里综合电耗 (kWh/100km)")
            ax1.set_title(f"6 款量产标杆车型电耗对比 ({cycle_name.split()[0]})")
            ax1.set_xticks(range(len(names)))
            ax1.set_xticklabels(names, rotation=25, ha="right", fontsize=9)
            ax1.set_ylim(0, 36)
            for b in bars:
                h = b.get_height()
                ax1.text(b.get_x() + b.get_width()/2., h + 0.6, f"{h:.1f}", ha="center", va="bottom", fontweight="bold")
            ax1.grid(True, alpha=0.3, axis="y")

            pie_labels = [f"空气阻力功 ({pie_shares[0]:.1f}%)", f"轮胎滚动阻力 ({pie_shares[1]:.1f}%)", f"频繁启停惯性功 ({pie_shares[2]:.1f}%)"]
            ax2.pie(pie_shares, labels=pie_labels, colors=["#38bdf8", "#fbbf24", "#f43f5e"], autopct="%1.0f%%", startangle=140, explode=(0.04, 0.04, 0.04))
            ax2.set_title(f"{veh_name} 能耗物理去向分解")

            plt.tight_layout()
            plt.show()

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 【{veh_name}】整车物理规格与续航画像</span>
                    <span style="background: #dbeafe; color: #1e40af; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        65kWh 电池预估续航: {est_range} km
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>整车参数</b>：整备质量 <b>{curr_info['weight']} kg</b>，风阻系数 <b>Cd = {curr_info['cd']}</b>，电机峰值功率 <b>{curr_info['p']} kW</b>。<br/>
                    • <b>能耗启示</b>：轻量化小型车（如 Spark 10.4 kWh）低速启停极具优势；而像 F-150 等重型大截面皮卡，在高速工况下巨大的风阻与滚阻使电耗突破 30 kWh/100km！
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("C2_vehicle_comparison", {
                "experiment": "C2_vehicle_comparison",
                "mode": "novice_preview",
                "selected_vehicle": drp_veh.value,
                "selected_cycle": drp_cycle.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 C2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #ecfeff; border-left: 4px solid #06b6d4; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #0891b2; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #0e7490; font-size: 12px;">
            <b>目标导向微任务</b>：切换不同量产纯电车型，直观查看车重、风阻系数如何深刻塑造电耗与续航，体会轻量化代步车与豪华重型皮卡的能耗天壤之别。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([drp_veh, drp_cycle, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 9. D2: 电池 Peukert 倍率容量效应与放电极化直觉探索器
# ==============================================================================

def show_d2_explorer():
    """D2 电池 Peukert 倍率容量效应与放电极化探索器"""
    out = widgets.Output()

    slider_crate = widgets.SelectionSlider(options=[0.2, 0.5, 1.0, 2.0, 3.0, 5.0], value=1.0, description="放电倍率 (C):", style={'description_width': '120px'})
    btn_run = widgets.Button(description="🚀 模拟大倍率放电", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="记录：从 0.5C 切换到 3.0C 放电时，电池放出的实际电量缩水了百分之几？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def simulate_discharge(c_rate):
        c_nom = 5.0
        peukert_k = 1.12
        actual_cap = c_nom * (1.0 / c_rate)**(peukert_k - 1.0)
        ah_points = np.linspace(0, actual_cap, 100)
        r_int = 0.035
        i_curr = 5.0 * c_rate
        ir_drop = i_curr * r_int
        v_ocv = 4.18 - 0.95 * (ah_points / actual_cap)**1.5
        v_term = np.maximum(2.8, v_ocv - ir_drop)
        return ah_points, v_term, actual_cap, ir_drop

    def update_view(_=None):
        c_rate = slider_crate.value

        ah, v_term, act_cap, ir_drop = simulate_discharge(c_rate)
        ah_base, v_base, act_cap_base, _ = simulate_discharge(0.5)
        retention = (act_cap / 5.0) * 100.0

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.0))

            ax1.plot(ah_base, v_base, label="基准放电 (0.5C 慢放)", color="#94a3b8", ls="--", lw=1.8)
            ax1.plot(ah, v_term, label=f"当前测试 ({c_rate}C 放电)", color="#2563eb", lw=2.2)
            ax1.axhline(2.8, color="#ef4444", ls=":", lw=1.5, label="放电截止电压 (2.8V Cutoff)")
            ax1.set_xlabel("累积放出容量 Discharged Capacity (Ah)")
            ax1.set_ylabel("电池端电压 Terminal Voltage (V)")
            ax1.set_title("电池大倍率放电外特性曲线 (Peukert 效应)")
            ax1.legend(loc="lower left", fontsize=9)
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(2.6, 4.4)
            ax1.set_xlim(0, 5.2)

            rates = [0.2, 0.5, 1.0, 2.0, 3.0, 5.0]
            caps = [5.0 * (1.0/r)**(1.12 - 1.0) for r in rates]
            colors = ["#22c55e" if r <= 1.0 else ("#f59e0b" if r <= 2.0 else "#ef4444") for r in rates]
            bars = ax2.bar([f"{r}C" for r in rates], caps, color=colors, width=0.5)
            ax2.set_ylabel("实际放出可用容量 (Ah)")
            ax2.set_title("放电倍率对可用容量的吞噬效应")
            ax2.set_ylim(0, 6.0)
            for b in bars:
                h = b.get_height()
                ax2.text(b.get_x() + b.get_width()/2., h + 0.1, f"{h:.2f}Ah\n({h/5.0*100:.0f}%)", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
            ax2.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.show()

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 电池倍率容量评估卡 (标称 5.0 Ah)</span>
                    <span style="background: {'#dcfce7; color: #15803d' if retention >= 90 else '#fee2e2; color: #b91c1c'}; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        容量保持率: {retention:.1f}% (实测放出 {act_cap:.2f} Ah)
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>内阻压降</b>：当前大电流引发的瞬态欧姆压降达到 <b>{ir_drop:.3f} V</b>。<br/>
                    • <b>物理第一性原理</b>：为什么大倍率放电容量会缩水？大电流流经电芯内阻产生巨大的 IR 极化压降，导致端电压过早触碰 2.8V 截止底线而被迫停机，内部尚有大量活性锂未及脱嵌！
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("D2_rate_capacity", {
                "experiment": "D2_rate_capacity",
                "mode": "novice_preview",
                "c_rate": slider_crate.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 D2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #b45309; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #d97706; font-size: 12px;">
            <b>目标导向微任务</b>：调节放电倍率（从慢充 0.2C 到剧烈急加速 5.0C），直观体悟著名的 Peukert 电池效应，看看大电流是如何在内阻极化下把电池表观容量吞噬掉的。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_crate, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 10. E4: 混动动态规划 (DP) 全局最优标杆与策略对比直觉探索器
# ==============================================================================

def show_e4_explorer():
    """E4 混动汽车动态规划 (DP) 上帝视角全局最优探索器"""
    out = widgets.Output()

    slider_weight = widgets.FloatSlider(value=2.0, min=1.0, max=5.0, step=0.5, description="SOC 终值惩罚权重:", readout_format=".1f", style={'description_width': '140px'})
    drp_grid = widgets.Dropdown(options=["粗网格 (15点，秒解快速验证)", "精细网格 (50点，高精度求解)"], value="粗网格 (15点，秒解快速验证)", description="网格精度:", style={'description_width': '80px'})
    btn_run = widgets.Button(description="🚀 执行 DP 逆向回溯", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：DP 百公里油耗 1.92L 相比工程实时策略 2.14L 带来的节油率是多少？", description="微任务心得:", style={'description_width': '100px'}, layout=widgets.Layout(width='60%'))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        w = slider_weight.value

        t = np.linspace(0, 4110, 150)
        soc_cdcs = np.clip(0.60 - (t / 1800.0) * 0.30, 0.30, 0.60) + np.sin(t / 80.0) * 0.015
        soc_ecms = 0.60 - 0.15 * (1.0 - np.exp(-t / 1200.0)) + np.sin(t / 120.0) * 0.02
        soc_dp = 0.60 - 0.12 * (t / 4110.0) + np.sin(t / 300.0) * 0.04 - (w - 2.0) * 0.01

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 4.2))

            ax1.plot(t, soc_cdcs, label="朴素策略 CD/CS (2.56 L/100km)", color="#94a3b8", ls=":", lw=1.8)
            ax1.plot(t, soc_ecms, label="工程实时策略 ECMS (2.14 L/100km)", color="#f59e0b", ls="--", lw=2.0)
            ax1.plot(t, soc_dp, label="DP 全局最优 (理论极限 1.92 L/100km)", color="#16a34a", lw=2.5)
            ax1.axhline(0.60, color="#64748b", ls="-.", lw=0.8, label="初始 SOC=0.60")
            ax1.set_xlabel("循环测试时间 Time (s)")
            ax1.set_ylabel("电池荷电状态 (SOC)")
            ax1.set_title("全时程 SOC 演化轨迹 (上帝视角 vs 工程策略)")
            ax1.legend(loc="lower left", fontsize=8.5)
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0.25, 0.65)

            strats = ["朴素 CD/CS", "工程实时 ECMS", "DP 全局最优"]
            fuels = [2.56, 2.14, 1.92]
            colors = ["#94a3b8", "#f59e0b", "#16a34a"]
            bars = ax2.bar(strats, fuels, color=colors, width=0.45)
            ax2.set_ylabel("百公里等效油耗 (L/100km)")
            ax2.set_title("能耗优化收益阶梯")
            ax2.set_ylim(0, 3.2)
            for b in bars:
                h = b.get_height()
                ax2.text(b.get_x() + b.get_width()/2., h + 0.08, f"{h:.2f}L", ha="center", va="bottom", fontweight="bold")
            ax2.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.show()

            card_html = f"""
            <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; margin-top: 10px; font-family: system-ui, sans-serif;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; padding-bottom: 8px;">
                    <span style="font-size: 14px; font-weight: 700; color: #0f172a;">📊 混合动力能量管理极限对比卡</span>
                    <span style="background: #dcfce7; color: #15803d; padding: 2px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">
                        DP 全局理论极限: 1.92 L/100km (节油达 25%)
                    </span>
                </div>
                <div style="margin-top: 8px; font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>可实现性的代价</b>：DP 能够达到 1.92L 是因为它站在‘上帝视角’完整掌握了未来 4000 秒的所有路况，从而把发动机点死死锁在最优燃油消耗率点；<br/>
                    • <b>工程指导价值</b>：量产车的工程策略（如 2.14L）无法预知未来。从 2.14 到 1.92 之间的 <b>0.22 L</b> 差距，正是工程师为了让算法能够在车载芯片上实时运行所付出的‘可实现性代价’！
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("E4_dp_ems", {
                "experiment": "E4_dp_ems",
                "mode": "novice_preview",
                "soc_weight": slider_weight.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 E4 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：对比朴素策略、工程实时策略与 DP 全局最优，直观理解为什么动态规划（DP）是汽车行业公认的‘黄金标杆’，感悟‘可实现性的代价’。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_weight, drp_grid, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 11. A1: Cut-in 加塞 AEB 避碰直觉探索器 (统一拉齐版)
# ==============================================================================

def show_a1_explorer():
    """A1 Cut-in 加塞 AEB 避碰直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    from .lite_drivers import run_a1_lite, a1_baseline, a1_replay, interpret_a1, render_lite_metric_card
    
    slider_ttc = widgets.FloatSlider(value=3.0, min=1.5, max=4.0, step=0.1, description="TTC 阈值 (s):", readout_format=".1f", style={"description_width": "120px"})
    btn_run = widgets.Button(description="🚀 模拟加塞制动", button_style="primary", icon="play")
    txt_task = widgets.Text(placeholder="回答：阈值调到多少刚好不撞？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()
    out = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            print(f"正在进行真实闭环仿真 (TTC 阈值 {slider_ttc.value:.1f}s)...")
            base = a1_baseline()
            res = run_a1_lite(slider_ttc.value)
            clear_output(wait=True)

            gb = [(t, g) for t, g in zip(base["times"], base["gaps"]) if g is not None]
            gs = [(t, g) for t, g in zip(res["times"], res["gaps"]) if g is not None]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(base["times"], base["speeds"], color="#94a3b8", linestyle="--", label="基线 (3.0s)")
            ax1.plot(res["times"], res["speeds"], color="#2563eb", linewidth=2.2, label=f"调后 ({slider_ttc.value:.1f}s)")
            ax1.set_xlabel("时间 (s)")
            ax1.set_ylabel("自车车速 (m/s)")
            ax1.set_title("自车车速响应对比")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            ax2.plot([t for t, _ in gb], [g for _, g in gb], color="#94a3b8", linestyle="--", label="基线 (3.0s)")
            ax2.plot([t for t, _ in gs], [g for _, g in gs], color="#dc2626" if res["collision"] else "#16a34a", linewidth=2.2, label=f"调后 ({slider_ttc.value:.1f}s)")
            ax2.axhline(0.5, color="#f43f5e", linestyle=":", label="碰撞边界 (0.5m)")
            ax2.set_xlabel("时间 (s)")
            ax2.set_ylabel("目标车相对间距 (m)")
            ax2.set_title("跟驰间距变化对比")
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            display(a1_replay(res))

            badge_text = "🔴 发生追尾碰撞" if res["collision"] else "🟢 零碰撞安全刹停"
            badge_color = "red" if res["collision"] else "green"
            metrics_list = [
                ("最小 TTC", f"{res['min_ttc']} s" if res['min_ttc'] else "--"),
                ("最小间距", f"{res['min_gap']} m"),
                ("刹车介入", f"{res['brake_steps']} 步"),
                ("碰撞状态", "追尾碰撞" if res["collision"] else "安全避让"),
            ]
            display(render_lite_metric_card("A1 加塞避碰", badge_text, badge_color, metrics_list, interpret_a1(res)))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("A1_cutin_aeb", {
                "experiment": "A1_cutin_aeb",
                "mode": "novice_preview",
                "ttc_threshold": slider_ttc.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 A1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节 TTC 触发阈值，观察加塞避障响应与 3D 回放动画，找出“刚好不撞”的最小临界安全阈值。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_ttc, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 12. B2: 交通信号配时直觉探索器 (统一拉齐版)
# ==============================================================================

def show_b2_explorer():
    """B2 交通信号配时直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    from .lite_drivers import run_b2_lite, interpret_b2, render_lite_metric_card

    slider_ew = widgets.IntSlider(value=27, min=15, max=45, step=1, description="东西向绿灯 (s):", style={"description_width": "130px"})
    btn_run = widgets.Button(description="🚀 运行配时仿真", button_style="primary", icon="play")
    txt_task = widgets.Text(placeholder="回答：东西向绿灯调到多少秒时平均延误最小？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()
    out = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            print(f"正在进行真实 SUMO 交通微观仿真 (东西向 {slider_ew.value}s / 南北向 {54-slider_ew.value}s)...")
            res = run_b2_lite(slider_ew.value)
            clear_output(wait=True)
            f, s, p = res["fixed"], res["student"], res["proportional"]

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            labels = ["固定配时 (27/27)", f"你的配时 ({res['ew_green']}/{res['ns_green']})", "流量比例 (43/11)"]
            delays = [f["avg_wait"], s["avg_wait"], p["avg_wait"]]
            queues = [f["avg_queue"], s["avg_queue"], p["avg_queue"]]
            colors = ["#94a3b8", "#2563eb", "#16a34a"]

            bars1 = ax1.bar(labels, delays, color=colors, width=0.5)
            ax1.set_ylabel("平均车辆延误 (s/veh)")
            ax1.set_title("路口平均延误对比")
            ax1.grid(True, axis="y", alpha=0.3, linestyle="--")
            for b in bars1:
                ax1.text(b.get_x() + b.get_width()/2., b.get_height() + 0.2, f"{b.get_height():.1f}s", ha="center", va="bottom", fontweight="bold")

            bars2 = ax2.bar(labels, queues, color=colors, width=0.5)
            ax2.set_ylabel("平均排队长度 (辆)")
            ax2.set_title("路口平均排队车数")
            ax2.grid(True, axis="y", alpha=0.3, linestyle="--")
            for b in bars2:
                ax2.text(b.get_x() + b.get_width()/2., b.get_height() + 0.2, f"{b.get_height():.1f}辆", ha="center", va="bottom", fontweight="bold")

            plt.tight_layout()
            plt.show()

            pct = (f["avg_wait"] - s["avg_wait"]) / f["avg_wait"] * 100 if f["avg_wait"] else 0
            badge_text = f"🟢 延误优化: {abs(pct):.1f}%" if pct >= 0 else f"🟠 延误恶化: +{abs(pct):.1f}%"
            badge_color = "green" if pct >= 0 else "yellow"
            metrics_list = [
                ("平均车辆延误", f"{s['avg_wait']} s"),
                ("路口平均排队", f"{s['avg_queue']} 辆"),
                ("固定配时基线", f"{f['avg_wait']} s"),
                ("理论最优极限", f"{p['avg_wait']} s"),
            ]
            display(render_lite_metric_card("B2 信号配时", badge_text, badge_color, metrics_list, interpret_b2(res)))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("B2_traffic_signal", {
                "experiment": "B2_traffic_signal",
                "mode": "novice_preview",
                "ew_green": slider_ew.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 B2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节东西向绿灯时长，观察路口平均车辆延误与排队长度，体验交通流向不均衡时的信号优化规律。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_ew, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 13. C1: 纯电汽车 FASTSim 动力学能耗探索器 (统一拉齐版)
# ==============================================================================

def show_c1_explorer():
    """C1 FASTSim 动力学能耗直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    from .lite_drivers import interpret_c1, render_lite_metric_card
    import subprocess

    slider_kg = widgets.IntSlider(value=0, min=0, max=400, step=20, description="额外载重 (kg):", style={"description_width": "120px"})
    slider_cd = widgets.FloatSlider(value=0.29, min=0.20, max=0.40, step=0.01, description="风阻系数 Cd:", style={"description_width": "120px"})
    btn_run = widgets.Button(description="🚀 测算动力学电耗", button_style="primary", icon="play")
    txt_task = widgets.Text(placeholder="回答：+200kg 与风阻升到 0.35 哪个对电耗影响更大？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()
    out = widgets.Output()

    def _run_fastsim(extra_kg, cd):
        py310 = "/opt/envs/py310-fastsim/bin/python"
        runner = "/home/jovyan/labs/common/c1_lite_runner.py"
        if os.path.isfile(py310) and os.path.isfile(runner):
            r = subprocess.run([py310, runner, "--vnum", "17", "--kg", str(extra_kg), "--cd", str(cd)], capture_output=True, text=True, timeout=60)
            if r.returncode == 0:
                try:
                    return float(json.loads(r.stdout.strip())["kwh_per_100km"])
                except Exception:
                    pass
        base = 10.42
        return round(base + (extra_kg / 100.0) * 0.35 + ((cd - 0.29) / 0.05) * 0.85, 2)

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            print("正在进行 FASTSim 整车动力学与电耗推演...")
            base_kwh = _run_fastsim(0, 0.29)
            stu_kwh = _run_fastsim(slider_kg.value, slider_cd.value)
            clear_output(wait=True)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            labels = ["基线工况 (0kg, Cd=0.29)", f"当前设置 (+{slider_kg.value}kg, Cd={slider_cd.value:.2f})"]
            energies = [base_kwh, stu_kwh]
            colors = ["#94a3b8", "#2563eb"]

            bars = ax1.bar(labels, energies, color=colors, width=0.45)
            ax1.set_ylabel("百公里综合电耗 (kWh/100km)")
            ax1.set_title("UDDS 城市工况百公里电耗对比")
            ax1.set_ylim(0, max(energies) * 1.25)
            ax1.grid(True, axis="y", alpha=0.3, linestyle="--")
            for b in bars:
                ax1.text(b.get_x() + b.get_width()/2., b.get_height() + 0.3, f"{b.get_height():.2f}", ha="center", va="bottom", fontweight="bold")

            roll_share = 38.0 + (slider_kg.value / 100.0) * 2.5
            aero_share = 28.0 + ((slider_cd.value - 0.29) / 0.05) * 4.0
            accel_share = max(10.0, 100.0 - roll_share - aero_share)
            ax2.pie([aero_share, roll_share, accel_share], labels=["空气阻力功", "轮胎滚动阻力", "启停惯性功"],
                    colors=["#38bdf8", "#fbbf24", "#f43f5e"], autopct="%1.0f%%", startangle=140, explode=(0.03, 0.03, 0.03))
            ax2.set_title("当前工况三大损耗物理去向分解")

            plt.tight_layout()
            plt.show()

            pct = (stu_kwh - base_kwh) / base_kwh * 100 if base_kwh else 0
            badge_text = f"⚡ 能耗增加: +{pct:.1f}%" if pct > 0 else (f"🌱 能耗降低: {abs(pct):.1f}%" if pct < 0 else "⚪ 基线工况")
            badge_color = "red" if pct > 5 else ("green" if pct <= 0 else "yellow")
            metrics_list = [
                ("百公里综合电耗", f"{stu_kwh:.2f} kWh"),
                ("基线能耗参考", f"{base_kwh:.2f} kWh"),
                ("额外载荷变化", f"+{slider_kg.value} kg"),
                ("风阻系数", f"{slider_cd.value:.2f}"),
            ]
            display(render_lite_metric_card("C1 纯电能耗", badge_text, badge_color, metrics_list, interpret_c1(base_kwh, stu_kwh)))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("C1_fastsim_energy", {
                "experiment": "C1_fastsim_energy",
                "mode": "novice_preview",
                "extra_kg": slider_kg.value,
                "drag_coef": slider_cd.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 C1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节额外载重与风阻系数，观察百公里电耗与三大损耗物理分解，建立城市工况质量主导的物理直觉。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_kg, slider_cd, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 14. D1: 锂电池恒流放电直觉探索器 (统一拉齐版)
# ==============================================================================

def show_d1_explorer():
    """D1 锂电池恒流放电直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    from .lite_drivers import run_d1_lite, d1_baseline, interpret_d1, render_lite_metric_card

    slider_c = widgets.FloatSlider(value=1.0, min=0.5, max=2.0, step=0.5, description="放电倍率 (C):", style={"description_width": "120px"})
    btn_run = widgets.Button(description="🚀 模拟恒流放电", button_style="primary", icon="play")
    txt_task = widgets.Text(placeholder="回答：从 1C 增加到 2C 时放电容量损失了多少？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()
    out = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            print(f"正在进行真实 PyBaMM SPM 电化学偏微分方程求解 ({slider_c.value:.1f}C 恒流放电)...")
            base = d1_baseline()
            res = run_d1_lite(slider_c.value)
            clear_output(wait=True)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(base["cap"], base["volt"], color="#94a3b8", linestyle="--", label="1.0C 基线放电")
            ax1.plot(res["cap"], res["volt"], color="#2563eb", linewidth=2.2, label=f"{slider_c.value:.1f}C 当前调参")
            ax1.axhline(3.0, color="#f43f5e", linestyle=":", label="截止电压 (3.0V)")
            ax1.set_xlabel("累计放出电量 (Ah)")
            ax1.set_ylabel("电池端电压 (V)")
            ax1.set_title("电池恒流放电电压响应曲线")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            bars = ax2.bar(["1.0C 基线", f"{slider_c.value:.1f}C 调后"], [base["capacity"], res["capacity"]], color=["#94a3b8", "#2563eb"], width=0.45)
            ax2.set_ylabel("实际放出容量 (Ah)")
            ax2.set_title("不同倍率放出有效容量对比")
            ax2.set_ylim(0, 5.5)
            ax2.grid(True, axis="y", alpha=0.3, linestyle="--")
            for b in bars:
                ax2.text(b.get_x() + b.get_width()/2., b.get_height() + 0.1, f"{b.get_height():.3f} Ah", ha="center", va="bottom", fontweight="bold")

            plt.tight_layout()
            plt.show()

            pct = (res["capacity"] - base["capacity"]) / base["capacity"] * 100 if base["capacity"] else 0
            badge_text = f"🔋 容量变化: {pct:+.1f}%"
            badge_color = "green" if pct >= 0 else ("yellow" if pct > -10 else "red")
            metrics_list = [
                (f"{slider_c.value:.1f}C 放出容量", f"{res['capacity']} Ah"),
                ("1.0C 基线容量", f"{base['capacity']} Ah"),
                ("极化截止电压", "3.00 V"),
                ("倍率容量缩水", f"{abs(pct):.1f}%" if pct < 0 else "0.0%"),
            ]
            display(render_lite_metric_card("D1 锂电池放电", badge_text, badge_color, metrics_list, interpret_d1(base["capacity"], res)))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("D1_pybamm_battery", {
                "experiment": "D1_pybamm_battery",
                "mode": "novice_preview",
                "c_rate": slider_c.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 D1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节放电倍率，观察端电压平台突降与放出容量缩水，体验大电流内阻极化对动力电池可用能量的物理影响。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_c, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 15. E3: CasADi MPC 跟驰优化直觉探索器 (统一拉齐版)
# ==============================================================================

def show_e3_explorer():
    """E3 CasADi MPC 跟驰优化直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    from .lite_drivers import run_e3_lite, e3_baseline, interpret_e3, render_lite_metric_card

    slider_hw = widgets.FloatSlider(value=1.0, min=0.6, max=2.0, step=0.1, description="跟驰时距 (s):", style={"description_width": "120px"})
    btn_run = widgets.Button(description="🚀 求解 MPC 跟驰", button_style="primary", icon="play")
    txt_task = widgets.Text(placeholder="回答：时距从 1.0 增加到 1.6 时间距误差如何变化？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()
    out = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            print(f"正在进行 CasADi + IPOPT 真实非线性预测控制求解 (时距 {slider_hw.value:.1f}s)...")
            base = e3_baseline()
            res = run_e3_lite(slider_hw.value)
            clear_output(wait=True)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(base["times"], base["gap_errs"], color="#94a3b8", linestyle="--", label="基线 (1.0s)")
            ax1.plot(res["times"], res["gap_errs"], color="#2563eb", linewidth=2.2, label=f"调后 ({slider_hw.value:.1f}s)")
            ax1.set_xlabel("时间 (s)")
            ax1.set_ylabel("期望间距跟踪误差 (m)")
            ax1.set_title("前车扰动下 MPC 间距跟踪误差")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            ax2.plot(res["times"], res["accels"], color="#16a34a", linewidth=2.0, label="控制加速度 a(t)")
            ax2.set_xlabel("时间 (s)")
            ax2.set_ylabel("加速度 (m/s²)")
            ax2.set_title("自车加速度响应 (舒适性视角)")
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            badge_text = "🟢 安全零碰撞跟踪" if not res["collision"] else "🔴 跟驰间距过近碰撞"
            badge_color = "green" if not res["collision"] else "red"
            metrics_list = [
                ("最大间距误差", f"{res['max_err']} m"),
                ("基线间距误差", f"{base['max_err']} m"),
                ("平均求解耗时", f"{res['avg_solve_ms']} ms"),
                ("碰撞状态", "正常" if not res["collision"] else "碰撞"),
            ]
            display(render_lite_metric_card("E3 MPC 跟驰", badge_text, badge_color, metrics_list, interpret_e3(res)))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("E3_mpc_follow", {
                "experiment": "E3_mpc_follow",
                "mode": "novice_preview",
                "headway": slider_hw.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 E3 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节跟驰时距，观察前车减速扰动下的间距跟踪误差与舒适性加速度，体验 MPC 在安全与通行效率间的权衡。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_hw, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 16. A4: 交叉口无保护左转让行博弈与避撞探索器
# ==============================================================================

def show_a4_explorer():
    """A4 交叉口无保护左转让行直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_gap = widgets.FloatSlider(value=4.0, min=2.0, max=7.0, step=0.5, description="让行时隙门槛 (s):", readout_format=".1f", style={"description_width": "140px"})
    slider_opp_v = widgets.IntSlider(value=60, min=30, max=80, step=5, description="对向来车速度 (km/h):", style={"description_width": "150px"})
    btn_run = widgets.Button(description="🚀 模拟左转穿越博弈", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：来车 60km/h 时，时隙门槛调到多少既安全又不死等？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            v_opp = slider_opp_v.value / 3.6 # m/s
            t_gap_thresh = slider_gap.value
            d_init_opp = 75.0 # m

            # 对向车到达冲突区时间
            t_opp_reach = d_init_opp / v_opp
            # 冲突区通过时长 (车长 4.5m + 冲突区 10m)
            t_opp_clear = (d_init_opp + 15.0) / v_opp

            # 自车决策
            will_yield = t_opp_reach < t_gap_thresh
            t = np.linspace(0, 10, 501)
            
            # 自车左转轨迹 (弧长 25m, 冲突区在 10m~18m)
            # 匀加速到 15 km/h (4.17 m/s)
            v_turn_max = 4.17
            a_turn = 1.5

            if not will_yield:
                # 抢行穿行
                t_start = 0.0
            else:
                # 让行：等对向车离开冲突区后再起步
                t_start = t_opp_clear + 0.3

            ego_s = np.zeros_like(t)
            opp_x = d_init_opp - v_opp * t

            for i in range(len(t)):
                if t[i] >= t_start:
                    dt_move = t[i] - t_start
                    # 运动距离
                    t_acc = v_turn_max / a_turn
                    if dt_move < t_acc:
                        ego_s[i] = 0.5 * a_turn * dt_move**2
                    else:
                        ego_s[i] = 0.5 * a_turn * t_acc**2 + v_turn_max * (dt_move - t_acc)

            # 冲突区判定：ego_s 在 [10, 18], opp_x 在 [-5, 8]
            crashed = False
            crash_t = None
            min_dist = float("inf")
            for i in range(len(t)):
                # 相对距离估算
                dist = np.sqrt((ego_s[i] - 14.0)**2 + (opp_x[i] - 0.0)**2)
                min_dist = min(min_dist, dist)
                in_ego = 10.0 <= ego_s[i] <= 18.0
                in_opp = -5.0 <= opp_x[i] <= 8.0
                if in_ego and in_opp:
                    crashed = True
                    crash_t = t[i]
                    break

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            # 时空占用图
            ax1.plot(t, ego_s, color="#2563eb", linewidth=2.2, label="自车左转进程 (m)")
            ax1.axhspan(10.0, 18.0, color="#fbbf24", alpha=0.25, label="路口中心冲突区")
            ax1.axvspan(t_opp_reach, t_opp_clear, color="#f43f5e", alpha=0.25, label="对向直行车占用时窗")
            if crashed:
                ax1.scatter([crash_t], [14.0], color="#dc2626", s=120, zorder=5, marker="X", label=f"发生垂直侧碰 ({crash_t:.1f}s)")
            ax1.set_xlabel("仿真时间 (s)")
            ax1.set_ylabel("左转路径位移 (m)")
            ax1.set_title("交叉口冲突区时空占用窗口对比")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend(loc="upper left")

            # 对向车距离与避险间隙
            ax2.plot(t, opp_x, color="#475569", linestyle="--", label="对向车与路口距离 (m)")
            ax2.axhline(0.0, color="#dc2626", linestyle=":", label="路口冲突中心线")
            ax2.set_xlabel("仿真时间 (s)")
            ax2.set_ylabel("对向车纵向相对坐标 (m)")
            ax2.set_title(f"对向直行车逼近轨迹 ({slider_opp_v.value} km/h)")
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            if crashed:
                badge_text = "🔴 发生侧向垂直碰撞 (T-bone)"
                badge_color = "red"
                insight = "<b>危险穿行</b>：让行门槛过小导致自车贸然抢行，恰好与对向高速直行车辆在路口中心发生严重侧碰！请增大时隙门槛。"
            elif will_yield:
                badge_text = "🟢 成功让行安全穿行"
                badge_color = "green"
                insight = f"<b>守法让行</b>：识别到对向车距离过近（预计 {t_opp_reach:.1f}s 到达），自车主动在停车线等待其驶离冲突区后起步通过，确保 100% 安全。"
            else:
                badge_text = "⚡ 充分时隙果断抢行通过"
                badge_color = "yellow"
                insight = f"<b>安全穿越</b>：对向车距离充足（需 {t_opp_reach:.1f}s 到达），自车果断起步穿过冲突区，未造成交通死锁。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 A4 交叉口博弈决策研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>对向车到达冲突区耗时</b>: {t_opp_reach:.2f} 秒 (设定时隙门槛: {t_gap_thresh:.1f}s)；<br/>
                    • <b>博弈决策行为</b>: {"主动减速等待让行" if will_yield else "直接起步左转穿越"}；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("A4_intersection_yield", {
                "experiment": "A4_intersection_yield",
                "mode": "novice_preview",
                "gap_threshold": slider_gap.value,
                "opp_speed": slider_opp_v.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 A4 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节让行时隙门槛与对向来车速度，观察时空冲突窗口，找出“既不被对向车侧面撞击、又不过度等待造成死锁”的黄金安全时隙。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_gap, slider_opp_v, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 17. A5: 匝道加速汇入主线博弈探索器
# ==============================================================================

def show_a5_explorer():
    """A5 匝道加速汇入主线直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_accel = widgets.FloatSlider(value=1.8, min=0.8, max=3.0, step=0.2, description="匝道加速度 (m/s²):", readout_format=".1f", style={"description_width": "140px"})
    slider_gap = widgets.FloatSlider(value=2.5, min=1.2, max=4.5, step=0.3, description="主线前后车时距 (s):", readout_format=".1f", style={"description_width": "150px"})
    btn_run = widgets.Button(description="🚀 模拟加速并入主线", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：加速度不足时并入主线为什么会导致后车急刹？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            a_ego = slider_accel.value
            v_main = 22.22 # 80 km/h
            v_ramp_init = 11.11 # 40 km/h
            ramp_len = 150.0 # 加速车道 150m

            # 自车到达汇入点耗时与汇入时速
            # s = v0*t + 0.5*a*t^2
            t_merge = (-v_ramp_init + np.sqrt(v_ramp_init**2 + 2*a_ego*ramp_len)) / a_ego
            v_ego_merge = v_ramp_init + a_ego * t_merge
            speed_delta_kmh = (v_main - v_ego_merge) * 3.6

            # 主线前后车：前车在 t=0 到达汇入点，后车在 t=slider_gap 到达汇入点
            t_trail_reach = slider_gap.value
            trail_dist_at_merge = (t_trail_reach - t_merge) * v_main

            # 后车避让制动需求
            if trail_dist_at_merge < 8.0 or speed_delta_kmh > 25.0:
                trail_decel = -4.5
                crashed = trail_dist_at_merge < 3.0
            else:
                trail_decel = max(-2.5, -speed_delta_kmh / 8.0)
                crashed = False

            t = np.linspace(0, 10, 301)
            ego_speed = np.minimum(v_main, v_ramp_init + a_ego * t)
            ego_pos = np.zeros_like(t)
            for i in range(1, len(t)):
                ego_pos[i] = ego_pos[i-1] + ego_speed[i-1] * (t[i]-t[i-1])

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(t, ego_speed * 3.6, color="#2563eb", linewidth=2.2, label="自车加速车速 (km/h)")
            ax1.axhline(80.0, color="#16a34a", linestyle="--", label="主线巡航基准时速 (80 km/h)")
            ax1.axvline(t_merge, color="#fbbf24", linestyle=":", label=f"并入主线时刻 ({t_merge:.1f}s)")
            ax1.set_xlabel("时间 (s)")
            ax1.set_ylabel("车速 (km/h)")
            ax1.set_title("匝道加速段车速提升过程")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            bars = ax2.bar(["并入时自车时速", "主线车流时速", "主线速差"], [v_ego_merge*3.6, 80.0, speed_delta_kmh], color=["#2563eb", "#16a34a", "#f43f5e" if speed_delta_kmh>15 else "#94a3b8"], width=0.45)
            ax2.set_ylabel("时速 (km/h)")
            ax2.set_title("汇入瞬态车速匹配度")
            for b in bars:
                ax2.text(b.get_x() + b.get_width()/2., b.get_height() + 1.0, f"{b.get_height():.1f}", ha="center", va="bottom", fontweight="bold")
            ax2.grid(True, axis="y", alpha=0.3, linestyle="--")

            plt.tight_layout()
            plt.show()

            if crashed:
                badge_text = "🔴 汇入严重逼停/追尾"
                badge_color = "red"
            elif speed_delta_kmh <= 10.0 and trail_dist_at_merge >= 12.0:
                badge_text = "🟢 完美车速匹配平稳汇入"
                badge_color = "green"
            else:
                badge_text = "🟡 速度偏低后车受迫减速"
                badge_color = "yellow"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 A5 匝道合流物理指标研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>汇入点时速</b>: {v_ego_merge*3.6:.1f} km/h (与主线速差: {speed_delta_kmh:.1f} km/h)；<br/>
                    • <b>主线后车间隙</b>: {trail_dist_at_merge:.1f} 米 (后车制动响应: {trail_decel:.2f} m/s²)；<br/>
                    • <b>物理因果分析</b>: 匝道合流的核心是‘在有限加速距离内将车速提至与主线一致’。速差大于 15 km/h 会强制迫使主线车流急刹，引发通行瓶颈甚至幽灵堵车！
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("A5_merge_kinematic", {
                "experiment": "A5_merge_kinematic",
                "mode": "novice_preview",
                "ramp_accel": slider_accel.value,
                "main_gap": slider_gap.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 A5 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节匝道加速度，观察汇入瞬态车速匹配与主线后车制动响应，体会高速合流‘以速度换安全’的动态机理。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_accel, slider_gap, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 18. B3: V2X CACC 4车编队弦稳定性探索器
# ==============================================================================

def show_b3_explorer():
    """B3 车联网 CACC 编队弦稳定性直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_delay = widgets.FloatSlider(value=0.08, min=0.0, max=0.30, step=0.02, description="V2X 通信时延 (s):", readout_format=".2f", style={"description_width": "140px"})
    slider_gap = widgets.FloatSlider(value=0.6, min=0.3, max=1.4, step=0.1, description="编队期望时距 (s):", readout_format=".1f", style={"description_width": "140px"})
    btn_run = widgets.Button(description="🚀 模拟编队扰动传递", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：通信时延超过多少时后车扰动开始逐级放大（失稳）？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            tau = slider_delay.value
            th = slider_gap.value
            t = np.linspace(0, 15, 301)
            dt = 0.05

            # 头车速度：在 t=3s 时急刹减速 -3m/s2 持续 1.5s，随后恢复
            v0 = 20.0 * np.ones_like(t)
            a0 = np.zeros_like(t)
            for i in range(len(t)):
                if 2.5 <= t[i] < 4.0:
                    a0[i] = -3.0
                elif 4.0 <= t[i] < 5.5:
                    a0[i] = 3.0
                if i > 0:
                    v0[i] = v0[i-1] + a0[i-1] * dt

            # 4车编队仿真 (Car 0, 1, 2, 3)
            # 传递增益模型：G = (1 + Kff*s)/(1 + Th*s + 0.5*s^2) * e^(-s*tau)
            # 经验弦稳定判据：当 tau > 0.18 或 th 过小时，增益 > 1.0 (失稳)
            gain = (1.0 + 3.5 * tau) / (1.0 + 0.8 * (th - 0.5))

            v = np.zeros((4, len(t)))
            v[0, :] = v0
            peak_decel = [3.0]

            for car in range(1, 4):
                amp = 3.0 * (gain ** car)
                peak_decel.append(round(amp, 2))
                shift_idx = int((car * th + car * tau) / dt)
                v_car = 20.0 * np.ones_like(t)
                for i in range(len(t)):
                    orig_idx = i - shift_idx
                    if 0 <= orig_idx < len(t):
                        # 扰动波动
                        delta = (v0[orig_idx] - 20.0) * (gain ** car)
                        v_car[i] = 20.0 + delta
                v[car, :] = v_car

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            colors = ["#0f172a", "#2563eb", "#f59e0b", "#dc2626"]
            for car in range(4):
                c_name = "领航车" if car == 0 else f"跟驰车 {car}"
                ax1.plot(t, v[car, :], color=colors[car], linewidth=2.0 if car==0 else 1.8, label=f"Car {car} ({c_name})")
            ax1.set_xlabel("时间 (s)")
            ax1.set_ylabel("车速 (m/s)")
            ax1.set_title("4车编队车速扰动传递曲线")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            bars = ax2.bar([f"Car {i}" for i in range(4)], peak_decel, color=colors, width=0.5)
            ax2.axhline(3.0, color="#64748b", linestyle="--", label="头车扰动基准 (3.0 m/s²)")
            ax2.set_ylabel("最大减速度峰值 (m/s²)")
            ax2.set_title("车队减速度峰值传递 (弦稳定性)")
            for b in bars:
                ax2.text(b.get_x() + b.get_width()/2., b.get_height() + 0.1, f"{b.get_height():.2f}", ha="center", va="bottom", fontweight="bold")
            ax2.grid(True, axis="y", alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            stable = gain <= 1.05
            if stable:
                badge_text = f"🟢 弦稳定 (扰动衰减率 {(1.0-gain)*100:.1f}%)"
                badge_color = "green"
                insight = "<b>车队弦稳定 (String Stable)</b>：后车减速波动逐级减弱收敛，车队不会发生‘幽灵堵车’，0.6s 超近车头时距安全可靠！"
            else:
                badge_text = f"🔴 弦失稳 (扰动逐级放大 {(gain-1.0)*100:.1f}%)"
                badge_color = "red"
                insight = f"<b>车队弦失稳 (String Unstable)</b>：通信时延偏大导致前馈信息滞后，第 3 辆车制动峰值达到 {peak_decel[3]:.1f} m/s²（比头车放大 {(peak_decel[3]/3.0-1)*100:.0f}%），极易在队尾引发追尾！"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else "#dc2626")}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 B3 CACC 编队弦稳定性研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else "#fee2e2")}; color: {("#15803d" if badge_color=="green" else "#dc2626")}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>扰动放大因子 Gain</b>: {gain:.3f} (基准要求: ≤ 1.0$)；<br/>
                    • <b>第 4 辆车制动冲击</b>: {peak_decel[3]:.2f} m/s² (领航头车: 3.00 m/s²)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("B3_sumo_cacc", {
                "experiment": "B3_sumo_cacc",
                "mode": "novice_preview",
                "v2x_delay": slider_delay.value,
                "headway": slider_gap.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 B3 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节 V2X 通信时延与期望时距，观察头车急刹扰动在 4 车队列中的波动收敛情况，理解‘弦稳定性’的核心本质。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_delay, slider_gap, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 19. B5: 干线绿波带协调控制探索器
# ==============================================================================

def show_b5_explorer():
    """B5 干线多交叉口绿波带协调直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_offset = widgets.IntSlider(value=24, min=0, max=60, step=2, description="信号相位差 (s):", style={"description_width": "120px"})
    slider_speed = widgets.IntSlider(value=50, min=30, max=70, step=5, description="绿波巡航速度 (km/h):", style={"description_width": "150px"})
    btn_run = widgets.Button(description="🚀 绘制干线时空图", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：车速 50km/h 且路口间距 400m 时，最佳相位差是多少？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            offset = slider_offset.value
            v_des = slider_speed.value / 3.6 # m/s
            cycle = 60.0
            green_len = 30.0
            d_inter = 400.0 # 400m 间距，共 3 个路口 (0, 400, 800)

            # 理论最佳相位差：delta_phi = d / v
            ideal_offset = (d_inter / v_des) % cycle
            offset_err = abs(offset - ideal_offset)

            # 绿波带宽估算 (max 30s)
            bandwidth = max(0.0, green_len - offset_err)

            # 车辆行驶轨迹
            t_traj = np.linspace(0, 80, 401)
            x_traj = v_des * t_traj

            fig, ax = plt.subplots(figsize=(12, 4.2))
            # 绘制 3 个路口的红绿灯周期 (x=0, x=400, x=800)
            inter_pos = [0.0, 400.0, 800.0]
            stops = 0

            for idx, x_p in enumerate(inter_pos):
                phi = (idx * offset) % cycle
                for c_start in range(-60, 120, int(cycle)):
                    g_start = c_start + phi
                    g_end = g_start + green_len
                    ax.plot([g_start, g_end], [x_p, x_p], color="#16a34a", linewidth=6, solid_capstyle="butt", label="绿灯放行" if idx==0 and c_start==0 else "")
                    ax.plot([g_end, g_start + cycle], [x_p, x_p], color="#dc2626", linewidth=3, solid_capstyle="butt", label="红灯禁行" if idx==0 and c_start==0 else "")

                # 检查车辆在通过该路口时是否遇到红灯
                t_cross = x_p / v_des
                phase_at_cross = (t_cross - (idx * offset)) % cycle
                if phase_at_cross > green_len:
                    stops += 1

            # 绘制设计绿波带 (绿色半透明多边形)
            t_band_start = 0.0
            t_band_end = t_band_start + bandwidth
            if bandwidth > 0:
                ax.fill_betweenx([0.0, 800.0], [t_band_start, t_band_start + 800.0/v_des], [t_band_end, t_band_end + 800.0/v_des], color="#86efac", alpha=0.35, label=f"畅行绿波带 ({bandwidth:.1f}s)")

            # 车辆真实轨迹
            ax.plot(t_traj, x_traj, color="#1e40af", linewidth=2.5, linestyle="--", label=f"车辆巡航轨迹 ({slider_speed.value} km/h)")

            ax.set_xlim(0, 80)
            ax.set_ylim(-20, 850)
            ax.set_xlabel("时间 (s)")
            ax.set_ylabel("干线距离 (m)")
            ax.set_title(f"干线绿波时空推演图 (XT Diagram) —— 相位差 ΔΦ={offset}$s")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend(loc="upper left")

            plt.tight_layout()
            plt.show()

            if stops == 0 and bandwidth >= 15.0:
                badge_text = f"🟢 完美双向绿波畅行 (带宽 {bandwidth:.1f}s, 0 次停车)"
                badge_color = "green"
                insight = f"<b>最佳配时</b>：相位差 {offset}s 与巡航速度 {slider_speed.value} km/h 完美共振！车辆在所有 3 个路口均在绿灯期间畅行穿过，全程零停顿！"
            elif stops == 0:
                badge_text = f"🟡 窄带宽绿波通行 (带宽 {bandwidth:.1f}s, 0 次停车)"
                badge_color = "yellow"
                insight = "<b>边缘绿波</b>：虽然实现了 0 次停车，但绿波带较窄，稍有车流波动或起步慢就会被下一个路口的红灯截断。"
            else:
                badge_text = f"🔴 绿波断裂 ({stops} 次被红灯截停)"
                badge_color = "red"
                insight = f"<b>信号脱节</b>：当前相位差导致车辆到达路口时刚好迎面撞上下游红灯（需停车等待），失去了干线协调意义。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 B5 干线绿波协调指标研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>干线绿波可用带宽</b>: {bandwidth:.1f} 秒 (理论上限: 30.0s)；<br/>
                    • <b>理论最优相位差参考</b>: {ideal_offset:.1f} 秒 (当前偏差: {offset_err:.1f}s)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("B5_green_wave", {
                "experiment": "B5_green_wave",
                "mode": "novice_preview",
                "offset": slider_offset.value,
                "speed": slider_speed.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 B5 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节相邻交叉口相位差与设计车速，观察干线 XT 时空图中的连续放行带宽，实现从起点到终点‘一路绿灯零停车’。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_offset, slider_speed, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 20. C4: PHEV 能量管理策略对比探索器
# ==============================================================================

def show_c4_explorer():
    """C4 PHEV 能量管理策略对比直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_s = widgets.FloatSlider(value=2.6, min=2.0, max=3.5, step=0.1, description="ECMS 等效因子 s:", readout_format=".1f", style={"description_width": "140px"})
    slider_soc0 = widgets.FloatSlider(value=0.6, min=0.35, max=0.85, step=0.05, description="初始电池 SOC:", readout_format=".2f", style={"description_width": "130px"})
    btn_run = widgets.Button(description="🚀 推演能量管理动力流", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：等效因子 s 偏大时电池 SOC 为什么不降反升？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            s_val = slider_s.value
            soc0 = slider_soc0.value
            dist_km = np.linspace(0, 100, 201)

            # CD/CS 朴素规则策略轨迹
            soc_cd_cs = np.zeros_like(dist_km)
            for i, d in enumerate(dist_km):
                if soc0 - (d / 60.0) * 0.4 > 0.3:
                    soc_cd_cs[i] = soc0 - (d / 60.0) * 0.4 # CD 纯电段
                else:
                    soc_cd_cs[i] = 0.30 + 0.01 * np.sin(d) # CS 保持段

            # ECMS 优化策略轨迹 (等效因子 s 决定了用电 vs 用油的权重)
            # s=2.6 为黄金平衡点 (ΔSOC ≈ 0)
            soc_ecms = np.zeros_like(dist_km)
            delta_slope = (2.6 - s_val) * 0.003
            for i, d in enumerate(dist_km):
                soc_ecms[i] = max(0.2, min(0.9, soc0 + delta_slope * d + 0.02 * np.sin(d/5.0)))

            # 油耗估算
            fuel_cd_cs = 3.65 # L/100km
            fuel_ecms = max(1.8, 2.14 + (s_val - 2.6) * 0.9)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(dist_km, soc_cd_cs, color="#94a3b8", linestyle="--", linewidth=2.0, label="规则策略 (CD/CS)")
            ax1.plot(dist_km, soc_ecms, color="#2563eb", linewidth=2.2, label=f"ECMS 优化策略 (s={s_val:.1f})")
            ax1.axhline(0.3, color="#f43f5e", linestyle=":", label="SOC 保护下限 (0.3)")
            ax1.set_xlabel("行驶里程 (km)")
            ax1.set_ylabel("电池荷电状态 (SOC)")
            ax1.set_title("电池 SOC 全程演化轨迹对比")
            ax1.set_ylim(0.2, 0.9)
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            bars = ax2.bar(["朴素 CD/CS 规则", f"ECMS 策略 (s={s_val:.1f})"], [fuel_cd_cs, fuel_ecms], color=["#94a3b8", "#2563eb"], width=0.45)
            ax2.set_ylabel("百公里综合油耗 (L/100km)")
            ax2.set_title("整车能耗经济性对比")
            for b in bars:
                ax2.text(b.get_x() + b.get_width()/2., b.get_height() + 0.1, f"{b.get_height():.2f} L", ha="center", va="bottom", fontweight="bold")
            ax2.grid(True, axis="y", alpha=0.3, linestyle="--")

            plt.tight_layout()
            plt.show()

            delta_soc = soc_ecms[-1] - soc0
            if abs(delta_soc) <= 0.05:
                badge_text = "🟢 SOC 终值平衡且油耗最低"
                badge_color = "green"
                insight = f"<b>黄金平衡</b>：等效因子 s={s_val:.1f} 完美拟合了油电边际等效汇率！全程电池 SOC 波动保持平衡（ΔSOC={delta_soc:+.2f}），百公里油耗仅 {fuel_ecms:.2f}L，节油超 35%！"
            elif delta_soc < -0.05:
                badge_text = "🟡 偏向用电 (SOC 亏电漂移)"
                badge_color = "yellow"
                insight = f"<b>用电偏向</b>：s 偏小导致算法认为‘电极度便宜’，过度透支电池电量（ΔSOC={delta_soc:+.2f}）。虽表显油耗低，但破坏了能量自持平衡。"
            else:
                badge_text = "🟠 偏向用油 (发动机过度发电)"
                badge_color = "yellow"
                insight = f"<b>用油偏向</b>：s 偏大导致算法认为‘电非常昂贵’，频繁强开辟发动机倒灌发电（ΔSOC={delta_soc:+.2f}），导致油耗恶化至 {fuel_ecms:.2f}L。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else "#b45309")}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 C4 PHEV 能量管理动力流研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else "#fef3c7")}; color: {("#15803d" if badge_color=="green" else "#b45309")}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>SOC 终值漂移</b>: {delta_soc:+.3f} (理想目标: $\approx 0.00$)；<br/>
                    • <b>相比 CD/CS 规则节油</b>: {(fuel_cd_cs - fuel_ecms)/fuel_cd_cs*100:.1f}%；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("C4_ems_comparison", {
                "experiment": "C4_ems_comparison",
                "mode": "novice_preview",
                "s_equiv": slider_s.value,
                "init_soc": slider_soc0.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 C4 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节 ECMS 等效因子 s，观察 SOC 终值平衡与油耗对比，理解等效因子作为‘油电汇率’对动力流分配的核心作用。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_s, slider_soc0, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 21. D3: 电池 OCV-SOC 开路电压特性探索器
# ==============================================================================

def show_d3_explorer():
    """D3 电池 OCV-SOC 静态特性曲线直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_crate = widgets.FloatSlider(value=0.05, min=0.02, max=0.40, step=0.02, description="充放电倍率 (C):", readout_format=".2f", style={"description_width": "130px"})
    slider_relax = widgets.IntSlider(value=40, min=10, max=60, step=5, description="静置弛豫时长 (min):", style={"description_width": "140px"})
    btn_run = widgets.Button(description="🚀 辨识准静态 OCV", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：倍率从 0.3C 降到 0.05C 时，充放电电压迟滞环如何变化？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            c = slider_crate.value
            r_min = slider_relax.value
            soc = np.linspace(0.05, 0.95, 201)

            # 理论真实 OCV(SOC) 曲线 (NMC 三元锂体系)
            ocv_true = 3.2 + 0.8 * soc - 0.1 * np.log(1.0 - soc) + 0.05 * np.log(soc)

            # 极化过电位与内阻压降：电流越大、弛豫越短，迟滞环张开得越大
            r0 = 0.025 # 欧姆内阻
            eta_pol = (c * 0.15) * (1.0 - r_min / 90.0)
            v_chg = ocv_true + c * r0 + eta_pol
            v_dis = ocv_true - c * r0 - eta_pol

            # 迟滞间距
            gap_mv = (v_chg - v_dis) * 1000.0

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(soc * 100, v_chg, color="#dc2626", linewidth=2.0, label="充电分支端电压")
            ax1.plot(soc * 100, v_dis, color="#2563eb", linewidth=2.0, label="放电分支端电压")
            ax1.plot(soc * 100, ocv_true, color="#16a34a", linestyle="--", linewidth=2.2, label="真实准静态平衡 OCV")
            ax1.set_xlabel("荷电状态 SOC (%)")
            ax1.set_ylabel("端电压 (V)")
            ax1.set_title(f"OCV-SOC 充放电迟滞环 ({c:.2f}C 倍率, 静置 {r_min}min)")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            ax2.plot(soc * 100, gap_mv, color="#f59e0b", linewidth=2.2)
            ax2.axhline(20.0, color="#16a34a", linestyle="--", label="工业高精度阈值 (20 mV)")
            ax2.set_xlabel("荷电状态 SOC (%)")
            ax2.set_ylabel("迟滞电压差 ΔV (mV)")
            ax2.set_title("充放电电化学极化迟滞压差")
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            mean_gap = np.mean(gap_mv)
            if mean_gap <= 25.0:
                badge_text = f"🟢 准静态收敛达标 (平均迟滞 {mean_gap:.1f} mV)"
                badge_color = "green"
                insight = "<b>高精度标定达成</b>：小倍率慢充放与充分静置使电化学浓差极化基本消退，充放电曲线高度贴合，成功提取出黄金准静态 OCV 曲线！"
            else:
                badge_text = f"🔴 极化未消除迟滞过大 (平均迟滞 {mean_gap:.1f} mV)"
                badge_color = "red"
                insight = f"<b>极化残存</b>：当前倍率偏大（{c:.2f}C），电池内部锂离子浓度梯度未平复，导致充放电电压差高达 {mean_gap:.1f} mV，无法作为整车仿真基准。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else "#dc2626")}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 D3 OCV-SOC 标定品质研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else "#fee2e2")}; color: {("#15803d" if badge_color=="green" else "#dc2626")}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>平均充放电迟滞误差</b>: {mean_gap:.1f} mV (高精度阈值: ≤ 20.0$ mV)；<br/>
                    • <b>平台区电压斜率</b>: {np.ptp(ocv_true)/0.9:.2f} V/ΔSOC；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("D3_ocv_soc_export", {
                "experiment": "D3_ocv_soc_export",
                "mode": "novice_preview",
                "c_rate": slider_crate.value,
                "relax_min": slider_relax.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 D3 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节测试倍率与静置弛豫时长，观察充放电迟滞环张开与闭合过程，理解准静态开路电压提取的电化学机理。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_crate, slider_relax, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 22. E1: 主减速器传动比动力性 vs 经济性寻优探索器
# ==============================================================================

def show_e1_explorer():
    """E1 单目标参数寻优直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_i0 = widgets.FloatSlider(value=9.0, min=6.0, max=12.0, step=0.5, description="主减速比 i0:", readout_format=".1f", style={"description_width": "120px"})
    btn_run = widgets.Button(description="🚀 测算动力经济性", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：满足百公里加速 < 7.5s 时，电耗最低的最优速比是多少？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            cur_i0 = slider_i0.value
            ratios = np.linspace(6.0, 12.0, 61)

            # 动力学经验推演：
            # 0-100 加速时间随传动比增大而缩短 (扭矩放大)，但受电机最高转速与附着力限制
            accel_times = 14.0 * (6.0 / ratios)**0.65
            # 电耗随传动比增大而增加 (电机长期在高转速低效区工作)
            energies = 11.2 + 0.55 * (ratios - 6.0)

            cur_accel = 14.0 * (6.0 / cur_i0)**0.65
            cur_energy = 11.2 + 0.55 * (cur_i0 - 6.0)

            fig, ax1 = plt.subplots(figsize=(10, 4.0))
            color1 = "#2563eb"
            ax1.set_xlabel("主减速器传动比 $i_0$")
            ax1.set_ylabel("百公里加速时间 $t_{0-100}$ (s)", color=color1)
            line1 = ax1.plot(ratios, accel_times, color=color1, linewidth=2.2, label="加速时间 (越短越快)")
            ax1.tick_params(axis="y", labelcolor=color1)
            ax1.axhline(7.5, color=color1, linestyle=":", alpha=0.6, label="动力性设计上限 (7.5s)")

            ax2 = ax1.twinx()
            color2 = "#dc2626"
            ax2.set_ylabel("百公里综合电耗 (kWh/100km)", color=color2)
            line2 = ax2.plot(ratios, energies, color=color2, linewidth=2.2, linestyle="--", label="综合电耗 (越低越省)")
            ax2.tick_params(axis="y", labelcolor=color2)

            # 当前选择速比垂直指示线
            ax1.axvline(cur_i0, color="#16a34a", linewidth=2.0, label=f"当前速比 ({cur_i0:.1f})")

            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc="upper center")
            ax1.set_title("电动车主减速比权衡：动力加速性 vs 百公里能耗")
            ax1.grid(True, alpha=0.3, linestyle="--")

            plt.tight_layout()
            plt.show()

            if cur_accel <= 7.5 and cur_energy <= 13.0:
                badge_text = "🟢 黄金平衡速比点 (动力达标且省电)"
                badge_color = "green"
                insight = f"<b>最优折中</b>：传动比 {cur_i0:.1f} 既将百公里加速压入 {cur_accel:.2f}s（满足动力性要求），又避免了电机过分高速运转，电耗控制在 {cur_energy:.2f} kWh！"
            elif cur_accel > 7.5:
                badge_text = "🟠 动力不足 (加速超过 7.5s)"
                badge_color = "yellow"
                insight = f"<b>速比过小</b>：传动比仅 {cur_i0:.1f} 导致轮端起步扭矩匮乏，0-100 加速耗时高达 {cur_accel:.2f}s，无法满足整车动力性设计指标。"
            else:
                badge_text = "🔴 过于激进 (电耗剧增)"
                badge_color = "red"
                insight = f"<b>速比过大</b>：传动比达到 {cur_i0:.1f} 虽然加速迅猛（{cur_accel:.2f}s），但高速电机转速过高导致摩擦损耗暴增，百公里电耗恶化至 {cur_energy:.2f} kWh。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 E1 速比单目标优化研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>0-100 km/h 加速时间</b>: {cur_accel:.2f} 秒 (指标门槛: ≤ 7.5$s)；<br/>
                    • <b>百公里综合电耗</b>: {cur_energy:.2f} kWh/100km；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("E1_single_objective", {
                "experiment": "E1_single_objective",
                "mode": "novice_preview",
                "gear_ratio": slider_i0.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 E1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节主减速比，观察动力加速性与能耗经济性的双曲线反向制约关系，找出兼顾动力性与节能的最优折中速比。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_i0, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 23. F1: FMI/FMU 模型加载与通信步长效应探索器
# ==============================================================================

def show_f1_explorer():
    """F1 FMI 联合仿真通信步长效应直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_step = widgets.FloatSlider(value=0.02, min=0.002, max=0.10, step=0.005, description="通信步长 h (s):", readout_format=".3f", style={"description_width": "130px"})
    btn_run = widgets.Button(description="🚀 模拟 FMU 离散积分", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：通信步长超过多少秒时数值截断误差开始显著发散？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            h = slider_step.value
            t_total = 3.0
            t_dense = np.linspace(0, t_total, 601)
            # 一阶惯性系统真实解析解: y(t) = 1 - e^(-5t)
            omega = 8.0
            y_true = 1.0 - np.exp(-omega * t_dense)

            # FMU 离散 Euler 前向通信步长采样
            t_fmu = np.arange(0, t_total + h, h)
            y_fmu = np.zeros_like(t_fmu)
            for i in range(len(t_fmu) - 1):
                y_fmu[i+1] = y_fmu[i] + h * omega * (1.0 - y_fmu[i])

            # 最大绝对误差
            y_true_interp = 1.0 - np.exp(-omega * t_fmu)
            errs = np.abs(y_fmu - y_true_interp)
            max_err = np.max(errs)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(t_dense, y_true, color="#16a34a", linewidth=2.5, label="连续真实解析解")
            ax1.step(t_fmu, y_fmu, where="post", color="#2563eb", linewidth=1.8, label=f"FMU 离散通信 (h={h:.3f}s)")
            ax1.set_xlabel("时间 (s)")
            ax1.set_ylabel("系统输出 y(t)")
            ax1.set_title("FMI 联合仿真步长效应与动态跟踪")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            ax2.plot(t_fmu, errs * 1000.0, color="#dc2626", linewidth=2.0)
            ax2.axhline(50.0, color="#f59e0b", linestyle="--", label="工业高精度门槛 (50 mV)")
            ax2.set_xlabel("时间 (s)")
            ax2.set_ylabel("离散截断绝对误差 (mV)")
            ax2.set_title("通信步长引起的数值积分截断误差")
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            if max_err <= 0.05:
                badge_text = f"🟢 高精度稳定收敛 (最大误差 {max_err*1000:.1f} mV)"
                badge_color = "green"
                insight = f"<b>优质步长</b>：步长 h={h:.3f}s 足够精细，主算法在每一个通信点均精确捕捉到动态响应，数值截断误差微乎其微。"
            elif max_err <= 0.20:
                badge_text = f"🟡 精度退化 (最大误差 {max_err*1000:.1f} mV)"
                badge_color = "yellow"
                insight = f"<b>步长偏大</b>：通信点间隔过宽导致阶段性超调与相位滞后，误差达到 {max_err*1000:.1f} mV，建议缩小步长以防高频振荡。"
            else:
                badge_text = f"🔴 数值发散振荡 (最大误差 {max_err*1000:.1f} mV)"
                badge_color = "red"
                insight = f"<b>步长越界</b>：步长已超过稳定性理论极限 (h > 2/omega)，Euler 积分发生剧烈发散振荡！联合仿真失真！"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 F1 FMU 通信步长数值特性研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>最大截断误差</b>: {max_err*1000:.1f} mV (高精度阈值: ≤ 50.0$ mV)；<br/>
                    • <b>联合仿真离散采样点数</b>: {len(t_fmu)} 个点；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("F1_fmu_load", {
                "experiment": "F1_fmu_load",
                "mode": "novice_preview",
                "comm_step": slider_step.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 F1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节 FMI 联合仿真主通信步长 h，对比解析真值与 FMU 离散采样阶跃响应，理解协同仿真中通信步长对数值稳定性的决定性影响。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_step, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 24. F2: OpenModelica 多物理域阶跃响应探索器
# ==============================================================================

def show_f2_explorer():
    """F2 OpenModelica 阶跃响应直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_wn = widgets.FloatSlider(value=4.0, min=1.0, max=10.0, step=0.5, description="自然频率 wn (rad/s):", readout_format=".1f", style={"description_width": "150px"})
    slider_zeta = widgets.FloatSlider(value=0.5, min=0.1, max=1.5, step=0.1, description="阻尼比 zeta:", readout_format=".1f", style={"description_width": "130px"})
    btn_run = widgets.Button(description="🚀 模拟二阶机电响应", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：阻尼比从 0.2 调到 0.8 时，系统的超调量和振荡如何变化？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            wn = slider_wn.value
            z = slider_zeta.value
            t = np.linspace(0, 4.0, 401)

            # 二阶系统阶跃响应: G(s) = wn^2 / (s^2 + 2*z*wn*s + wn^2)
            if z < 1.0:
                wd = wn * np.sqrt(1.0 - z**2)
                phi = np.arccos(z)
                y = 1.0 - (np.exp(-z * wn * t) / np.sqrt(1.0 - z**2)) * np.sin(wd * t + phi)
                overshoot = np.exp(-np.pi * z / np.sqrt(1.0 - z**2)) * 100.0
            else:
                s1 = -wn * (z - np.sqrt(z**2 - 1.0))
                s2 = -wn * (z + np.sqrt(z**2 - 1.0))
                y = 1.0 + (s2 * np.exp(s1 * t) - s1 * np.exp(s2 * t)) / (s1 - s2)
                overshoot = 0.0

            fig, ax = plt.subplots(figsize=(10, 3.8))
            ax.plot(t, y, color="#2563eb", linewidth=2.2, label=f"系统响应 (wn={wn:.1f}, zeta={z:.1f})")
            ax.axhline(1.0, color="#16a34a", linestyle="--", label="稳态目标值 (1.0)")
            ax.axhline(1.0 + overshoot/100.0, color="#dc2626", linestyle=":", label=f"峰值超调 ({overshoot:.1f}%)" if overshoot>0 else "")
            ax.set_xlabel("时间 (s)")
            ax.set_ylabel("物理量幅值")
            ax.set_title("OpenModelica 二阶机电系统阶跃时域响应")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend()

            plt.tight_layout()
            plt.show()

            if z < 0.4:
                badge_text = f"🔴 欠阻尼强振荡 (超调 {overshoot:.1f}%)"
                badge_color = "red"
                insight = "<b>强振荡</b>：阻尼过小导致动能无法被耗散，系统发生剧烈机械超调与来回震荡，易对底盘构件造成交变疲劳损伤。"
            elif 0.6 <= z <= 0.8:
                badge_text = f"🟢 最佳工程阻尼 (超调 {overshoot:.1f}%, 快速收敛)"
                badge_color = "green"
                insight = "<b>工程黄金阻尼</b>：阻尼比处于 0.7 左右时，系统兼顾快速响应与微小超调，是机电悬架与电机扭矩闭环的标准标定点。"
            else:
                badge_text = "🟡 过阻尼迟缓响应 (无超调)"
                badge_color = "yellow"
                insight = "<b>响应迟缓</b>：阻尼过大虽然杜绝了超调，但系统动作迟钝，无法及时跟上动态控制指令。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 F2 机电动力学时域特性研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>最大超调量 Mp</b>: {overshoot:.1f}% (工程推荐: ≤ 15.0$%)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("F2_openmodelica_fmu", {
                "experiment": "F2_openmodelica_fmu",
                "mode": "novice_preview",
                "wn": slider_wn.value,
                "zeta": slider_zeta.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 F2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节自然频率与阻尼比，观察阶跃时域响应超调与收敛速度，建立多物理域机电系统的经典阻尼直觉。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_wn, slider_zeta, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 25. F3: 多 FMU 协同 Master 算法步长与解耦探索器
# ==============================================================================

def show_f3_explorer():
    """F3 多 FMU 协同 Master 算法直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_dt = widgets.FloatSlider(value=0.02, min=0.005, max=0.15, step=0.005, description="Master 协同周期 (s):", readout_format=".3f", style={"description_width": "150px"})
    drp_algo = widgets.Dropdown(options=["Jacobi 并行弱耦合 (易代数环漂移)", "Gauss-Seidel 串行预测 (高精度收敛)"], value="Jacobi 并行弱耦合 (易代数环漂移)", description="协同算法:", style={"description_width": "90px"})
    btn_run = widgets.Button(description="🚀 测算能量耦合误差", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：Gauss-Seidel 相比 Jacobi 为什么能在更大协同周期下保持能量守恒？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            dt = slider_dt.value
            is_gs = "Gauss-Seidel" in drp_algo.value
            t = np.linspace(0, 5.0, 201)

            # 车辆动力学 FMU 与 电池总成 FMU 双向能量交换误差
            # Jacobi 算法的代数环延迟产生虚假能量注入: E_err ~ dt^1
            # Gauss-Seidel 包含一步内插补偿: E_err ~ dt^2
            coef = 120.0 if not is_gs else 25.0
            power = 1.0 if not is_gs else 2.0
            err_curve = coef * (dt ** power) * t

            fig, ax = plt.subplots(figsize=(10, 3.8))
            ax.plot(t, err_curve, color="#2563eb" if is_gs else "#dc2626", linewidth=2.2, label=drp_algo.value.split()[0])
            ax.axhline(5.0, color="#16a34a", linestyle="--", label="能量守恒容许门槛 (5.0 J)")
            ax.set_xlabel("仿真时间 (s)")
            ax.set_ylabel("代数环虚假能量漂移 (J)")
            ax.set_title("多 FMU 协同 Master 算法数值能量守恒对比")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend()

            plt.tight_layout()
            plt.show()

            max_e = err_curve[-1]
            if max_e <= 5.0:
                badge_text = f"🟢 能量守恒严密 (终值漂移 {max_e:.2f} J)"
                badge_color = "green"
                insight = "<b>高保真协同</b>：主算法在通信点间通过预测解耦了代数环，消除了虚假能量注入，多从站联合仿真高度真实！"
            elif max_e <= 15.0:
                badge_text = f"🟡 存在轻微能量虚假漂移 ({max_e:.2f} J)"
                badge_color = "yellow"
                insight = "<b>轻度漂移</b>：主算法协同周期略大，两个 FMU 从站间的耦合变量存在单步延迟，导致出现微量非物理能量膨胀。"
            else:
                badge_text = f"🔴 代数环严重发散 ({max_e:.2f} J)"
                badge_color = "red"
                insight = "<b>代数环失稳</b>：Jacobi 并行算法无法处理紧密双向耦合，步长过大导致虚假能量无限累积，整车仿真数据失效！"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 F3 多 FMU 协同数值能量研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>能量漂移终值</b>: {max_e:.2f} 焦耳 (允许门限: ≤ 5.0$ J)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("F3_multi_fmu", {
                "experiment": "F3_multi_fmu",
                "mode": "novice_preview",
                "master_step": slider_dt.value,
                "algorithm": drp_algo.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 F3 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：切换 Master 协同解耦算法与协同周期，观察代数环带来的非物理能量漂移，体会分布式多系统联合仿真的通信机制。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_dt, drp_algo, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 26. G1: ROS 2 话题发布与 DDS QoS 网络性能探索器
# ==============================================================================

def show_g1_explorer():
    """G1 ROS 2 话题发布与 DDS QoS 直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_freq = widgets.IntSlider(value=50, min=10, max=100, step=10, description="感知发布频率 (Hz):", style={"description_width": "140px"})
    slider_loss = widgets.FloatSlider(value=5.0, min=0.0, max=30.0, step=2.5, description="无线丢包率 (%):", readout_format=".1f", style={"description_width": "130px"})
    btn_run = widgets.Button(description="🚀 测算 DDS 传输延迟", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：发布频率达到 100Hz 且存在丢包时，端到端延迟抖动为何加剧？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            freq = slider_freq.value
            loss_rate = slider_loss.value / 100.0

            # 模拟 100 帧感知报文传输
            n_packets = 100
            delays = []
            np.random.seed(42)
            base_delay = 5.0 + (freq / 100.0) * 8.0 # 排队时延
            for i in range(n_packets):
                is_lost = np.random.rand() < loss_rate
                if is_lost:
                    # 重传时延
                    delays.append(base_delay + 25.0 + np.random.exponential(10.0))
                else:
                    delays.append(base_delay + np.random.normal(0, 1.2))

            delays = np.maximum(2.0, np.array(delays))
            mean_d = np.mean(delays)
            max_d = np.max(delays)

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 3.8))
            ax1.plot(range(n_packets), delays, color="#2563eb", linewidth=1.2, marker="o", markersize=3, label="单帧到达时延")
            ax1.axhline(20.0, color="#f59e0b", linestyle="--", label="实车控制延迟红线 (20ms)")
            ax1.set_xlabel("数据包序号")
            ax1.set_ylabel("端到端传输时延 (ms)")
            ax1.set_title(f"ROS 2 话题实时通信时延序列 ({freq} Hz)")
            ax1.grid(True, alpha=0.3, linestyle="--")
            ax1.legend()

            ax2.hist(delays, bins=15, color="#38bdf8", edgecolor="#0284c7")
            ax2.axvline(mean_d, color="#dc2626", linewidth=2.0, label=f"平均时延 ({mean_d:.1f}ms)")
            ax2.set_xlabel("时延区间 (ms)")
            ax2.set_ylabel("频数分布")
            ax2.set_title("DDS 网络抖动分布直方图")
            ax2.grid(True, alpha=0.3, linestyle="--")
            ax2.legend()

            plt.tight_layout()
            plt.show()

            if mean_d <= 15.0 and max_d <= 35.0:
                badge_text = "🟢 实时性优异 (满足底盘闭环)"
                badge_color = "green"
                insight = "<b>低延迟通信</b>：网络带宽充足且丢包率低，DDS 队列无堆积，感知数据在 15ms 内瞬时触达控制器。"
            elif mean_d <= 25.0:
                badge_text = "🟡 存在偶发重传抖动"
                badge_color = "yellow"
                insight = "<b>边缘抖动</b>：无线网络存在偶发丢包，触发了可靠性重传机制，导致个别报文时延突增至 30ms 以上。"
            else:
                badge_text = "🔴 严重通信拥塞超时"
                badge_color = "red"
                insight = "<b>严重滞后</b>：高频率与高丢包引发网络排队风暴，平均时延超标，无法满足智能驾驶纵向控制的实时性要求！"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 G1 ROS 2 话题通信 QoS 研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>平均端到端时延</b>: {mean_d:.1f} ms (峰值抖动: {max_d:.1f} ms)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("G1_ros_topics", {
                "experiment": "G1_ros_topics",
                "mode": "novice_preview",
                "freq": slider_freq.value,
                "loss": slider_loss.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 G1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节发布频率与网络丢包率，观察 DDS 通信端到端时延与抖动分布，理解智能网联自动驾驶中间件的 QoS 选型权衡。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_freq, slider_loss, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 27. G2: ROS 2 服务通信超时与重试探索器
# ==============================================================================

def show_g2_explorer():
    """G2 ROS 2 服务通信超时重试直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_timeout = widgets.FloatSlider(value=0.2, min=0.05, max=0.6, step=0.05, description="服务超时时间 (s):", readout_format=".2f", style={"description_width": "140px"})
    slider_retries = widgets.IntSlider(value=2, min=1, max=5, step=1, description="最大重试次数:", style={"description_width": "120px"})
    btn_run = widgets.Button(description="🚀 模拟底盘 RPC 请求", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：超时时间设置过短为什么会导致底盘指令频繁重试风暴？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            timeout = slider_timeout.value
            max_r = slider_retries.value

            # 模拟底盘 ECU 响应时间分布 (期望 0.15s, 方差 0.08s)
            np.random.seed(33)
            ecu_time = 0.16 + np.random.exponential(0.06)

            success = False
            total_time = 0.0
            attempts = 0

            for r in range(max_r):
                attempts += 1
                if timeout >= ecu_time:
                    success = True
                    total_time += ecu_time
                    break
                else:
                    total_time += timeout
                    # 下一次尝试
                    ecu_time = 0.14 + np.random.exponential(0.04)

            fig, ax = plt.subplots(figsize=(10, 3.8))
            labels = ["本次执行耗时", "超时阈值", "ECU 处理基准"]
            vals = [total_time * 1000.0, timeout * 1000.0, 160.0]
            colors = ["#16a34a" if success else "#dc2626", "#64748b", "#38bdf8"]
            bars = ax.bar(labels, vals, color=colors, width=0.45)
            ax.set_ylabel("毫秒 (ms)")
            ax.set_title(f"ROS 2 Service 请求/响应时序剖析 (尝试次数: {attempts}/{max_r})")
            for b in bars:
                ax.text(b.get_x() + b.get_width()/2., b.get_height() + 5.0, f"{b.get_height():.1f}ms", ha="center", va="bottom", fontweight="bold")
            ax.grid(True, axis="y", alpha=0.3, linestyle="--")

            plt.tight_layout()
            plt.show()

            if success and attempts == 1:
                badge_text = f"🟢 瞬时响应成功 ({total_time*1000:.1f}ms)"
                badge_color = "green"
                insight = "<b>高效率匹配</b>：超时阈值合理宽裕，ECU 在第 1 次调用内即返回控制确认，通信零重传、闭环控制极度流畅。"
            elif success:
                badge_text = f"🟡 重试后成功 (第 {attempts} 次尝试成功)"
                badge_color = "yellow"
                insight = f"<b>偶发重试</b>：首轮因超时未收到回执，通过第 {attempts} 次重传挽回了请求，但带来了额外的时延开销。"
            else:
                badge_text = "🔴 彻底超时调用失败"
                badge_color = "red"
                insight = "<b>通信风暴死锁</b>：超时阈值过短，所有重试全部遭遇超时截断，底盘未收到控制指令，触发系统保护机制！"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 G2 服务通信可靠性研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>闭环可用状态</b>: {"调用成功" if success else "请求超时放弃"}；<br/>
                    • <b>总消耗时延</b>: {total_time*1000:.1f} ms (尝试 {attempts} 次)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("G2_ros_services", {
                "experiment": "G2_ros_services",
                "mode": "novice_preview",
                "timeout": slider_timeout.value,
                "retries": slider_retries.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 G2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节 RPC 服务超时与最大重试次数，观察客户端/服务端在偶发延迟下的行为响应，理解自动驾驶高可靠服务通信机制。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_timeout, slider_retries, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 28. H1: OpenSCENARIO 参数空间网格扫描与危险度测绘探索器
# ==============================================================================

def show_h1_explorer():
    """H1 场景参数空间危险度测绘直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_d0 = widgets.IntSlider(value=25, min=10, max=50, step=5, description="切入距离 d0 (m):", style={"description_width": "130px"})
    slider_dv = widgets.IntSlider(value=30, min=10, max=50, step=5, description="相对速差 dv (km/h):", style={"description_width": "140px"})
    btn_run = widgets.Button(description="🚀 测绘参数空间危险度", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：相对速差超过多少时切入距离 25m 就会落入严重碰撞红区？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            cur_d = slider_d0.value
            cur_dv = slider_dv.value

            d_grid = np.linspace(10, 50, 41)
            dv_grid = np.linspace(10, 50, 41)
            D, DV = np.meshgrid(d_grid, dv_grid)

            # TTC 危险度计算: TTC = (D - 4.5) / (DV / 3.6)
            TTC = (D - 4.5) / (DV / 3.6)
            cur_ttc = (cur_d - 4.5) / (cur_dv / 3.6)

            fig, ax = plt.subplots(figsize=(10, 4.0))
            # 等高线热力图
            cs = ax.contourf(D, DV, TTC, levels=[0.0, 1.5, 2.5, 4.0, 8.0], colors=["#f87171", "#fbbf24", "#86efac", "#38bdf8"], alpha=0.8)
            cbar = fig.colorbar(cs, ax=ax)
            cbar.set_label("TTC 碰撞预警时间 (秒)")

            # 当前参数散点
            ax.scatter([cur_d], [cur_dv], color="#0f172a", s=140, marker="*", zorder=5, label=f"当前采样工况 (d={cur_d}m, dv={cur_dv}km/h)")
            ax.set_xlabel("加塞切入初始纵向间距 (m)")
            ax.set_ylabel("两车相对逼近速度差 (km/h)")
            ax.set_title("OpenSCENARIO 参数空间全因子危险度测绘图 (安全绿区 / 预警黄区 / 碰撞红区)")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend(loc="upper right")

            plt.tight_layout()
            plt.show()

            if cur_ttc <= 1.5:
                badge_text = f"🔴 极度危险 (TTC={cur_ttc:.2f}s)"
                badge_color = "red"
                insight = "<b>高危死区</b>：切入间距过近且速差巨大，TTC 突破物理制动极限，常规 AEB 无法避免追尾！"
            elif cur_ttc <= 2.5:
                badge_text = f"🟡 临界紧迫工况 (TTC={cur_ttc:.2f}s)"
                badge_color = "yellow"
                insight = "<b>边缘工况</b>：处于自动紧急制动的临界触发边缘，也是算法验证与标定最关键的黄金测试用例点。"
            else:
                badge_text = f"🟢 宽松安全区间 (TTC={cur_ttc:.2f}s)"
                badge_color = "green"
                insight = "<b>安全区域</b>：两车具备充足的时空裕度，自车通过轻微减速即可实现平顺避障。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 H1 场景参数空间测绘研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>工况危险度 TTC</b>: {cur_ttc:.2f} 秒 (紧急制动门槛: ≤ 2.0$s)；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("H1_batch_generation", {
                "experiment": "H1_batch_generation",
                "mode": "novice_preview",
                "cutin_dist": slider_d0.value,
                "speed_delta": slider_dv.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 H1 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节切入距离与相对速差，观察参数空间 TTC 危险度二维等高线热力图，理解批量参数泛化与场景覆盖率测绘。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_d0, slider_dv, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 29. H2: 场景模糊测试 (Fuzzing) 与 SOTIF 边界探索器
# ==============================================================================

def show_h2_explorer():
    """H2 场景模糊测试与 SOTIF 安全边界直觉探索驾驶舱"""
    if not _HAS_WIDGETS:
        return
    out = widgets.Output()

    slider_iters = widgets.IntSlider(value=50, min=20, max=150, step=10, description="变异测试轮数:", style={"description_width": "120px"})
    slider_sigma = widgets.FloatSlider(value=0.3, min=0.1, max=0.8, step=0.1, description="变异扰动方差:", readout_format=".1f", style={"description_width": "130px"})
    btn_run = widgets.Button(description="🚀 执行引导式变异搜索", button_style="primary", icon="play")

    txt_task = widgets.Text(placeholder="回答：变异轮数增加时，模糊测试发现隐蔽碰撞用例的概率如何提升？", description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="60%"))
    btn_checkin = widgets.Button(description="📝 预习打卡保存", button_style="success", icon="check")
    out_checkin = widgets.Output()

    def update_view(_=None):
        with out:
            clear_output(wait=True)
            n = slider_iters.value
            sig = slider_sigma.value

            np.random.seed(42)
            # 种子点 (25, 25)
            pts_d = [30.0]
            pts_dv = [20.0]
            for _ in range(n - 1):
                # 变异步进
                cand_d = pts_d[-1] + np.random.normal(0, sig * 10.0)
                cand_dv = pts_dv[-1] + np.random.normal(0, sig * 10.0)
                cand_d = np.clip(cand_d, 10.0, 50.0)
                cand_dv = np.clip(cand_dv, 10.0, 50.0)
                pts_d.append(cand_d)
                pts_dv.append(cand_dv)

            pts_d = np.array(pts_d)
            pts_dv = np.array(pts_dv)
            ttc = (pts_d - 4.5) / (pts_dv / 3.6)
            crashes = ttc <= 1.6
            n_crashes = np.sum(crashes)

            fig, ax = plt.subplots(figsize=(10, 4.0))
            ax.scatter(pts_d[~crashes], pts_dv[~crashes], color="#2563eb", alpha=0.6, s=40, label="正常避让测试用例")
            if n_crashes > 0:
                ax.scatter(pts_d[crashes], pts_dv[crashes], color="#dc2626", s=80, marker="X", label=f"Fuzzing 捕获碰撞缺陷 ({n_crashes} 个)")
            ax.set_xlabel("切入间距 (m)")
            ax.set_ylabel("相对速差 (km/h)")
            ax.set_title(f"SOTIF 模糊测试变异探索散点图 ({n} 次变异演化)")
            ax.grid(True, alpha=0.3, linestyle="--")
            ax.legend()

            plt.tight_layout()
            plt.show()

            crash_rate = (n_crashes / n) * 100.0
            if n_crashes > 0:
                badge_text = f"🎯 成功检出边界缺陷 (检出率 {crash_rate:.1f}%)"
                badge_color = "green"
                insight = f"<b>高效变异</b>：模糊测试在 {n} 次变异中成功捕获了 {n_crashes} 个导致系统失效的极端长尾工况 (Corner Cases)，验证了预期功能安全 (SOTIF) 边界！"
            else:
                badge_text = "🟡 未触发极限缺陷 (覆盖率尚不足)"
                badge_color = "yellow"
                insight = "<b>扰动保守</b>：当前变异轮数较少或扰动步长较小，测试点均落在安全包络内部，建议增加测试轮数以触碰未知危险区域。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else "#b45309")}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">📊 H2 模糊测试安全边界研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else "#fef3c7")}; color: {("#15803d" if badge_color=="green" else "#b45309")}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>缺陷用例检出数</b>: {n_crashes} 个 (总测试轮数: {n})；<br/>
                    • <b>SOTIF 边界覆盖率</b>: {min(100.0, n * sig * 1.5):.1f}%；<br/>
                    • <b>物理因果分析</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("H2_scenario_fuzzing", {
                "experiment": "H2_scenario_fuzzing",
                "mode": "novice_preview",
                "iters": slider_iters.value,
                "sigma": slider_sigma.value,
                "student_insight": ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 H2 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节变异轮数与扰动强度，观察自适应变异点向 SOTIF 危险边界的演变过程，理解长尾极端场景挖掘的模糊测试本质。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_iters, slider_sigma, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()


# ==============================================================================
# 30. Capstone: 感-算-控-电-网一体化综合探索器
# ==============================================================================

def show_capstone_explorer():
    """Capstone 综合大作业：智能电动汽车一体化避险与能量回收探索器"""
    out = widgets.Output()
    out_checkin = widgets.Output()

    slider_ttc = widgets.FloatSlider(
        value=2.2, min=1.4, max=3.5, step=0.1,
        description="TTC避险阈值(s):", continuous_update=False,
        style={"description_width": "140px"}, layout=widgets.Layout(width="340px")
    )
    slider_headway = widgets.FloatSlider(
        value=1.6, min=1.0, max=2.5, step=0.1,
        description="跟驰安全时距(s):", continuous_update=False,
        style={"description_width": "140px"}, layout=widgets.Layout(width="340px")
    )
    slider_regen = widgets.FloatSlider(
        value=0.50, min=0.0, max=0.85, step=0.05,
        description="制动电回收比:", continuous_update=False,
        style={"description_width": "140px"}, layout=widgets.Layout(width="340px")
    )

    btn_run = widgets.Button(
        description="🚀 综合仿真推演", button_style="primary",
        icon="play", layout=widgets.Layout(width="150px")
    )
    txt_task = widgets.Text(
        placeholder="输入微任务心得：例如当 TTC=2.4s 时自车提前柔和制动，最小车距提升至 6.8m 且回收电能最高...",
        description="微任务心得:", style={"description_width": "100px"}, layout=widgets.Layout(width="600px")
    )
    btn_checkin = widgets.Button(
        description="📝 预习打卡保存", button_style="success",
        icon="check", layout=widgets.Layout(width="150px")
    )

    def update_view(_=None):
        ttc_thresh = slider_ttc.value
        th = slider_headway.value
        regen = slider_regen.value

        dt = 0.1
        t_arr = np.linspace(0, 30.0, 300)

        # 运动学与物理参数
        mass = 1650.0  # kg
        cd_a = 0.28 * 2.2
        f_r = 0.012
        bat_cap_kwh = 60.0

        ego_x = 0.0
        ego_v = 14.0  # 50.4 km/h
        soc = 0.800

        lead_x = 35.0
        lead_v = 11.0

        ego_v_log = []
        lead_v_log = []
        gap_log = []
        accel_log = []
        soc_log = []
        p_bat_log = []
        ttc_log = []

        total_regen_joules = 0.0
        total_traction_joules = 0.0

        for t in t_arr:
            # 加塞车横向轨迹 (t=4.5s 开始变道，t=7.0s 完成加塞进入主车道)
            if t < 4.5:
                lead_y = 3.5
            elif t < 7.0:
                lead_y = 3.5 - 3.5 * ((t - 4.5) / 2.5)
            else:
                lead_y = 0.0

            # 加塞车前向纵向减速工况 (t=12s 前车以 -0.8m/s2 减速至 8m/s)
            if t >= 12.0 and lead_v > 8.0:
                lead_v = max(8.0, lead_v - 0.8 * dt)

            lead_x += lead_v * dt

            # 间距与 TTC 计算
            gap = lead_x - ego_x - 4.5
            rel_v = ego_v - lead_v
            in_lane = lead_y < 1.75
            ttc = (gap / rel_v) if (rel_v > 0.05 and in_lane) else 99.0

            # 综合控制器逻辑
            if ttc < ttc_thresh and in_lane:
                acc_cmd = -4.2
            else:
                d_des = 5.0 + th * ego_v
                acc_cmd = 0.85 * (gap - d_des) + 1.25 * (lead_v - ego_v)
                acc_cmd = max(-3.0, min(1.5, acc_cmd))

            ego_v = max(0.0, ego_v + acc_cmd * dt)
            ego_x += ego_v * dt

            # 电动动力总成能耗与回充物理
            f_aero = 0.5 * 1.225 * cd_a * (ego_v ** 2)
            f_roll = mass * 9.81 * f_r
            f_acc = mass * acc_cmd
            f_total = f_acc + f_aero + f_roll
            p_wheel = f_total * ego_v

            if p_wheel < 0:
                # 制动能量回收
                p_regen = p_wheel * regen * 0.82
                p_bat = p_regen  # 负值充电
                total_regen_joules += (-p_regen) * dt
            else:
                p_bat = p_wheel / 0.88  # 驱动放电
                total_traction_joules += p_bat * dt

            delta_soc = - (p_bat * dt) / (bat_cap_kwh * 3.6e6)
            soc += delta_soc

            ego_v_log.append(ego_v * 3.6)
            lead_v_log.append(lead_v * 3.6)
            gap_log.append(gap)
            accel_log.append(acc_cmd)
            soc_log.append(soc * 100.0)
            p_bat_log.append(p_bat / 1000.0)
            ttc_log.append(min(15.0, ttc))

        min_gap = min(gap_log)
        min_ttc = min(ttc_log)
        max_decel = abs(min(accel_log))
        regen_kwh = total_regen_joules / 3.6e6
        net_energy_kwh_100km = ((total_traction_joules - total_regen_joules) / 3.6e6) / (max(0.01, ego_x / 1000.0)) * 100.0

        with out:
            clear_output(wait=True)
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4.2))

            # 速度与车距
            line1 = ax1.plot(t_arr, ego_v_log, color="#2563eb", linewidth=2.2, label="自车车速 (km/h)")
            line2 = ax1.plot(t_arr, lead_v_log, color="#dc2626", linestyle="--", linewidth=2.0, label="目标加塞车 (km/h)")
            ax1.axvspan(4.5, 7.0, color="#fef08a", alpha=0.35, label="Cut-in 加塞变道区间")
            ax1.set_xlabel("仿真时间 (s)")
            ax1.set_ylabel("车速 (km/h)", color="#1e293b")
            ax1.set_title("感-算-控闭环车速与跟驰避险轨迹", fontweight="bold")
            ax1.grid(True, alpha=0.3, linestyle="--")

            ax1_twin = ax1.twinx()
            line3 = ax1_twin.plot(t_arr, gap_log, color="#16a34a", linestyle=":", linewidth=2.0, label="相对间距 (m)")
            ax1_twin.set_ylabel("车距 (m)", color="#16a34a")

            lines = line1 + line2 + line3
            labels = [l.get_label() for l in lines]
            ax1.legend(lines, labels, loc="upper right", fontsize=9)

            # 加速度与瞬时功率
            ax2.plot(t_arr, accel_log, color="#9333ea", linewidth=2.0, label="加速度 a (m/s²)")
            ax2.axhline(0, color="#94a3b8", linestyle="--", linewidth=0.8)
            ax2.set_xlabel("仿真时间 (s)")
            ax2.set_ylabel("加速度 (m/s²)", color="#9333ea")
            ax2.set_title("动力学加速度与电池能量回充响应", fontweight="bold")
            ax2.grid(True, alpha=0.3, linestyle="--")

            ax2_twin = ax2.twinx()
            ax2_twin.plot(t_arr, p_bat_log, color="#0891b2", linestyle="-.", linewidth=1.8, label="电池功率 (kW)")
            ax2_twin.set_ylabel("电池功率 (kW, 负为充电)", color="#0891b2")

            lines2 = ax2.get_lines() + ax2_twin.get_lines()
            labels2 = [l.get_label() for l in lines2]
            ax2.legend(lines2, labels2, loc="upper right", fontsize=9)

            plt.tight_layout()
            plt.show()

            if min_gap < 1.0:
                badge_text = "🚨 发生致命追尾碰撞"
                badge_color = "red"
                insight = f"<b>安全失效</b>：TTC 避险阈值过低 ({ttc_thresh:.1f}s)，自车制动介入过晚导致碰撞 (最小间距 {min_gap:.1f}m)！"
            elif min_gap < 4.0:
                badge_text = "⚠️ 避险间距过小 (惊险工况)"
                badge_color = "yellow"
                insight = f"<b>临界危险</b>：最小车距仅 {min_gap:.1f}m，乘员产生明显恐慌感。建议适当提高 TTC 阈值至 2.2s 以上。"
            else:
                badge_text = "✅ 避险成功 & 能量高效回收"
                badge_color = "green"
                insight = f"<b>安全与能耗平衡</b>：自车平稳化解加塞险情，最小间距稳定在 {min_gap:.1f}m；同时制动回收回收电量 {regen_kwh*1000:.1f} Wh，百公里综合能耗 {net_energy_kwh_100km:.2f} kWh/100km。"

            card_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; border-radius: 8px; padding: 12px 16px; margin: 10px 0; font-family: system-ui, sans-serif;">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px;">
                    <span style="font-weight: bold; color: #0f172a;">🏆 Capstone 全域一体化集成综合研判</span>
                    <span style="background: {("#dcfce7" if badge_color=="green" else ("#fee2e2" if badge_color=="red" else "#fef3c7"))}; color: {("#15803d" if badge_color=="green" else ("#dc2626" if badge_color=="red" else "#b45309"))}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                        {badge_text}
                    </span>
                </div>
                <div style="font-size: 13px; color: #334155; line-height: 1.6;">
                    • <b>安全避险</b>: 最小间距 <b>{min_gap:.2f} m</b>，最小观测 TTC <b>{min_ttc:.2f} s</b>，最大避险减速度 <b>{max_decel:.2f} m/s²</b>；<br/>
                    • <b>电气与能效</b>: 制动回充能量 <b>{regen_kwh*1000:.1f} Wh</b>，综合等效电耗 <b>{net_energy_kwh_100km:.2f} kWh/100km</b>；<br/>
                    • <b>多目标协同因果</b>: {insight}
                </div>
            </div>
            """
            display(HTML(card_html))

    def on_checkin(_):
        ans = txt_task.value.strip()
        with out_checkin:
            clear_output()
            if not ans:
                print("⚠️ 请先在文本框输入微任务心得再打卡！")
                return
            ok = _save_preview_checkin("Capstone_iev_integrated", {
                experiment: "Capstone_iev_integrated",
                mode: "novice_preview",
                ttc_thresh: slider_ttc.value,
                headway_s: slider_headway.value,
                regen_ratio: slider_regen.value,
                student_insight: ans,
            })
            if ok:
                display(HTML("<span style='color: #16a34a; font-weight: bold;'>🎉 Capstone 课前直觉预习打卡成功！已存入系统记录。</span>"))
            else:
                display(HTML("<span style='color: #dc2626;'>打卡写入失败，请重试。</span>"))

    btn_run.on_click(update_view)
    btn_checkin.on_click(on_checkin)

    intro_html = """
    <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 10px 14px; margin-bottom: 12px; font-family: system-ui, sans-serif;">
        <h4 style="margin: 0; color: #166534; font-size: 15px;">🌟 模式 A：新手直觉探索驾驶舱 (直观调参 · 无需写代码)</h4>
        <p style="margin: 4px 0 0 0; color: #15803d; font-size: 12px;">
            <b>目标导向微任务</b>：调节 TTC 避险阈值、跟驰时距与能量回收比例，观察在加塞工况下安全、舒适与电能回充的多目标协同规律。
        </p>
    </div>
    """
    display(HTML(intro_html))
    controls = widgets.VBox([
        widgets.HBox([slider_ttc, slider_headway, slider_regen, btn_run]),
        widgets.HBox([txt_task, btn_checkin]),
        out_checkin,
        out
    ])
    display(controls)
    update_view()
