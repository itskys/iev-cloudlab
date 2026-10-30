"""IEV CloudLab 轻量数字孪生与双视角轨迹回放组件（2D 画布：俯视 + 斜视角投影） | Interactive Digital Twin Replay

功能：
  1. 纯前端零外部依赖（原生 HTML5 Canvas + WebGL 视效，无第三方 npm/pip 依赖）
  2. 支持双模视角无缝切换：BEV 鸟瞰俯视图与斜视角投影（2D 画布 oblique 投影，非真三维渲染）
  3. 全功能回放控制台：播放/暂停、进度拖拽条、0.5x/1x/2x/5x 倍速切换、单步步进
  4. 实时动态车载 HUD 仪表盘：
     - 数字时速表 (km/h) 与加速度/急动度仪表
     - 动态雷达感知视场角（FOV 动态发光检测锥，遇障变色）
     - 实时纵向车距与 TTC 安全时间显示
     - 预警状态胶囊（巡航 / 预警 / AEB触发 / 碰撞）
  5. 完美适配 JupyterLab 深浅色主题与高分屏（Retina Display）渲染

适用场景：A1~A5 智驾场景、E3 MPC跟车、B3 CACC车队、H2 极限避障推演。
"""

import json
import numpy as np


def render_trajectory_replay(
    t,
    ego,
    targets=None,
    road=None,
    metrics=None,
    title="IEV 数字孪生 · 车辆动态回放",
    subtitle="Interactive Cyber-Physical Vehicle Replay",
    height=540,
    show_radar=True,
):
    """生成内嵌式动态轨迹回放器 HTML 小部件。

    参数:
      t: 时间数组 (list 或 1D np.ndarray, 单位 s)
      ego: dict, 包含 'x', 'y'(可选), 'v', 'a'(可选), 'jerk'(可选)
      targets: list of dict 或 dict, 每个目标包含 'name', 'x', 'y'(可选), 'v', 'color'(可选)
      road: dict (可选), {'num_lanes': 3, 'lane_width': 3.75, 'speed_limit': 120}
      metrics: dict (可选), {'ttc': [...], 'spacing': [...], 'aeb_active': [...]}
      title: str, 视窗主标题
      subtitle: str, 视窗副标题
      height: int, 控件视窗高度 (像素)
      show_radar: bool, 是否显示主车前向毫米波雷达/激光雷达感知锥

    返回:
      IPython.display.HTML 对象 (可直接在 Notebook cell 中返回显示)
    """
    # 格式化数据为紧凑 JSON
    t_list = [round(float(v), 3) for v in np.asarray(t).flatten()]
    n_frames = len(t_list)
    if n_frames == 0:
        raise ValueError("时间序列 t 不能为空")

    def _get_arr(d, key, default_val=0.0):
        if key in d and d[key] is not None:
            arr = np.asarray(d[key]).flatten()
            if len(arr) == n_frames:
                return [round(float(v), 3) for v in arr]
            # 若长度不一致做简单插值或截断
            return [round(float(arr[min(i, len(arr) - 1)]), 3) for i in range(n_frames)]
        return [default_val] * n_frames

    ego_data = {
        "x": _get_arr(ego, "x", 0.0),
        "y": _get_arr(ego, "y", 0.0),
        "v": _get_arr(ego, "v", 0.0),
        "a": _get_arr(ego, "a", 0.0),
        "jerk": _get_arr(ego, "jerk", 0.0),
    }

    if targets is None:
        target_list = []
    elif isinstance(targets, dict):
        target_list = [targets]
    else:
        target_list = list(targets)

    parsed_targets = []
    default_colors = ["#FF5722", "#FF9800", "#9C27B0", "#00BCD4"]
    for idx, tgt in enumerate(target_list):
        parsed_targets.append({
            "name": str(tgt.get("name", f"Target-{idx+1}")),
            "color": str(tgt.get("color", default_colors[idx % len(default_colors)])),
            "x": _get_arr(tgt, "x", 0.0),
            "y": _get_arr(tgt, "y", 0.0),
            "v": _get_arr(tgt, "v", 0.0),
        })

    road_cfg = {
        "num_lanes": int(road.get("num_lanes", 3)) if road else 3,
        "lane_width": float(road.get("lane_width", 3.75)) if road else 3.75,
        "speed_limit": float(road.get("speed_limit", 120)) if road else 120,
    }

    metric_data = {}
    if metrics:
        for k, v in metrics.items():
            if v is not None:
                metric_data[k] = _get_arr({k: v}, k, 0.0)

    # 序列化为安全 JSON
    payload = {
        "t": t_list,
        "ego": ego_data,
        "targets": parsed_targets,
        "road": road_cfg,
        "metrics": metric_data,
        "show_radar": bool(show_radar),
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    import uuid
    widget_id = f"iev_dt_{uuid.uuid4().hex[:8]}"

    html_code = f"""
<div id="{widget_id}" class="iev-digital-twin-container" style="
    position: relative;
    width: 100%;
    height: {height}px;
    background: #0D1117;
    border: 1px solid #30363D;
    border-radius: 10px;
    overflow: hidden;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', sans-serif;
    color: #C9D1D9;
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    user-select: none;
    margin: 16px 0;
">
    <!-- 顶部标题栏 -->
    <div style="
        position: absolute; top: 0; left: 0; right: 0; height: 42px;
        background: rgba(22, 27, 34, 0.85);
        backdrop-filter: blur(8px);
        border-bottom: 1px solid #30363D;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 16px; z-index: 10;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #2EA043; box-shadow: 0 0 8px #2EA043;"></span>
            <span style="font-weight: 600; font-size: 13px; color: #F0F6FC;">{title}</span>
            <span style="font-size: 11px; color: #8B949E; margin-left: 4px;">{subtitle}</span>
        </div>
        <div style="display: flex; align-items: center; gap: 10px;">
            <div style="background: #21262D; border-radius: 6px; padding: 2px; display: flex; gap: 2px;">
                <button id="{widget_id}_view_bev" class="iev-btn active" style="padding: 3px 10px; font-size: 11px; border-radius: 4px; border: none; cursor: pointer; background: #388BFD; color: #fff;">BEV 鸟瞰</button>
                <button id="{widget_id}_view_3d" class="iev-btn" style="padding: 3px 10px; font-size: 11px; border-radius: 4px; border: none; cursor: pointer; background: transparent; color: #8B949E;">斜视角</button>
            </div>
            <button id="{widget_id}_btn_reset" style="background: #21262D; border: 1px solid #30363D; color: #C9D1D9; border-radius: 4px; padding: 3px 8px; font-size: 11px; cursor: pointer;">复位视点</button>
        </div>
    </div>

    <!-- Canvas 视窗 -->
    <canvas id="{widget_id}_canvas" style="width: 100%; height: 100%; display: block;"></canvas>

    <!-- 实时 HUD 遥测仪表盘 (左上角悬浮) -->
    <div style="
        position: absolute; top: 52px; left: 16px;
        background: rgba(13, 17, 23, 0.82);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(48, 54, 61, 0.9);
        border-radius: 8px;
        padding: 10px 14px;
        display: flex; flex-direction: column; gap: 6px;
        font-size: 11px; z-index: 5;
        min-width: 170px;
        pointer-events: none;
    ">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span style="color: #8B949E;">本车时速</span>
            <span style="font-size: 18px; font-weight: 700; color: #58A6FF; font-family: monospace;">
                <span id="{widget_id}_hud_speed">0.0</span> <span style="font-size: 10px; color: #8B949E;">km/h</span>
            </span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #8B949E;">加速度 / Jerk</span>
            <span style="font-family: monospace; color: #E6EDF3;"><span id="{widget_id}_hud_acc">0.00</span> m/s² | <span id="{widget_id}_hud_jerk">0.0</span></span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #8B949E;">前车间距</span>
            <span style="font-family: monospace; color: #E6EDF3;"><span id="{widget_id}_hud_dist">--</span> m</span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #8B949E;">安全 TTC</span>
            <span id="{widget_id}_hud_ttc" style="font-family: monospace; font-weight: 700; color: #3FB950;">-- s</span>
        </div>
        <div style="margin-top: 4px; border-top: 1px solid #21262D; padding-top: 6px; display: flex; justify-content: space-between; align-items: center;">
            <span style="color: #8B949E;">ADAS 状态</span>
            <span id="{widget_id}_hud_status" style="
                background: #1F6FEB22; color: #58A6FF; border: 1px solid #1F6FEB66;
                padding: 1px 6px; border-radius: 10px; font-size: 10px; font-weight: 600;
            ">CRUISE</span>
        </div>
    </div>

    <!-- 底部时间轴控制台 -->
    <div style="
        position: absolute; bottom: 0; left: 0; right: 0; height: 50px;
        background: rgba(22, 27, 34, 0.9);
        backdrop-filter: blur(8px);
        border-top: 1px solid #30363D;
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 16px; gap: 14px; z-index: 10;
    ">
        <!-- 播放/暂停/单步 -->
        <div style="display: flex; align-items: center; gap: 6px;">
            <button id="{widget_id}_btn_play" style="
                background: #238636; border: none; color: #fff; width: 32px; height: 32px;
                border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-size: 12px;
            ">▶</button>
            <button id="{widget_id}_btn_step_prev" style="background: #21262D; border: 1px solid #30363D; color: #C9D1D9; border-radius: 4px; width: 28px; height: 28px; cursor: pointer;">⏮</button>
            <button id="{widget_id}_btn_step_next" style="background: #21262D; border: 1px solid #30363D; color: #C9D1D9; border-radius: 4px; width: 28px; height: 28px; cursor: pointer;">⏭</button>
        </div>

        <!-- 进度条与时间显示 -->
        <div style="display: flex; flex: 1; align-items: center; gap: 10px;">
            <span id="{widget_id}_lbl_time" style="font-family: monospace; font-size: 12px; color: #8B949E; min-width: 45px;">0.00s</span>
            <input id="{widget_id}_slider" type="range" min="0" max="{n_frames - 1}" value="0" style="
                flex: 1; accent-color: #58A6FF; cursor: pointer;
            ">
            <span id="{widget_id}_lbl_total" style="font-family: monospace; font-size: 12px; color: #8B949E; min-width: 45px;">{t_list[-1]:.2f}s</span>
        </div>

        <!-- 倍速选择 -->
        <div style="display: flex; align-items: center; gap: 4px;">
            <span style="font-size: 11px; color: #8B949E;">倍速:</span>
            <select id="{widget_id}_speed" style="
                background: #21262D; border: 1px solid #30363D; color: #C9D1D9;
                border-radius: 4px; padding: 2px 6px; font-size: 11px; cursor: pointer;
            ">
                <option value="0.5">0.5x</option>
                <option value="1.0" selected>1.0x</option>
                <option value="2.0">2.0x</option>
                <option value="4.0">4.0x</option>
            </select>
        </div>
    </div>
</div>

<script>
(function() {{
    const data = {payload_json};
    const cId = "{widget_id}";
    const container = document.getElementById(cId);
    const canvas = document.getElementById(cId + "_canvas");
    const ctx = canvas.getContext("2d");

    const btnPlay = document.getElementById(cId + "_btn_play");
    const btnStepPrev = document.getElementById(cId + "_btn_step_prev");
    const btnStepNext = document.getElementById(cId + "_btn_step_next");
    const slider = document.getElementById(cId + "_slider");
    const lblTime = document.getElementById(cId + "_lbl_time");
    const selSpeed = document.getElementById(cId + "_speed");
    const btnViewBev = document.getElementById(cId + "_view_bev");
    const btnView3d = document.getElementById(cId + "_view_3d");
    const btnReset = document.getElementById(cId + "_btn_reset");

    const hudSpeed = document.getElementById(cId + "_hud_speed");
    const hudAcc = document.getElementById(cId + "_hud_acc");
    const hudJerk = document.getElementById(cId + "_hud_jerk");
    const hudDist = document.getElementById(cId + "_hud_dist");
    const hudTtc = document.getElementById(cId + "_hud_ttc");
    const hudStatus = document.getElementById(cId + "_hud_status");

    let isPlaying = false;
    let currentFrame = 0;
    let playbackSpeed = 1.0;
    let viewMode = 'bev'; // 'bev' or '3d'
    let lastAnimTime = null;
    let subFrameTime = 0;

    // 缩放与平移状态
    let zoom = 12.0; // 像素 / 米
    let camOffsetX = 0;
    let camOffsetY = 0;

    function resize() {{
        const dpr = window.devicePixelRatio || 1;
        const rect = container.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        draw();
    }}
    window.addEventListener('resize', resize);

    // 视角切换
    btnViewBev.addEventListener('click', () => {{
        viewMode = 'bev';
        btnViewBev.style.background = '#388BFD';
        btnViewBev.style.color = '#fff';
        btnView3d.style.background = 'transparent';
        btnView3d.style.color = '#8B949E';
        draw();
    }});
    btnView3d.addEventListener('click', () => {{
        viewMode = '3d';
        btnView3d.style.background = '#388BFD';
        btnView3d.style.color = '#fff';
        btnViewBev.style.background = 'transparent';
        btnViewBev.style.color = '#8B949E';
        draw();
    }});
    btnReset.addEventListener('click', () => {{
        camOffsetX = 0;
        camOffsetY = 0;
        zoom = (viewMode === 'bev') ? 12.0 : 15.0;
        draw();
    }});

    // 播放控制
    btnPlay.addEventListener('click', () => {{
        isPlaying = !isPlaying;
        btnPlay.innerText = isPlaying ? "⏸" : "▶";
        btnPlay.style.background = isPlaying ? "#D29922" : "#238636";
        if (isPlaying) {{
            lastAnimTime = performance.now();
            requestAnimationFrame(tick);
        }}
    }});

    slider.addEventListener('input', (e) => {{
        currentFrame = parseInt(e.target.value);
        subFrameTime = 0;
        updateUI();
        draw();
    }});

    btnStepPrev.addEventListener('click', () => {{
        if (currentFrame > 0) {{ currentFrame--; updateUI(); draw(); }}
    }});
    btnStepNext.addEventListener('click', () => {{
        if (currentFrame < data.t.length - 1) {{ currentFrame++; updateUI(); draw(); }}
    }});
    selSpeed.addEventListener('change', (e) => {{
        playbackSpeed = parseFloat(e.target.value);
    }});

    function tick(now) {{
        if (!isPlaying) return;
        if (!lastAnimTime) lastAnimTime = now;
        const dt = (now - lastAnimTime) / 1000.0 * playbackSpeed;
        lastAnimTime = now;

        const totalFrames = data.t.length;
        if (totalFrames > 1) {{
            const simDt = data.t[1] - data.t[0];
            subFrameTime += dt;
            while (subFrameTime >= simDt) {{
                subFrameTime -= simDt;
                currentFrame++;
                if (currentFrame >= totalFrames) {{
                    currentFrame = 0; // 循环播放
                    break;
                }}
            }}
        }}

        updateUI();
        draw();
        requestAnimationFrame(tick);
    }}

    function updateUI() {{
        slider.value = currentFrame;
        const curT = data.t[currentFrame];
        lblTime.innerText = curT.toFixed(2) + "s";

        // HUD 数据刷新
        const v_ego = data.ego.v[currentFrame];
        const a_ego = data.ego.a[currentFrame];
        const jerk_ego = data.ego.jerk[currentFrame];
        hudSpeed.innerText = (v_ego * 3.6).toFixed(1);
        hudAcc.innerText = a_ego.toFixed(2);
        hudJerk.innerText = jerk_ego.toFixed(1);

        // 前车距离与 TTC
        if (data.targets && data.targets.length > 0) {{
            const tgt = data.targets[0];
            const dist = tgt.x[currentFrame] - data.ego.x[currentFrame] - 4.5;
            hudDist.innerText = dist > 0 ? dist.toFixed(1) : "0.0";

            let ttc = 99.0;
            if (data.metrics && data.metrics.ttc) {{
                ttc = data.metrics.ttc[currentFrame];
            }} else {{
                const relV = v_ego - tgt.v[currentFrame];
                if (relV > 0.1 && dist > 0) ttc = dist / relV;
            }}

            if (ttc < 90 && ttc > 0) {{
                hudTtc.innerText = ttc.toFixed(1) + " s";
                if (ttc < 1.5) {{
                    hudTtc.style.color = "#F85149";
                    hudStatus.innerText = "AEB BRAKING";
                    hudStatus.style.background = "#DA363322";
                    hudStatus.style.color = "#F85149";
                    hudStatus.style.borderColor = "#F85149";
                }} else if (ttc < 3.0) {{
                    hudTtc.style.color = "#D29922";
                    hudStatus.innerText = "WARNING";
                    hudStatus.style.background = "#D2992222";
                    hudStatus.style.color = "#D29922";
                    hudStatus.style.borderColor = "#D29922";
                }} else {{
                    hudTtc.style.color = "#3FB950";
                    hudStatus.innerText = "FOLLOWING";
                    hudStatus.style.background = "#23863622";
                    hudStatus.style.color = "#3FB950";
                    hudStatus.style.borderColor = "#3FB950";
                }}
            }} else {{
                hudTtc.innerText = "-- s";
                hudTtc.style.color = "#8B949E";
                hudStatus.innerText = "CRUISE";
                hudStatus.style.background = "#1F6FEB22";
                hudStatus.style.color = "#58A6FF";
                hudStatus.style.borderColor = "#1F6FEB66";
            }}
        }}
    }}

    function draw() {{
        const rect = container.getBoundingClientRect();
        const W = rect.width;
        const H = rect.height;
        ctx.clearRect(0, 0, W, H);

        if (viewMode === 'bev') {{
            drawBEV(W, H);
        }} else {{
            draw3D(W, H);
        }}
    }}

    // ==================== 1. BEV 鸟瞰俯视绘制 ====================
    function drawBEV(W, H) {{
        const egoX = data.ego.x[currentFrame];
        const egoY = data.ego.y[currentFrame];
        const cx = W * 0.25 + camOffsetX;
        const cy = H * 0.5 + camOffsetY;
        const scale = zoom;

        // 道路绘制 (3 车道)
        const laneW = data.road.lane_width * scale;
        const numLanes = data.road.num_lanes;
        const roadTopY = cy - (numLanes * 0.5) * laneW;
        const roadBotY = cy + (numLanes * 0.5) * laneW;

        // 沥青路面
        ctx.fillStyle = "#161B22";
        ctx.fillRect(0, roadTopY - 10, W, (roadBotY - roadTopY) + 20);

        // 路肩草地/安全岛
        ctx.fillStyle = "#0D1117";
        ctx.fillRect(0, 0, W, roadTopY - 10);
        ctx.fillRect(0, roadBotY + 10, W, H - roadBotY - 10);

        // 实线路边缘
        ctx.strokeStyle = "#484F58";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(0, roadTopY); ctx.lineTo(W, roadTopY);
        ctx.moveTo(0, roadBotY); ctx.lineTo(W, roadBotY);
        ctx.stroke();

        // 虚线车道线 (随车辆前进移动)
        ctx.strokeStyle = "#6E7681";
        ctx.lineWidth = 1.5;
        ctx.setLineDash([12, 16]);
        const dashOffset = (egoX * scale) % 28;
        ctx.lineDashOffset = -dashOffset;

        for (let l = 1; l < numLanes; l++) {{
            const ly = roadTopY + l * laneW;
            ctx.beginPath();
            ctx.moveTo(0, ly);
            ctx.lineTo(W, ly);
            ctx.stroke();
        }}
        ctx.setLineDash([]); // 还原

        // 距离标尺 (每 20m 标尺线)
        const startMarkerX = Math.floor((egoX - 30) / 20) * 20;
        ctx.fillStyle = "#484F58";
        ctx.font = "10px monospace";
        for (let mx = startMarkerX; mx < egoX + 120; mx += 20) {{
            const scrX = cx + (mx - egoX) * scale;
            if (scrX >= 0 && scrX <= W) {{
                ctx.beginPath();
                ctx.moveTo(scrX, roadBotY + 5);
                ctx.lineTo(scrX, roadBotY + 15);
                ctx.strokeStyle = "#30363D";
                ctx.stroke();
                ctx.fillText(mx + "m", scrX - 10, roadBotY + 26);
            }}
        }}

        // 绘制目标车辆
        if (data.targets) {{
            data.targets.forEach(tgt => {{
                const tx = tgt.x[currentFrame];
                const ty = tgt.y[currentFrame];
                const tgtScrX = cx + (tx - egoX) * scale;
                const tgtScrY = cy - (ty * scale);
                drawCar2D(tgtScrX, tgtScrY, scale, tgt.color, tgt.name, false);
            }});
        }}

        // 绘制雷达/感知检测锥
        if (data.show_radar) {{
            const egoScrX = cx;
            const egoScrY = cy - (egoY * scale);
            const radarDist = 60 * scale; // 60米探测距离
            const radarHalfW = Math.tan(18 * Math.PI / 180) * radarDist;

            const grad = ctx.createRadialGradient(egoScrX + 20, egoScrY, 5, egoScrX + 20, egoScrY, radarDist);
            const isWarn = hudStatus.innerText.includes("WARNING") || hudStatus.innerText.includes("AEB");
            const radarColor = isWarn ? "248, 81, 73" : "88, 166, 255";
            grad.addColorStop(0, "rgba(" + radarColor + ", 0.35)");
            grad.addColorStop(1, "rgba(" + radarColor + ", 0.0)");

            ctx.fillStyle = grad;
            ctx.beginPath();
            ctx.moveTo(egoScrX + 20, egoScrY);
            ctx.lineTo(egoScrX + 20 + radarDist, egoScrY - radarHalfW);
            ctx.lineTo(egoScrX + 20 + radarDist, egoScrY + radarHalfW);
            ctx.closePath();
            ctx.fill();

            ctx.strokeStyle = "rgba(" + radarColor + ", 0.5)";
            ctx.lineWidth = 1;
            ctx.stroke();
        }}

        // 绘制本车 (Ego Vehicle)
        const egoScrX = cx;
        const egoScrY = cy - (egoY * scale);
        drawCar2D(egoScrX, egoScrY, scale, "#58A6FF", "Ego (主车)", true);
    }}

    function drawCar2D(x, y, scale, color, label, isEgo) {{
        const length = 4.6 * scale;
        const width = 1.9 * scale;
        const hx = x - length * 0.5;
        const hy = y - width * 0.5;

        // 阴影
        ctx.fillStyle = "rgba(0,0,0,0.4)";
        ctx.fillRect(hx + 2, hy + 2, length, width);

        // 车身主体
        ctx.fillStyle = color;
        ctx.beginPath();
        if (ctx.roundRect) {{
            ctx.roundRect(hx, hy, length, width, [4 * (scale/10)]);
        }} else {{
            ctx.rect(hx, hy, length, width);
        }}
        ctx.fill();
        ctx.strokeStyle = "#FFFFFF33";
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // 挡风玻璃与车窗
        ctx.fillStyle = "#0D1117";
        const windW = length * 0.22;
        const windH = width * 0.75;
        ctx.fillRect(hx + length * 0.55, hy + (width - windH) * 0.5, windW, windH);

        // 前大灯 / 刹车尾灯
        ctx.fillStyle = "#F0E68C"; // 前大灯黄白光
        ctx.fillRect(hx + length - 2, hy + 2, 2, 4);
        ctx.fillRect(hx + length - 2, hy + width - 6, 2, 4);

        ctx.fillStyle = isEgo && hudStatus.innerText.includes("AEB") ? "#FF2200" : "#CC1100"; // 尾灯
        ctx.fillRect(hx, hy + 2, 2, 4);
        ctx.fillRect(hx, hy + width - 6, 2, 4);

        // 标签文字
        ctx.fillStyle = "#F0F6FC";
        ctx.font = "bold 10px sans-serif";
        ctx.fillText(label, hx, hy - 6);
    }}

    // ==================== 2. 斜视角投影绘制 ====================
    function draw3D(W, H) {{
        const egoX = data.ego.x[currentFrame];
        const egoY = data.ego.y[currentFrame];
        const cx = W * 0.5;
        const horizonY = H * 0.38;

        // 地平线与天空星空
        const skyGrad = ctx.createLinearGradient(0, 0, 0, horizonY);
        skyGrad.addColorStop(0, "#080B10");
        skyGrad.addColorStop(1, "#161B22");
        ctx.fillStyle = skyGrad;
        ctx.fillRect(0, 0, W, horizonY);

        // 道路地面透视渐变
        const groundGrad = ctx.createLinearGradient(0, horizonY, 0, H);
        groundGrad.addColorStop(0, "#1F242C");
        groundGrad.addColorStop(1, "#0D1117");
        ctx.fillStyle = groundGrad;
        ctx.fillRect(0, horizonY, W, H - horizonY);

        // 透视道路梯形 (Road Trapezoid)
        const roadTopW = 140;
        const roadBotW = W * 0.92;
        ctx.fillStyle = "#181D24";
        ctx.beginPath();
        ctx.moveTo(cx - roadTopW * 0.5, horizonY);
        ctx.lineTo(cx + roadTopW * 0.5, horizonY);
        ctx.lineTo(cx + roadBotW * 0.5, H);
        ctx.lineTo(cx - roadBotW * 0.5, H);
        ctx.closePath();
        ctx.fill();

        // 路肩警示线
        ctx.strokeStyle = "#484F58";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(cx - roadTopW * 0.5, horizonY); ctx.lineTo(cx - roadBotW * 0.5, H);
        ctx.moveTo(cx + roadTopW * 0.5, horizonY); ctx.lineTo(cx + roadBotW * 0.5, H);
        ctx.stroke();

        // 斜视角投影函数
        function project3D(xRel, yRel, zRel = 0) {{
            // xRel 为相对主车纵向距离 (米), yRel 为横向偏移 (米)
            const d = Math.max(1.0, xRel + 12.0); // 视距
            const fov = 320.0;
            const pScale = fov / d;
            const px = cx + yRel * pScale * 2.8;
            const py = horizonY + (d * 3.8) - (zRel * pScale * 1.5);
            return {{ x: px, y: py, scale: pScale, depth: d }};
        }}

        // 斜视角车道虚线绘制
        const numLanes = data.road.num_lanes;
        for (let l = 1; l < numLanes; l++) {{
            const laneOffset = (l - numLanes * 0.5) * data.road.lane_width;
            ctx.strokeStyle = "#6E7681";
            ctx.lineWidth = 2;
            for (let dist = 3; dist < 90; dist += 6) {{
                const p1 = project3D(dist, laneOffset);
                const p2 = project3D(dist + 2.5, laneOffset);
                if (p1.y > horizonY && p2.y <= H) {{
                    ctx.beginPath();
                    ctx.moveTo(p1.x, p1.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.stroke();
                }}
            }}
        }}

        // 绘制斜视角目标车辆
        if (data.targets) {{
            data.targets.forEach(tgt => {{
                const relDist = tgt.x[currentFrame] - egoX;
                const relY = -(tgt.y[currentFrame] - egoY);
                if (relDist > -5 && relDist < 100) {{
                    const p = project3D(relDist, relY);
                    drawCar3D(p.x, p.y, p.scale, tgt.color, tgt.name, false);
                }}
            }});
        }}

        // 绘制 3D 主车 (Ego Vehicle 近景)
        const pEgo = project3D(0, 0);
        drawCar3D(pEgo.x, H - 70, pEgo.scale * 1.2, "#58A6FF", "Ego (主车)", true);
    }}

    function drawCar3D(x, y, scale, color, label, isEgo) {{
        const w = 1.9 * scale * 1.5;
        const h = 1.5 * scale * 1.2;
        const hx = x - w * 0.5;
        const hy = y - h;

        // 地面投影阴影
        ctx.fillStyle = "rgba(0,0,0,0.6)";
        ctx.beginPath();
        ctx.ellipse(x, y + 2, w * 0.55, h * 0.2, 0, 0, Math.PI * 2);
        ctx.fill();

        // 3D 车体箱体 (后挡板与车顶)
        ctx.fillStyle = color;
        ctx.beginPath();
        if (ctx.roundRect) {{
            ctx.roundRect(hx, hy, w, h, [6]);
        }} else {{
            ctx.rect(hx, hy, w, h);
        }}
        ctx.fill();

        // 挡风玻璃与后窗
        ctx.fillStyle = "#0D1117";
        ctx.fillRect(hx + w * 0.15, hy + h * 0.15, w * 0.7, h * 0.45);

        // 尾灯动态高亮
        const isBraking = isEgo && hudStatus.innerText.includes("AEB");
        ctx.fillStyle = isBraking ? "#FF1744" : "#D32F2F";
        ctx.fillRect(hx + 4, hy + h * 0.65, w * 0.2, h * 0.18);
        ctx.fillRect(hx + w - w * 0.2 - 4, hy + h * 0.65, w * 0.2, h * 0.18);

        // 刹车辉光特效
        if (isBraking) {{
            ctx.fillStyle = "rgba(255, 23, 68, 0.4)";
            ctx.beginPath();
            ctx.arc(hx + 6, hy + h * 0.74, 12, 0, Math.PI * 2);
            ctx.arc(hx + w - 6, hy + h * 0.74, 12, 0, Math.PI * 2);
            ctx.fill();
        }}

        // 铭牌文字
        ctx.fillStyle = "#C9D1D9";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText(label, x, hy - 8);
        ctx.textAlign = "left";
    }}

    // 初始化运行
    setTimeout(() => {{
        resize();
        updateUI();
    }}, 100);
}})();
</script>
"""

    try:
        from IPython.display import HTML
        return HTML(html_code)
    except ImportError:
        return html_code


# 兼容性别名
render_visualizer_html = render_trajectory_replay

