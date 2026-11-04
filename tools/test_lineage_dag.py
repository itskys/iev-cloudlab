#!/usr/bin/env python3
"""test_lineage_dag.py
测试生成跨域工程数据血缘交互式拓扑图 SVG
"""

def render_data_lineage_dag_svg(scores: dict = None) -> str:
    """生成三链贯通跨域工程数据血缘 DAG 拓扑图 SVG (响应式矢量图)"""
    scores = scores or {}

    # 3 条核心工程链定义
    # 链 1: 新能源动力与电耗 (D3 -> C1 -> C4 -> Capstone)
    # 链 2: 智驾感知与规控 (H1 -> A1 -> A2 -> E3 -> Capstone)
    # 链 3: 车联网车路协同 (B1 -> B3 -> B4 -> B5 -> Capstone)

    nodes = [
        # 链 1
        {"id": "D3", "title": "电芯准静态OCV", "chain": 1, "x": 60, "y": 65, "artifact": "ocv_soc.csv"},
        {"id": "C1", "title": "FASTSim动力学电耗", "chain": 1, "x": 260, "y": 65, "artifact": "kwh_100km.json"},
        {"id": "C4", "title": "混动ECMS能量管理", "chain": 1, "x": 490, "y": 65, "artifact": "ecms_s_factor.json"},

        # 链 2
        {"id": "H1", "title": "加塞场景空间测绘", "chain": 2, "x": 60, "y": 160, "artifact": "cutin_space.xosc"},
        {"id": "A1", "title": "Cut-in AEB避碰", "chain": 2, "x": 240, "y": 160, "artifact": "aeb_profile.json"},
        {"id": "A2", "title": "ACC巡航跟车", "chain": 2, "x": 420, "y": 160, "artifact": "acc_spacing.csv"},
        {"id": "E3", "title": "CasADi MPC优化", "chain": 2, "x": 600, "y": 160, "artifact": "mpc_weights.json"},

        # 链 3
        {"id": "B1", "title": "IDM真实跟驰标定", "chain": 3, "x": 60, "y": 255, "artifact": "idm_calib.json"},
        {"id": "B3", "title": "V2X编队弦稳定", "chain": 3, "x": 240, "y": 255, "artifact": "cacc_delay.json"},
        {"id": "B4", "title": "LWR交通冲击波", "chain": 3, "x": 420, "y": 255, "artifact": "wave_speed.json"},
        {"id": "B5", "title": "干线绿波带协调", "chain": 3, "x": 600, "y": 255, "artifact": "offset_sync.json"},

        # 终点
        {"id": "Capstone", "title": "全域协同总成调度", "chain": 0, "x": 800, "y": 160, "artifact": "iev_integrated_report.pdf"},
    ]

    edges = [
        # Chain 1
        ("D3", "C1", "ocv_soc.csv"),
        ("C1", "C4", "kwh_100km.json"),
        ("C4", "Capstone", "ecms_opt.json"),

        # Chain 2
        ("H1", "A1", "cutin.xosc"),
        ("A1", "A2", "aeb_profile.json"),
        ("A2", "E3", "acc_err.csv"),
        ("E3", "Capstone", "mpc_cmd.json"),

        # Chain 3
        ("B1", "B3", "idm_params.json"),
        ("B3", "B4", "delay_flow.json"),
        ("B4", "B5", "shockwave.json"),
        ("B5", "Capstone", "green_wave.json"),
    ]

    node_map = {n["id"]: n for n in nodes}

    svg = ['<svg width="100%" height="100%" viewBox="0 0 960 320" xmlns="http://www.w3.org/2000/svg" style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; font-family:system-ui,-apple-system,sans-serif;">']
    svg.append('<defs>')
    svg.append('<marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
    svg.append('<path d="M 0 1 L 10 5 L 0 9 z" fill="#94a3b8" />')
    svg.append('</marker>')
    svg.append('<marker id="arrow-green" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
    svg.append('<path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />')
    svg.append('</marker>')
    svg.append('<linearGradient id="capstone-grad" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#fef08a"/><stop offset="100%" stop-color="#fde047"/></linearGradient>')
    svg.append('</defs>')

    # 链条分类标签
    svg.append('<text x="20" y="32" font-size="12" font-weight="700" fill="#2563eb">🔋 链 1：动力电池与整车能耗链</text>')
    svg.append('<text x="20" y="130" font-size="12" font-weight="700" fill="#0284c7">🚗 链 2：智驾极限感知与规划控制链</text>')
    svg.append('<text x="20" y="228" font-size="12" font-weight="700" fill="#059669">🌐 链 3：车联网车路协同与交通流链</text>')

    # 绘制连线
    for u_id, v_id, asset in edges:
        u = node_map[u_id]
        v = node_map[v_id]
        ux = u["x"] + (110 if u_id != "Capstone" else 130)
        uy = u["y"] + 20
        vx = v["x"]
        vy = v["y"] + 20

        # 判断上游是否已完成
        u_score = scores.get(u_id, {})
        u_done = bool(u_score.get("passed", False)) or (isinstance(u_score, (int, float)) and u_score >= 60)
        stroke_color = "#10b981" if u_done else "#94a3b8"
        marker_id = "arrow-green" if u_done else "arrow"
        dash_arr = "" if u_done else "stroke-dasharray='4,4'"

        # 曲线路径
        svg.append(f'<path d="M {ux} {uy} C {(ux+vx)/2} {uy}, {(ux+vx)/2} {vy}, {vx} {vy}" fill="none" stroke="{stroke_color}" stroke-width="1.8" {dash_arr} marker-end="url(#{marker_id})" />')
        # 传递的数据资产标签
        mid_x = (ux + vx) / 2
        mid_y = (uy + vy) / 2 - 4
        svg.append(f'<text x="{mid_x}" y="{mid_y}" font-size="9" fill="#64748b" text-anchor="middle" font-family="monospace">{asset}</text>')

    # 绘制节点
    for n in nodes:
        nid = n["id"]
        nx = n["x"]
        ny = n["y"]
        is_cap = (nid == "Capstone")
        nw = 136 if is_cap else 115
        nh = 42

        sc = scores.get(nid, {})
        is_passed = bool(sc.get("passed", False)) or (isinstance(sc, (int, float)) and sc >= 60)
        has_score = (isinstance(sc, dict) and 'score' in sc) or isinstance(sc, (int, float))
        score_val = sc.get('score', 0) if isinstance(sc, dict) else (sc if isinstance(sc, (int, float)) else 0)

        if is_cap:
            bg = "url(#capstone-grad)"
            border = "#eab308"
            bw = "2.5"
            badge = "★ 终极"
            badge_color = "#854d0e"
            status_text = "三链汇流贯通"
            status_color = "#a16207"
        elif is_passed:
            bg = "#ecfdf5"
            border = "#10b981"
            bw = "1.8"
            badge = "✔ 达标"
            badge_color = "#047857"
            status_text = f"{score_val:.0f}分" if has_score else "已完成"
            status_color = "#059669"
        elif has_score and score_val < 60:
            bg = "#fffbeb"
            border = "#f59e0b"
            bw = "1.8"
            badge = "⚠️ 偏差"
            badge_color = "#b45309"
            status_text = f"{score_val:.0f}分 需重整"
            status_color = "#d97706"
        else:
            bg = "#ffffff"
            border = "#cbd5e1"
            bw = "1.2"
            badge = "⏳ 待研"
            badge_color = "#64748b"
            status_text = "输入就绪"
            status_color = "#94a3b8"

        svg.append(f'<rect x="{nx}" y="{ny}" width="{nw}" height="{nh}" rx="6" fill="{bg}" stroke="{border}" stroke-width="{bw}" />')
        svg.append(f'<text x="{nx+8}" y="{ny+16}" font-size="11" font-weight="700" fill="#0f172a">{nid} <tspan font-size="9.5" font-weight="normal" fill="#475569">{n["title"]}</tspan></text>')
        svg.append(f'<rect x="{nx+nw-42}" y="{ny+5}" width="36" height="14" rx="3" fill="#ffffff88" />')
        svg.append(f'<text x="{nx+nw-24}" y="{ny+15}" font-size="8.5" font-weight="700" fill="{badge_color}" text-anchor="middle">{badge}</text>')
        svg.append(f'<text x="{nx+8}" y="{ny+32}" font-size="9" fill="{status_color}">{status_text}</text>')

    svg.append('</svg>')
    return "".join(svg)

if __name__ == "__main__":
    test_scores = {"D3": {"passed": True, "score": 92}, "A1": {"passed": True, "score": 88}, "B1": {"passed": False, "score": 45}}
    svg_code = render_data_lineage_dag_svg(test_scores)
    assert "<svg" in svg_code and "</svg>" in svg_code
    print("DAG SVG generation test passed successfully! Length:", len(svg_code))
