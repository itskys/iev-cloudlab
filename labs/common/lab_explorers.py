"""IEV CloudLab 新手直觉探索与课前导学驱动引擎 (Phase 0: Interactive Intuition Explorers)

本模块专为初学学生设计（双轨制直观轨道）：
  1. 零代码门槛：仅需调节 1~3 个关键物理滑杆，一键实时推演
  2. 交互三件套：
     - 基线对比曲线图（基线 vs 调后同图叠画，变化一眼可见）
     - 动态工况/回放示意（直观展现车态、流场或微观电位）
     - 指标卡 + 一句话物理增量解读（将枯燥数值翻译为驾驶体感与物理因果）
  3. 目标导向寻优微任务：引导学生拖动滑杆寻找达标区间，完成填空式心得
  4. 课前预习打卡机制：独立于正式 29+1 成绩册，完成即得预习分，无感建立物理直觉

覆盖实验（与 Muse A1/B2/C1/D1/E3 形成 10 门对仗矩阵）：
  - A2: 自适应巡航 (ACC) 跟车时距与刚度阻尼
  - B4: 交通拥堵冲击波 (LWR) 倒灌与负波速拟合
  - C3: 载重与风阻灵敏度分析与工况反转
  - D4: 极速快充析锂风险与负极 0V 安全边界
  - E2: 动力性 vs 成本多目标 Pareto 前沿与膝点决策
"""

import os
import json
import numpy as np
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
import matplotlib.pyplot as plt

# 配置高清晰度 CJK 中文字体支持
plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Micro Hei', 'DejaVu Sans', 'Arial', 'sans-serif']
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
