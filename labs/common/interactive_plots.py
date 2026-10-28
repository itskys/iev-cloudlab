"""IEV CloudLab 交互式参数调优与多维工程分析图表库 | Interactive Exploration Dashboards

提供基于前端原生 Canvas / SVG 的即时调参交互小部件（零第三方 Python 依赖，秒级响应）：
  1. render_interactive_idm_tuner(): IDM 智能跟车模型多参数即时滑块标定器 (B1 Pro)
  2. render_interactive_mpc_explorer(): MPC 跟踪精度 vs 舒适性动态权衡滑块仪表盘 (E3 Pro)
  3. render_interactive_vehicle_radar(): 多构型智能电动汽车六维综合性能雷达图 (C2 Pro)

设计原则：
  - 纯前端 JavaScript 毫秒级解算，拖动滑块时无需刷新 Python 内核
  - 自适应适配深色/浅色工程 UI 风格
  - 导出标准 IPython.display.HTML 对象，直接在 Notebook Cell 中交互
"""

import json
import numpy as np


def render_interactive_idm_tuner(
    ground_truth_t,
    ground_truth_dist,
    lead_v,
    init_v=15.0,
    init_dist=20.0,
    title="IEV 智能跟车模型 (IDM) 实时交互标定器",
    height=480,
):
    """B1 Pro 交互式 IDM 参数标定看板。

    通过滑块即时调节 s0, T, a, b，前端毫秒级实时积分推演跟车距离并与实测值叠加对比，动态刷新 RMSE。
    """
    t_arr = [round(float(v), 2) for v in np.asarray(ground_truth_t).flatten()]
    gt_dist_arr = [round(float(v), 2) for v in np.asarray(ground_truth_dist).flatten()]
    lead_v_arr = [round(float(v), 2) for v in np.asarray(lead_v).flatten()]

    payload = {
        "t": t_arr,
        "gt_dist": gt_dist_arr,
        "lead_v": lead_v_arr,
        "init_v": float(init_v),
        "init_dist": float(init_dist),
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    import uuid
    uid = f"idm_{uuid.uuid4().hex[:8]}"

    html = f"""
<div id="{uid}" style="
    width: 100%; height: {height}px; background: #0D1117;
    border: 1px solid #30363D; border-radius: 10px; overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #C9D1D9; display: flex; flex-direction: column; box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    margin: 16px 0;
">
    <!-- 顶栏 -->
    <div style="
        height: 42px; background: #161B22; border-bottom: 1px solid #30363D;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 16px;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #58A6FF;"></span>
            <span style="font-weight: 600; font-size: 13px; color: #F0F6FC;">{title}</span>
            <span style="font-size: 11px; color: #8B949E;">(无需重启内核，拖拽即时推演)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 12px; color: #8B949E;">标定拟合误差:</span>
            <span id="{uid}_rmse_badge" style="
                background: #23863622; color: #3FB950; border: 1px solid #23863688;
                padding: 2px 10px; border-radius: 12px; font-weight: 700; font-family: monospace; font-size: 13px;
            ">RMSE: -- m</span>
        </div>
    </div>

    <!-- 主体：左侧图表 + 右侧调参控制板 -->
    <div style="flex: 1; display: flex; min-height: 0;">
        <!-- 曲线画布 -->
        <div style="flex: 1; position: relative; padding: 10px;">
            <canvas id="{uid}_canvas" style="width: 100%; height: 100%; display: block;"></canvas>
            <div style="position: absolute; top: 20px; right: 25px; display: flex; gap: 14px; font-size: 11px;">
                <span style="display: flex; align-items: center; gap: 5px;">
                    <span style="width: 14px; height: 3px; background: #8B949E; display: inline-block;"></span> 真实采集基准
                </span>
                <span style="display: flex; align-items: center; gap: 5px;">
                    <span style="width: 14px; height: 3px; background: #58A6FF; display: inline-block;"></span> IDM 模拟推演
                </span>
            </div>
        </div>

        <!-- 参数控制面板 -->
        <div style="
            width: 280px; background: #161B22; border-left: 1px solid #30363D;
            padding: 14px 16px; display: flex; flex-direction: column; gap: 12px;
            overflow-y: auto; font-size: 12px;
        ">
            <div style="font-weight: 600; color: #F0F6FC; border-bottom: 1px solid #21262D; padding-bottom: 6px;">
                IDM 物理参数标定项
            </div>

            <!-- s0 -->
            <div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8B949E;">静止安全间距 s₀</span>
                    <span id="{uid}_val_s0" style="font-family: monospace; color: #58A6FF; font-weight: 600;">2.0 m</span>
                </div>
                <input id="{uid}_sl_s0" type="range" min="1.0" max="6.0" step="0.1" value="2.0" style="width: 100%; accent-color: #58A6FF;">
            </div>

            <!-- T -->
            <div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8B949E;">期望车头时距 T</span>
                    <span id="{uid}_val_T" style="font-family: monospace; color: #58A6FF; font-weight: 600;">1.5 s</span>
                </div>
                <input id="{uid}_sl_T" type="range" min="0.5" max="3.0" step="0.05" value="1.5" style="width: 100%; accent-color: #58A6FF;">
            </div>

            <!-- a -->
            <div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8B949E;">最大加速度 a</span>
                    <span id="{uid}_val_a" style="font-family: monospace; color: #58A6FF; font-weight: 600;">1.5 m/s²</span>
                </div>
                <input id="{uid}_sl_a" type="range" min="0.5" max="3.5" step="0.1" value="1.5" style="width: 100%; accent-color: #58A6FF;">
            </div>

            <!-- b -->
            <div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #8B949E;">舒适制动减速度 b</span>
                    <span id="{uid}_val_b" style="font-family: monospace; color: #58A6FF; font-weight: 600;">2.0 m/s²</span>
                </div>
                <input id="{uid}_sl_b" type="range" min="0.8" max="4.0" step="0.1" value="2.0" style="width: 100%; accent-color: #58A6FF;">
            </div>

            <!-- 标定预置快捷键 -->
            <div style="margin-top: 8px; border-top: 1px solid #21262D; padding-top: 10px;">
                <div style="color: #8B949E; margin-bottom: 6px; font-size: 11px;">工程推荐配置预置：</div>
                <div style="display: flex; gap: 6px;">
                    <button id="{uid}_btn_preset_sport" style="flex: 1; padding: 4px; background: #21262D; border: 1px solid #30363D; color: #C9D1D9; border-radius: 4px; cursor: pointer; font-size: 11px;">激进型</button>
                    <button id="{uid}_btn_preset_optimal" style="flex: 1; padding: 4px; background: #238636; border: 1px solid #2EA043; color: #fff; border-radius: 4px; cursor: pointer; font-size: 11px;">最优标定</button>
                    <button id="{uid}_btn_preset_comfort" style="flex: 1; padding: 4px; background: #21262D; border: 1px solid #30363D; color: #C9D1D9; border-radius: 4px; cursor: pointer; font-size: 11px;">保守型</button>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
(function() {{
    const data = {payload_json};
    const uid = "{uid}";
    const canvas = document.getElementById(uid + "_canvas");
    const ctx = canvas.getContext("2d");

    const sl_s0 = document.getElementById(uid + "_sl_s0");
    const sl_T = document.getElementById(uid + "_sl_T");
    const sl_a = document.getElementById(uid + "_sl_a");
    const sl_b = document.getElementById(uid + "_sl_b");

    const val_s0 = document.getElementById(uid + "_val_s0");
    const val_T = document.getElementById(uid + "_val_T");
    const val_a = document.getElementById(uid + "_val_a");
    const val_b = document.getElementById(uid + "_val_b");
    const badge_rmse = document.getElementById(uid + "_rmse_badge");

    const btn_sport = document.getElementById(uid + "_btn_preset_sport");
    const btn_opt = document.getElementById(uid + "_btn_preset_optimal");
    const btn_comfort = document.getElementById(uid + "_btn_preset_comfort");

    let simDist = [];

    function runIDMSimulation(s0, T, a, b) {{
        const N = data.t.length;
        simDist = new Array(N);
        let curV = data.init_v;
        let curDist = data.init_dist;
        const v0 = 25.0; // 期望自由流速度 25 m/s

        simDist[0] = curDist;
        for (let i = 0; i < N - 1; i++) {{
            const dt = data.t[i+1] - data.t[i];
            const leadV = data.lead_v[i];
            const deltaV = curV - leadV;

            // IDM 经典方程: s* = s0 + max(0, v*T + v*deltaV/(2*sqrt(a*b)))
            const sStar = s0 + Math.max(0, curV * T + (curV * deltaV) / (2.0 * Math.sqrt(a * b)));
            // a_idm = a * [1 - (v/v0)^4 - (s*/s)^2]
            const termV = Math.pow(curV / v0, 4);
            const termS = Math.pow(sStar / Math.max(0.5, curDist), 2);
            let acc = a * (1.0 - termV - termS);

            // 限制减速度不超过 -8 m/s^2，加速度不超过 a
            acc = Math.max(-8.0, Math.min(a, acc));

            curV = Math.max(0.0, curV + acc * dt);
            curDist = Math.max(0.1, curDist + (leadV - curV) * dt);
            simDist[i+1] = curDist;
        }}

        // 计算 RMSE
        let sumSq = 0;
        for (let i = 0; i < N; i++) {{
            const diff = simDist[i] - data.gt_dist[i];
            sumSq += diff * diff;
        }}
        const rmse = Math.sqrt(sumSq / N);
        return rmse;
    }}

    function update() {{
        const s0 = parseFloat(sl_s0.value);
        const T = parseFloat(sl_T.value);
        const a = parseFloat(sl_a.value);
        const b = parseFloat(sl_b.value);

        val_s0.innerText = s0.toFixed(1) + " m";
        val_T.innerText = T.toFixed(2) + " s";
        val_a.innerText = a.toFixed(1) + " m/s²";
        val_b.innerText = b.toFixed(1) + " m/s²";

        const rmse = runIDMSimulation(s0, T, a, b);
        badge_rmse.innerText = "RMSE: " + rmse.toFixed(2) + " m";

        if (rmse <= 2.5) {{
            badge_rmse.style.color = "#3FB950";
            badge_rmse.style.background = "#23863622";
            badge_rmse.style.borderColor = "#23863688";
        }} else if (rmse <= 4.0) {{
            badge_rmse.style.color = "#D29922";
            badge_rmse.style.background = "#D2992222";
            badge_rmse.style.borderColor = "#D2992288";
        }} else {{
            badge_rmse.style.color = "#F85149";
            badge_rmse.style.background = "#DA363322";
            badge_rmse.style.borderColor = "#DA363388";
        }}

        draw();
    }}

    function draw() {{
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.resetTransform();
        ctx.scale(dpr, dpr);

        const W = rect.width;
        const H = rect.height;
        ctx.clearRect(0, 0, W, H);

        const padLeft = 45;
        const padRight = 20;
        const padTop = 30;
        const padBottom = 35;
        const plotW = W - padLeft - padRight;
        const plotH = H - padTop - padBottom;

        // 计算网格坐标
        const maxT = data.t[data.t.length - 1];
        let maxD = 40.0;
        for (let i = 0; i < data.t.length; i++) {{
            if (data.gt_dist[i] > maxD) maxD = data.gt_dist[i];
            if (simDist[i] && simDist[i] > maxD) maxD = simDist[i];
        }}
        maxD = Math.ceil(maxD / 10) * 10;

        // 背景网格线
        ctx.strokeStyle = "#21262D";
        ctx.lineWidth = 1;
        ctx.fillStyle = "#8B949E";
        ctx.font = "10px monospace";
        ctx.textAlign = "right";

        for (let d = 0; d <= maxD; d += 10) {{
            const y = padTop + plotH - (d / maxD) * plotH;
            ctx.beginPath();
            ctx.moveTo(padLeft, y);
            ctx.lineTo(padLeft + plotW, y);
            ctx.stroke();
            ctx.fillText(d + "m", padLeft - 6, y + 3);
        }}

        ctx.textAlign = "center";
        for (let t = 0; t <= maxT; t += 5) {{
            const x = padLeft + (t / maxT) * plotW;
            ctx.beginPath();
            ctx.moveTo(x, padTop);
            ctx.lineTo(x, padTop + plotH);
            ctx.stroke();
            ctx.fillText(t + "s", x, padTop + plotH + 16);
        }}

        // 绘制基准真实值曲线 (灰白实线)
        ctx.strokeStyle = "#8B949E";
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < data.t.length; i++) {{
            const x = padLeft + (data.t[i] / maxT) * plotW;
            const y = padTop + plotH - (data.gt_dist[i] / maxD) * plotH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }}
        ctx.stroke();

        // 绘制 IDM 拟合推演曲线 (高亮青蓝线)
        ctx.strokeStyle = "#58A6FF";
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        for (let i = 0; i < data.t.length; i++) {{
            const x = padLeft + (data.t[i] / maxT) * plotW;
            const y = padTop + plotH - (simDist[i] / maxD) * plotH;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }}
        ctx.stroke();
    }}

    [sl_s0, sl_T, sl_a, sl_b].forEach(sl => sl.addEventListener('input', update));

    btn_sport.addEventListener('click', () => {{
        sl_s0.value = 1.2; sl_T.value = 0.9; sl_a.value = 2.5; sl_b.value = 3.0; update();
    }});
    btn_opt.addEventListener('click', () => {{
        sl_s0.value = 2.0; sl_T.value = 1.4; sl_a.value = 1.5; sl_b.value = 2.0; update();
    }});
    btn_comfort.addEventListener('click', () => {{
        sl_s0.value = 3.5; sl_T.value = 2.2; sl_a.value = 1.0; sl_b.value = 1.5; update();
    }});

    window.addEventListener('resize', draw);
    setTimeout(update, 50);
}})();
</script>
"""
    try:
        from IPython.display import HTML
        return HTML(html)
    except ImportError:
        return html


def render_interactive_vehicle_radar(
    vehicles_data=None,
    title="IEV 多构型车辆全维度工程对比雷达图",
    height=460,
):
    """C2 Pro 多动力总成架构（BEV / PHEV / HEV / 传统燃油）多维性能交互对比雷达图。"""
    if vehicles_data is None:
        vehicles_data = {
            "纯电动 (BEV)": {
                "color": "#58A6FF",
                "metrics": {"动力性能": 92, "综合能效": 95, "续航里程": 75, "整车轻量化": 68, "环保碳排": 98, "补能便利度": 65}
            },
            "插电混动 (PHEV)": {
                "color": "#3FB950",
                "metrics": {"动力性能": 85, "综合能效": 82, "续航里程": 96, "整车轻量化": 60, "环保碳排": 80, "补能便利度": 95}
            },
            "油电混动 (HEV)": {
                "color": "#D29922",
                "metrics": {"动力性能": 72, "综合能效": 78, "续航里程": 92, "整车轻量化": 82, "环保碳排": 70, "补能便利度": 98}
            },
            "燃油车 (ICE)": {
                "color": "#F85149",
                "metrics": {"动力性能": 70, "综合能效": 45, "续航里程": 85, "整车轻量化": 90, "环保碳排": 35, "补能便利度": 100}
            }
        }

    payload_json = json.dumps(vehicles_data, ensure_ascii=False)
    import uuid
    uid = f"radar_{uuid.uuid4().hex[:8]}"

    html = f"""
<div id="{uid}" style="
    width: 100%; height: {height}px; background: #0D1117;
    border: 1px solid #30363D; border-radius: 10px; overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #C9D1D9; display: flex; flex-direction: column; box-shadow: 0 8px 24px rgba(0,0,0,0.35);
    margin: 16px 0;
">
    <div style="
        height: 42px; background: #161B22; border-bottom: 1px solid #30363D;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 16px;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="width: 8px; height: 8px; border-radius: 50%; background: #3FB950;"></span>
            <span style="font-weight: 600; font-size: 13px; color: #F0F6FC;">{title}</span>
            <span style="font-size: 11px; color: #8B949E;">(点击右侧标签显示/隐藏对应车型)</span>
        </div>
    </div>

    <div style="flex: 1; display: flex; min-height: 0;">
        <canvas id="{uid}_canvas" style="flex: 1; display: block;"></canvas>
        <div id="{uid}_legend" style="
            width: 220px; background: #161B22; border-left: 1px solid #30363D;
            padding: 16px; display: flex; flex-direction: column; gap: 10px; font-size: 12px;
        ">
            <div style="font-weight: 600; color: #F0F6FC; border-bottom: 1px solid #21262D; padding-bottom: 6px;">
                对比车型筛选
            </div>
        </div>
    </div>
</div>

<script>
(function() {{
    const data = {payload_json};
    const uid = "{uid}";
    const canvas = document.getElementById(uid + "_canvas");
    const ctx = canvas.getContext("2d");
    const legendContainer = document.getElementById(uid + "_legend");

    const activeVehicles = {{}};
    Object.keys(data).forEach(k => activeVehicles[k] = true);

    const categories = Object.keys(Object.values(data)[0].metrics);
    const numAxes = categories.length;

    // 创建筛选选项
    Object.keys(data).forEach(veh => {{
        const vInfo = data[veh];
        const row = document.createElement("div");
        row.style.cssText = "display: flex; align-items: center; gap: 8px; cursor: pointer; user-select: none;";
        row.innerHTML = `
            <input type="checkbox" checked id="${{uid}}_${{veh}}" style="accent-color: ${{vInfo.color}};">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 2px; background: ${{vInfo.color}};"></span>
            <span style="color: #F0F6FC; font-weight: 500;">${{veh}}</span>
        `;
        row.addEventListener("click", (e) => {{
            if (e.target.tagName !== "INPUT") {{
                const chk = row.querySelector("input");
                chk.checked = !chk.checked;
            }}
            activeVehicles[veh] = row.querySelector("input").checked;
            draw();
        }});
        legendContainer.appendChild(row);
    }});

    function draw() {{
        const rect = canvas.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.resetTransform();
        ctx.scale(dpr, dpr);

        const W = rect.width;
        const H = rect.height;
        ctx.clearRect(0, 0, W, H);

        const cx = W * 0.5;
        const cy = H * 0.5;
        const radius = Math.min(W, H) * 0.38;

        // 绘制雷达同心多边形网格
        const levels = 5;
        for (let l = 1; l <= levels; l++) {{
            const r = (radius / levels) * l;
            ctx.strokeStyle = "#21262D";
            ctx.lineWidth = 1;
            ctx.beginPath();
            for (let i = 0; i < numAxes; i++) {{
                const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
                const x = cx + r * Math.cos(angle);
                const y = cy + r * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }}
            ctx.closePath();
            ctx.stroke();
        }}

        // 绘制射线与标签
        ctx.font = "11px sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        for (let i = 0; i < numAxes; i++) {{
            const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
            const x = cx + radius * Math.cos(angle);
            const y = cy + radius * Math.sin(angle);

            ctx.strokeStyle = "#30363D";
            ctx.beginPath();
            ctx.moveTo(cx, cy);
            ctx.lineTo(x, y);
            ctx.stroke();

            // 外部文字标签
            const labelX = cx + (radius + 20) * Math.cos(angle);
            const labelY = cy + (radius + 16) * Math.sin(angle);
            ctx.fillStyle = "#8B949E";
            ctx.fillText(categories[i], labelX, labelY);
        }}

        // 绘制各车型多边形
        Object.keys(data).forEach(veh => {{
            if (!activeVehicles[veh]) return;
            const vInfo = data[veh];
            ctx.strokeStyle = vInfo.color;
            ctx.fillStyle = vInfo.color + "33"; // 20% 透明度填充
            ctx.lineWidth = 2;

            ctx.beginPath();
            for (let i = 0; i < numAxes; i++) {{
                const score = vInfo.metrics[categories[i]];
                const r = (radius / 100.0) * score;
                const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
                const x = cx + r * Math.cos(angle);
                const y = cy + r * Math.sin(angle);
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }}
            ctx.closePath();
            ctx.fill();
            ctx.stroke();

            // 绘制顶点圆点
            ctx.fillStyle = vInfo.color;
            for (let i = 0; i < numAxes; i++) {{
                const score = vInfo.metrics[categories[i]];
                const r = (radius / 100.0) * score;
                const angle = (Math.PI * 2 / numAxes) * i - Math.PI / 2;
                const x = cx + r * Math.cos(angle);
                const y = cy + r * Math.sin(angle);
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, Math.PI * 2);
                ctx.fill();
            }}
        }});
    }}

    window.addEventListener("resize", draw);
    setTimeout(draw, 50);
}})();
</script>
"""
    try:
        from IPython.display import HTML
        return HTML(html)
    except ImportError:
        return html
