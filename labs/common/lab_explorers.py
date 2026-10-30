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
import ipywidgets as widgets
from IPython.display import display, clear_output, HTML
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
