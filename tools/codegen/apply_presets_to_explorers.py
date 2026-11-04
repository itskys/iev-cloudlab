#!/usr/bin/env python3
"""apply_presets_to_explorers.py
自动向 labs/common/lab_explorers.py 注入：
1. 教师一键案例快照对标栏 (_create_preset_bar)
2. 行业真实车型与车规量规物理锚点 (_create_benchmark_badge)
3. 一键恢复出厂默认参数与基线对比
"""

import os
import re
import ast

CONFIGS = {
    "show_a1_explorer": {
        "title": "Euro NCAP AEB 介入时机量规",
        "standard": "对标 Euro NCAP 2023 & ISO 22838",
        "benchmarks": [
            ("FCW 碰撞预警", "2.7~3.0s", "info"),
            ("PB 部分制动", "1.8~2.2s", "warning"),
            ("EB 极限制动", "1.2~1.5s", "danger"),
        ],
        "presets": [
            {"title": "⚡ 激进加塞 (TTC=1.8s)", "style": "warning", "values": {"ttc": 1.8}, "tip": "近距离变道加塞，AEB 紧急制动介入"},
            {"title": "🎯 极限制动 (TTC=2.4s)", "style": "primary", "values": {"ttc": 2.4}, "tip": "临界安全阈值，刚好零碰撞刹停"},
            {"title": "🛡️ 稳健安全 (TTC=3.2s)", "style": "success", "values": {"ttc": 3.2}, "tip": "提前制动介入，从容避碰"},
        ],
        "defaults": {"ttc": 3.0},
        "setters": "{'ttc': slider_ttc}",
    },
    "show_a2_explorer": {
        "title": "ISO 15622 跟车平顺性与时距量规",
        "standard": "对标 ISO 15622 Class IV",
        "benchmarks": [
            ("时距 Th", "1.0~2.0s", "info"),
            ("舒适减速", "-1.5 ~ +1.5 m/s²", "success"),
            ("急刹临界", "<-3.0 m/s² (不适)", "danger"),
        ],
        "presets": [
            {"title": "🛋️ 舒适稳态跟车 (Th=1.5s, Kp=0.8, Kd=0.6)", "style": "success", "values": {"th": 1.5, "kp": 0.8, "kd": 0.6}, "tip": "时距充裕，加速度处于舒适区间无顿挫"},
            {"title": "⚡ 激进追赶震荡 (Th=0.8s, Kp=1.8, Kd=0.3)", "style": "warning", "values": {"th": 0.8, "kp": 1.8, "kd": 0.3}, "tip": "刚度过大，强烈超调并伴随急刹"},
            {"title": "🐢 迟缓保守跟车 (Th=1.8s, Kp=0.4, Kd=0.9)", "style": "", "values": {"th": 1.8, "kp": 0.4, "kd": 0.9}, "tip": "刚度偏低，间距收敛迟缓"},
        ],
        "defaults": {"th": 1.0, "kp": 0.8, "kd": 0.5},
        "setters": "{'th': slider_th, 'kp': slider_kp, 'kd': slider_kd}",
    },
    "show_a3_explorer": {
        "title": "紧急制动附着力极限与前车加速度",
        "standard": "对标 GB/T 39901 乘用车 AEB 规范",
        "benchmarks": [
            ("舒适刹车", "-1.5 m/s²", "success"),
            ("中度刹车", "-3.5 m/s²", "warning"),
            ("干沥青极限", "-7.5~-8.0 m/s²", "danger"),
        ],
        "presets": [
            {"title": "⚠️ 朴素 TTC 失效工况 (alead=-5.0, TTC=2.0s)", "style": "danger", "values": {"alead": -5.0, "ttc": 2.0}, "tip": "前车猛刹，朴素 TTC 低估碰撞风险导致追尾"},
            {"title": "🛡️ 增强型 TTC 预警 (alead=-4.0, TTC=2.8s)", "style": "success", "values": {"alead": -4.0, "ttc": 2.8}, "tip": "前车急刹补偿，提前启动全力制动"},
            {"title": "🍃 缓和减速工况 (alead=-1.5, TTC=2.5s)", "style": "info", "values": {"alead": -1.5, "ttc": 2.5}, "tip": "前车轻刹，平稳跟停"},
        ],
        "defaults": {"alead": -4.0, "ttc": 2.0},
        "setters": "{'alead': slider_alead, 'ttc': slider_ttc}",
    },
    "show_a4_explorer": {
        "title": "NHTSA 交叉口左转临界可接受间隙",
        "standard": "对标 NHTSA Intersection Safety",
        "benchmarks": [
            ("安全待转间隙", "≥ 5.5s", "success"),
            ("临界博弈间隙", "4.0~5.0s", "warning"),
            ("高危冲突间隙", "< 3.5s", "danger"),
        ],
        "presets": [
            {"title": "🚨 危险强穿博弈 (Gap=2.5s, 60km/h)", "style": "danger", "values": {"gap": 2.5, "opp_v": 60}, "tip": "间隙严重不足且对向车速高，极易侧面成撞"},
            {"title": "🛡️ 规范安全让行 (Gap=5.5s, 50km/h)", "style": "success", "values": {"gap": 5.5, "opp_v": 50}, "tip": "从容待转，时隙充裕安全穿越"},
            {"title": "⏱️ 临界压哨穿越 (Gap=3.8s, 40km/h)", "style": "warning", "values": {"gap": 3.8, "opp_v": 40}, "tip": "对向车速较低，刚好贴边通过"},
        ],
        "defaults": {"gap": 4.0, "opp_v": 60},
        "setters": "{'gap': slider_gap, 'opp_v': slider_opp_v}",
    },
    "show_a5_explorer": {
        "title": "公路工程技术标准高速合流加速量规",
        "standard": "对标 JTG D20 公路路线设计规范",
        "benchmarks": [
            ("推荐汇入时距", "≥ 3.0s", "success"),
            ("舒适提速", "1.2~1.8 m/s²", "info"),
            ("匝道急加速", "> 2.5 m/s²", "warning"),
        ],
        "presets": [
            {"title": "🚗 平顺协同汇入 (a=1.5 m/s², Gap=3.5s)", "style": "success", "values": {"accel": 1.5, "gap": 3.5}, "tip": "主线空当充裕，平顺加速对齐主线车速"},
            {"title": "⚡ 激进窄隙抢插 (a=2.2 m/s², Gap=1.6s)", "style": "warning", "values": {"accel": 2.2, "gap": 1.6}, "tip": "大油门全力提速，强插窄缝逼停后车"},
            {"title": "🐢 动力犹豫阻滞 (a=0.8 m/s², Gap=2.0s)", "style": "danger", "values": {"accel": 0.8, "gap": 2.0}, "tip": "提速迟缓导致汇入端速度严重脱节"},
        ],
        "defaults": {"accel": 1.8, "gap": 2.5},
        "setters": "{'accel': slider_accel, 'gap': slider_gap}",
    },
    "show_b1_explorer": {
        "title": "真实人类驾驶员跟驰参数实测范围",
        "standard": "对标 NGSIM 典型高速微观跟驰数据集",
        "benchmarks": [
            ("车头时距 T", "1.2~1.8s", "info"),
            ("舒适减速 b", "1.2~2.0 m/s²", "success"),
            ("最大加速 a", "1.0~2.0 m/s²", "neutral"),
        ],
        "presets": [
            {"title": "🎯 黄金实测标定 (T=1.5s, b=1.5, a=1.2)", "style": "success", "values": {"t": 1.5, "b": 1.5, "a": 1.2}, "tip": "拟合误差 RMSE<0.60，完美复现真实减速轨迹"},
            {"title": "🏎️ 激进跟车 (T=1.0s, b=2.5, a=2.0)", "style": "warning", "values": {"t": 1.0, "b": 2.5, "a": 2.0}, "tip": "紧贴前车急加速急减速，易引发幽灵拥堵"},
            {"title": "🐢 佛系大间距 (T=2.2s, b=1.0, a=0.8)", "style": "", "values": {"t": 2.2, "b": 1.0, "a": 0.8}, "tip": "时距过大减速佛系，通行效率降低"},
        ],
        "defaults": {"t": 1.5, "b": 1.5, "a": 1.2},
        "setters": "{'t': slider_t, 'b': slider_b, 'a': slider_a}",
    },
    "show_b2_explorer": {
        "title": "城市交叉口信号控制规范配时标准",
        "standard": "对标 GB/T 31418 道路交通信号控制规范",
        "benchmarks": [
            ("最小绿灯时间", "≥ 15s (行人过街)", "info"),
            ("饱和度最佳区间", "0.75 ~ 0.85", "success"),
            ("过饱和排队", "> 0.90 (延误激增)", "danger"),
        ],
        "presets": [
            {"title": "⚖️ 平峰均衡配时 (EW=27s)", "style": "success", "values": {"ew": 27}, "tip": "东西南北相位平衡，总延误最小"},
            {"title": "🌊 东西高峰特长绿灯 (EW=40s)", "style": "info", "values": {"ew": 40}, "tip": "东西向大车流放行，南北向轻微排队"},
            {"title": "⚠️ 严重失衡拥堵配时 (EW=15s)", "style": "danger", "values": {"ew": 15}, "tip": "东西向绿灯被压榨至极限，产生严重倒灌拥堵"},
        ],
        "defaults": {"ew": 27},
        "setters": "{'ew': slider_ew}",
    },
    "show_b3_explorer": {
        "title": "车联网 C-V2X 通信时延与车辆编队量规",
        "standard": "对标 3GPP Rel-16 V2X & SAE J3161",
        "benchmarks": [
            ("5G-V2X PC5 时延", "< 20ms", "success"),
            ("4G LTE-V 时延", "50~100ms", "info"),
            ("弦不稳定临界", "时延 > 0.2s (易追尾)", "danger"),
        ],
        "presets": [
            {"title": "🛡️ 弦稳定平稳衰减 (Delay=0.04s, Gap=1.0s)", "style": "success", "values": {"delay": 0.04, "gap": 1.0}, "tip": "通信极快时距合适，后车扰动逐步衰减"},
            {"title": "🚨 弦不稳定振荡放大 (Delay=0.25s, Gap=0.4s)", "style": "danger", "values": {"delay": 0.25, "gap": 0.4}, "tip": "时延过长导致误差逐车放大，发生追尾"},
            {"title": "🏎️ 极致 5G-V2X 紧凑编队 (Delay=0.02s, Gap=0.4s)", "style": "info", "values": {"delay": 0.02, "gap": 0.4}, "tip": "超低时延支持极紧凑编队，显著降低风阻"},
        ],
        "defaults": {"delay": 0.08, "gap": 0.6},
        "setters": "{'delay': slider_delay, 'gap': slider_gap}",
    },
    "show_b4_explorer": {
        "title": "高速公路通行能力与拥堵波速对标",
        "standard": "对标 HCM 2020 (Highway Capacity Manual)",
        "benchmarks": [
            ("单车道通行能力极限", "1800~2200 pcu/h/ln", "info"),
            ("自由流速度 vf", "100~120 km/h", "success"),
            ("拥堵反向冲击波速", "-15 ~ -20 km/h", "warning"),
        ],
        "presets": [
            {"title": "🌊 突发大流量拥堵 (流入 2200, 瓶颈 500)", "style": "warning", "values": {"qin": 2200, "cneck": 500}, "tip": "严重过饱和，产生强烈的负波速向后倒灌"},
            {"title": "🟢 畅通临界平衡 (流入 1400, 瓶颈 900)", "style": "success", "values": {"qin": 1400, "cneck": 900}, "tip": "流入接近通行力，波速平稳无大排队"},
            {"title": "🚨 突发事故断路 (流入 2000, 瓶颈 300)", "style": "danger", "values": {"qin": 2000, "cneck": 300}, "tip": "瓶颈严重缩水，波速急剧倒灌数公里"},
        ],
        "defaults": {"qin": 1800, "cneck": 600},
        "setters": "{'qin': slider_qin, 'cneck': slider_cneck}",
    },
    "show_b5_explorer": {
        "title": "城市干道绿波协调设计参数",
        "standard": "对标 公安部城市道路交通信号协调控制指导意见",
        "benchmarks": [
            ("干线设计时速", "50~60 km/h", "info"),
            ("路口标准间距", "400~800 m", "neutral"),
            ("最佳相位差", "ΔΦ = L / v (理论)", "success"),
        ],
        "presets": [
            {"title": "🟢 完美绿波共振 (Offset=28s, 50km/h)", "style": "success", "values": {"offset": 28, "speed": 50}, "tip": "相位差完美匹配行驶耗时，3个路口全程零停顿"},
            {"title": "🔴 独立无协调撞红灯 (Offset=0s, 50km/h)", "style": "danger", "values": {"offset": 0, "speed": 50}, "tip": "同时变灯导致车辆到达下游正好红灯截停"},
            {"title": "⚡ 高速绿波巡航 (Offset=20s, 70km/h)", "style": "info", "values": {"offset": 20, "speed": 70}, "tip": "高车速快速通勤，相位差相应缩短"},
        ],
        "defaults": {"offset": 24, "speed": 50},
        "setters": "{'offset': slider_offset, 'speed': slider_speed}",
    },
    "show_c1_explorer": {
        "title": "行业真实车型风阻系数 Cd 谱系",
        "standard": "对标 SAE 汽车空气动力学对标数据库",
        "benchmarks": [
            ("保时捷 Taycan", "0.22", "success"),
            ("特斯拉 Model 3", "0.23", "info"),
            ("主流轿车", "0.28", "neutral"),
            ("城市 SUV", "0.34", "warning"),
            ("硬派越野", "0.40+", "danger"),
        ],
        "presets": [
            {"title": "🚗 纯电轿跑低风阻 (0kg, Cd=0.22 仿Taycan)", "style": "success", "values": {"kg": 0, "cd": 0.22}, "tip": "低风阻单人空载，百公里电耗极低"},
            {"title": "🚙 满员满载城市 SUV (+300kg, Cd=0.34)", "style": "warning", "values": {"kg": 300, "cd": 0.34}, "tip": "SUV迎风面与质量双增，滚动与风阻功剧增"},
            {"title": "🛻 满载越野恶劣风阻 (+400kg, Cd=0.40)", "style": "danger", "values": {"kg": 400, "cd": 0.40}, "tip": "高车身满负荷，百公里电耗增加 40%+"},
        ],
        "defaults": {"kg": 0, "cd": 0.29},
        "setters": "{'kg': slider_kg, 'cd': slider_cd}",
    },
    "show_c2_explorer": {
        "title": "各级别纯电动汽车百公里电耗基准",
        "standard": "对标 工信部乘用车能耗标识工况",
        "benchmarks": [
            ("A00/A0 紧凑级", "10~12 kWh/100km", "success"),
            ("B 级主流轿车", "12~14 kWh/100km", "info"),
            ("C 级豪华 SUV", "16~20 kWh/100km", "warning"),
            ("纯电重卡/客车", "100~140 kWh/100km", "danger"),
        ],
        "presets": [
            {"title": "🚗 Model 3 @ 市区工况", "style": "info", "values": {"veh": "Tesla Model 3", "cycle": "市区工况 (UDDS)"}, "tip": "中型纯电轿车市区低速工况"},
            {"title": "🚙 Ford F-150 @ 高速工况", "style": "warning", "values": {"veh": "Ford F-150 (重型皮卡)", "cycle": "高速工况 (HWFET)"}, "tip": "重型皮卡高速迎风工况"},
            {"title": "⚡ Spark EV @ 市区工况", "style": "success", "values": {"veh": "Spark EV (小型代步)", "cycle": "市区工况 (UDDS)"}, "tip": "轻量化小型代步车市区极省电"},
        ],
        "defaults": {"veh": "Tesla Model 3", "cycle": "市区工况 (UDDS)"},
        "setters": "{'veh': drp_veh, 'cycle': drp_cycle}",
    },
    "show_c3_explorer": {
        "title": "能耗损耗去向与车速关系物理基准",
        "standard": "对标 《汽车理论》动力与能耗平衡方程式",
        "benchmarks": [
            ("低速市区 (<40km/h)", "质量惯性与滚阻主导 (>70%)", "info"),
            ("高速匀速 (>100km/h)", "空气阻力主导 (>65%)", "warning"),
            ("风阻功", "∝ v³ (随速度三次方暴增)", "danger"),
        ],
        "presets": [
            {"title": "🏙️ 市区工况载重敏感情境 (+15%质量, 0%风阻 @ 市区)", "style": "info", "values": {"mass": 15, "cd": 0, "cycle": "城市工况 (UDDS)"}, "tip": "频繁启停工况下质量对能耗起决定性作用"},
            {"title": "🛣️ 高速工况风阻敏感反转 (0%质量, +20%风阻 @ 高速)", "style": "warning", "values": {"mass": 0, "cd": 20, "cycle": "高速工况 (HWFET)"}, "tip": "高速匀速工况下风阻成为绝对能耗大头"},
            {"title": "🌱 轻量低风阻协同减碳 (-15%质量, -15%风阻 @ 高速)", "style": "success", "values": {"mass": -15, "cd": -15, "cycle": "高速工况 (HWFET)"}, "tip": "双向优化，大幅拓展高速真实续航"},
        ],
        "defaults": {"mass": 0, "cd": 0, "cycle": "城市工况 (UDDS)"},
        "setters": "{'mass': slider_mass, 'cd': slider_cd, 'cycle': drp_cycle}",
    },
    "show_c4_explorer": {
        "title": "插电混动能量管理与等效油耗量规",
        "standard": "对标 比亚迪 DM-i / 丰田 THS 混动控制逻辑",
        "benchmarks": [
            ("ECMS 黄金平衡 s", "2.5 ~ 2.7 (ΔSOC ≈ 0)", "success"),
            ("纯电透支区 s", "< 2.3 (电池亏电)", "warning"),
            ("强制保电区 s", "> 3.0 (发动机强充油耗高)", "danger"),
            ("SOC 维持窗口", "30% ~ 75%", "info"),
        ],
        "presets": [
            {"title": "⚖️ 黄金电量自持平衡 (s=2.6, SOC0=0.60)", "style": "success", "values": {"s": 2.6, "soc0": 0.60}, "tip": "油电边际汇率精准平衡，综合油耗最优低至2.14L"},
            {"title": "🔋 偏电工况/亏电漂移 (s=2.1, SOC0=0.60)", "style": "warning", "values": {"s": 2.1, "soc0": 0.60}, "tip": "算法低估电价，过度透支电池破坏能量自持"},
            {"title": "⛽ 强制保电/发动机制电 (s=3.2, SOC0=0.45)", "style": "danger", "values": {"s": 3.2, "soc0": 0.45}, "tip": "高估电价强行向电池倒灌，导致综合油耗恶化"},
        ],
        "defaults": {"s": 2.6, "soc0": 0.60},
        "setters": "{'s': slider_s, 'soc0': slider_soc0}",
    },
    "show_d1_explorer": {
        "title": "动力电池充放电倍率与电芯参数",
        "standard": "对标 GB/T 31484 电动汽车用动力蓄电池循环寿命要求",
        "benchmarks": [
            ("BOL 新电芯内阻 R0", "15 ~ 25 mΩ", "success"),
            ("EOL 报废内阻 R0", "> 40 mΩ (衰减翻倍)", "danger"),
            ("持续放电倍率", "1.0 ~ 2.0C", "info"),
            ("脉冲加速倍率", "3.0 ~ 5.0C", "warning"),
        ],
        "presets": [
            {"title": "🔋 温和巡航放电 (1.0C)", "style": "success", "values": {"c": 1.0}, "tip": "端电压平稳，极化压降小"},
            {"title": "⚡ 爆发加速大倍率 (2.0C)", "style": "warning", "values": {"c": 2.0}, "tip": "欧姆内阻与极化急剧拉低端电压，提前触碰截止电压"},
            {"title": "🍃 极低倍率准静态 (0.5C)", "style": "info", "values": {"c": 0.5}, "tip": "最接近热力学平衡电位"},
        ],
        "defaults": {"c": 1.0},
        "setters": "{'c': slider_c}",
    },
    "show_d2_explorer": {
        "title": "Peukert 方程与电芯容量衰减常数",
        "standard": "对标 Peukert's Law: I^k * t = C",
        "benchmarks": [
            ("磷酸铁锂 LFP k", "1.02 ~ 1.05 (倍率性好)", "success"),
            ("三元锂 NCM k", "1.04 ~ 1.08", "info"),
            ("铅酸电池 k", "1.15 ~ 1.30 (衰减严重)", "danger"),
        ],
        "presets": [
            {"title": "🟢 0.2C 慢速放电 (100% 额定容量)", "style": "success", "values": {"crate": 0.2}, "tip": "充分扩散释放全部标称容量"},
            {"title": "🟡 1.0C 额定放电 (95% 容量保持)", "style": "info", "values": {"crate": 1.0}, "tip": "标准工况基准"},
            {"title": "🔴 3.0C 极限大倍率 (82% 容量衰减)", "style": "warning", "values": {"crate": 3.0}, "tip": "扩散受限导致大量电量未放出即触碰截止电压"},
        ],
        "defaults": {"crate": 1.0},
        "setters": "{'crate': slider_crate}",
    },
    "show_d3_explorer": {
        "title": "动力电池静置弛豫时间常数",
        "standard": "对标 SAE J2464 & GB/T 31467 动力电池测试标准",
        "benchmarks": [
            ("双电层物理弛豫", "1 ~ 10s", "info"),
            ("浓度极化消除", "15 ~ 30min", "success"),
            ("高精度 OCV 标定", "静置 ≥ 2小时", "neutral"),
        ],
        "presets": [
            {"title": "🎯 充分弛豫精准辨识 (0.05C, 弛豫 50min)", "style": "success", "values": {"crate": 0.05, "relax": 50}, "tip": "极化电压几乎完全消除，辨识曲线精准贴合平衡 OCV"},
            {"title": "⚠️ 匆忙测试极化残留 (0.25C, 弛豫 15min)", "style": "danger", "values": {"crate": 0.25, "relax": 15}, "tip": "极化严重未散，OCV 出现严重假高或假低畸变"},
            {"title": "⚖️ 工程折中测试 (0.10C, 弛豫 30min)", "style": "info", "values": {"crate": 0.10, "relax": 30}, "tip": "兼顾测试效率与 OCV 辨识精度的工程方案"},
        ],
        "defaults": {"crate": 0.05, "relax": 40},
        "setters": "{'crate': slider_crate, 'relax': slider_relax}",
    },
    "show_d4_explorer": {
        "title": "负极界面电化学析锂安全红线",
        "standard": "对标 宁德时代超充安全边界规范 & GB 38031",
        "benchmarks": [
            ("安全嵌锂电位", "Φs - Φe > 0.05V", "success"),
            ("析锂临界红线", "Φs - Φe = 0.00V", "danger"),
            ("低温快充禁令", "≤0°C 严禁大功率充 (>0.2C)", "danger"),
            ("常温超充温控", "25°C ~ 45°C", "info"),
        ],
        "presets": [
            {"title": "❄️ 极寒未预热强充 (-10°C, 2.0C 致命析锂)", "style": "danger", "values": {"crate": 2.0, "temp": -10}, "tip": "负极电位暴跌穿透 0V，极板严重沉积锂枝晶短路"},
            {"title": "♨️ 热管理预热后快充 (25°C, 2.0C 安全嵌锂)", "style": "success", "values": {"crate": 2.0, "temp": 25}, "tip": "离子扩散活化能充裕，全程无金属锂析出"},
            {"title": "⚡ 常温大倍率闪充 (25°C, 3.5C 临界触边)", "style": "warning", "values": {"crate": 3.5, "temp": 25}, "tip": "大倍率逼近 0V 临界红线，极度依赖热管理散热"},
        ],
        "defaults": {"crate": 2.0, "temp": 25},
        "setters": "{'crate': slider_crate, 'temp': slider_temp}",
    },
    "show_e1_explorer": {
        "title": "单挡纯电动汽车主减速比匹配量规",
        "standard": "对标 GB/T 18385 电动汽车动力性能试验方法",
        "benchmarks": [
            ("最高车速要求", "≥ 160 km/h (需较小速比)", "info"),
            ("最大爬坡度要求", "≥ 30% (需较大速比)", "neutral"),
            ("主流量产单挡速比", "7.5 ~ 9.5", "success"),
        ],
        "presets": [
            {"title": "🏎️ 高速经济性大续航 (i0=7.0)", "style": "info", "values": {"i0": 7.0}, "tip": "高速电机转速低，百公里电耗低，但爬坡力稍弱"},
            {"title": "⚖️ 黄金均衡速比 (i0=9.0)", "style": "success", "values": {"i0": 9.0}, "tip": "兼顾零百加速与高速巡航效率的黄金中庸点"},
            {"title": "🧗 强劲爬坡起步偏向 (i0=11.5)", "style": "warning", "values": {"i0": 11.5}, "tip": "起步轮端扭矩极大，但高速时电机早早触碰超速红线"},
        ],
        "defaults": {"i0": 9.0},
        "setters": "{'i0': slider_i0}",
    },
    "show_e2_explorer": {
        "title": "量产乘用车零百加速与电机 BOM 成本",
        "standard": "对标 乘用车动力总成采购选型成本库",
        "benchmarks": [
            ("普及型代步车", "8.0~10.5s (单电机小总成)", "info"),
            ("家用主流黄金段", "5.5~7.0s (最佳性价比)", "success"),
            ("性能跑车级", "< 4.0s (双电机高成本)", "danger"),
        ],
        "presets": [
            {"title": "🎯 膝点最优决策 (零百 5.5s, 黄金平衡)", "style": "success", "values": {"accel": 5.5}, "tip": "Pareto 前沿膝点，性能提升显著而成本边际增量平缓"},
            {"title": "⚡ 极致性能跑车 (零百 3.8s, 高额成本)", "style": "danger", "values": {"accel": 3.8}, "tip": "双大电机总成，成本暴增 85%"},
            {"title": "🛒 极致平价代步 (零百 7.5s, 最低成本)", "style": "", "values": {"accel": 7.5}, "tip": "单小功率电机，BOM 成本极低"},
        ],
        "defaults": {"accel": 5.5},
        "setters": "{'accel': slider_accel}",
    },
    "show_e3_explorer": {
        "title": "MPC 预测控制舒适性与跟踪约束",
        "standard": "对标 ISO 15622 & SAE 舒适度评级规范",
        "benchmarks": [
            ("跟驰安全时距", "0.8 ~ 1.8s", "info"),
            ("加加速度 Jerk 舒适域", "-2.5 ~ +2.5 m/s³", "success"),
            ("预测时域 Np * dt", "1.5 ~ 2.5s (前瞻规划)", "neutral"),
        ],
        "presets": [
            {"title": "🛋️ 舒适远距跟驰 (时距 1.8s)", "style": "success", "values": {"hw": 1.8}, "tip": "时距宽裕，加加速度被严格约束在舒适区间"},
            {"title": "⏱️ 紧凑高效跟驰 (时距 1.0s)", "style": "info", "values": {"hw": 1.0}, "tip": "兼顾车道通行率与跟驰安全，跟踪误差低"},
            {"title": "🏎️ 激进贴身跟驰 (时距 0.6s)", "style": "warning", "values": {"hw": 0.6}, "tip": "前车减速时 MPC 求解出临界大减速度"},
        ],
        "defaults": {"hw": 1.0},
        "setters": "{'hw': slider_hw}",
    },
    "show_e4_explorer": {
        "title": "动态规划 DP 全局最优与 SOC 自持约束",
        "standard": "对标 Bellman 最优性原理与离线全局理论下界",
        "benchmarks": [
            ("终值 SOC 偏差目标", "|ΔSOC| ≤ 0.01", "success"),
            ("DP 算力开销", "离线逆向遍历 (无法直接实车)", "warning"),
            ("ECMS 相比 DP 差距", "油耗偏离通常 < 3%", "info"),
        ],
        "presets": [
            {"title": "🎯 严格电量自持平衡 (权重 4.0, 精细网格)", "style": "success", "values": {"weight": 4.0, "grid": "精细网格 (50点，高精度求解)"}, "tip": "严厉惩罚 SOC 偏移，保证起止电量高度平衡"},
            {"title": "⚖️ 基准工程验证 (权重 2.0, 粗网格)", "style": "info", "values": {"weight": 2.0, "grid": "粗网格 (15点，秒解快速验证)"}, "tip": "秒级验证，平衡求解速度与状态回溯"},
            {"title": "🔴 纯电放水透支 (权重 1.0, 粗网格)", "style": "warning", "values": {"weight": 1.0, "grid": "粗网格 (15点，秒解快速验证)"}, "tip": "惩罚过低导致电池被深度透支，破坏自持"},
        ],
        "defaults": {"weight": 2.0, "grid": "粗网格 (15点，秒解快速验证)"},
        "setters": "{'weight': slider_weight, 'grid': drp_grid}",
    },
    "show_f1_explorer": {
        "title": "车规软硬件在环 HIL 联合仿真通信步长",
        "standard": "对标 FMI 2.0 / 3.0 Co-Simulation 规范",
        "benchmarks": [
            ("高精度动力学步长", "1 ~ 5 ms", "success"),
            ("控制总线推荐步长", "10 ~ 20 ms", "info"),
            ("数值发散临界步长", "> 30 ms (积分失稳)", "danger"),
        ],
        "presets": [
            {"title": "🟢 稳定收敛精细步长 (h=0.005s)", "style": "success", "values": {"step": 0.005}, "tip": "积分曲线光滑无抖动，能量守恒高"},
            {"title": "🟡 临界工程步长 (h=0.030s)", "style": "warning", "values": {"step": 0.030}, "tip": "计算速度快，但高频处出现轻微数值毛刺"},
            {"title": "🔴 步长过大发散爆炸 (h=0.080s)", "style": "danger", "values": {"step": 0.080}, "tip": "超出数值积分稳定域，状态量呈指数发散"},
        ],
        "defaults": {"step": 0.02},
        "setters": "{'step': slider_step}",
    },
    "show_f2_explorer": {
        "title": "底盘线控执行机构二阶阻尼比标定",
        "standard": "对标 SAE 汽车线控底盘动态响应性能规范",
        "benchmarks": [
            ("最佳工程阻尼比 ζ", "0.65 ~ 0.75 (超调<5%)", "success"),
            ("自然频率 ωn", "3.0 ~ 6.0 rad/s", "info"),
            ("欠阻尼振颤", "ζ < 0.3 (方向盘/踏板抖动)", "danger"),
        ],
        "presets": [
            {"title": "🎯 最佳工程临界阻尼 (wn=4.0, zeta=0.707)", "style": "success", "values": {"wn": 4.0, "zeta": 0.707}, "tip": "快速响应无超调，线控转向制动理想标定"},
            {"title": "⚡ 欠阻尼剧烈震颤 (wn=6.0, zeta=0.20)", "style": "danger", "values": {"wn": 6.0, "zeta": 0.20}, "tip": "执行机构剧烈超调振荡，导致车身顿挫摇晃"},
            {"title": "🐢 过阻尼迟缓迟钝 (wn=2.5, zeta=1.40)", "style": "", "values": {"wn": 2.5, "zeta": 1.40}, "tip": "无超调但上升时间长，紧急避障时滞严重"},
        ],
        "defaults": {"wn": 4.0, "zeta": 0.5},
        "setters": "{'wn': slider_wn, 'zeta': slider_zeta}",
    },
    "show_f3_explorer": {
        "title": "多物理场耦合能量守恒误差容限",
        "standard": "对标 IEEE 能量守恒多域协同仿真准则",
        "benchmarks": [
            ("微秒级电力电子", "0.1 ~ 1 ms", "info"),
            ("整车热/机电耦合", "5 ~ 10 ms", "success"),
            ("能量漂移上限", "< 1.0%", "warning"),
        ],
        "presets": [
            {"title": "🟢 高频串行精准协同 (dt=0.005s, Gauss-Seidel)", "style": "success", "values": {"dt": 0.005, "algo": "Gauss-Seidel 串行预测 (高精度收敛)"}, "tip": "串行预估消除代数环延迟，能量守恒度极高"},
            {"title": "⚖️ 标准总线并行协同 (dt=0.020s, Jacobi)", "style": "info", "values": {"dt": 0.020, "algo": "Jacobi 并行弱耦合 (易代数环漂移)"}, "tip": "并行计算速度快，但存在轻微虚假能量注入"},
            {"title": "🔴 低频失真严重泄漏 (dt=0.100s, Jacobi)", "style": "danger", "values": {"dt": 0.100, "algo": "Jacobi 并行弱耦合 (易代数环漂移)"}, "tip": "步长过大导致跨域协同严重失步，能量漂移超标"},
        ],
        "defaults": {"dt": 0.02, "algo": "Jacobi 并行弱耦合 (易代数环漂移)"},
        "setters": "{'dt': slider_dt, 'algo': drp_algo}",
    },
    "show_g1_explorer": {
        "title": "车载以太网 DDS 实时性与丢包容差",
        "standard": "对标 AUTOSAR Adaptive DDS & ISO 17387",
        "benchmarks": [
            ("自动驾驶硬实时上限", "时延 < 50 ms", "success"),
            ("智驾感知发布频率", "10 ~ 50 Hz", "info"),
            ("QoS 丢包耐受限度", "< 5% (依赖预测与重传)", "warning"),
        ],
        "presets": [
            {"title": "🟢 确定性车载以太网 (Freq=50Hz, Loss=0%)", "style": "success", "values": {"freq": 50, "loss": 0.0}, "tip": "端到端时延稳定在 15ms 内，满足最高硬实时要求"},
            {"title": "🟡 车联网弱网抖动 (Freq=20Hz, Loss=15%)", "style": "warning", "values": {"freq": 20, "loss": 15.0}, "tip": "丢包导致延迟阶跃跳跃，感知帧率断续"},
            {"title": "🚨 严重网络风暴雪崩 (Freq=90Hz, Loss=25%)", "style": "danger", "values": {"freq": 90, "loss": 25.0}, "tip": "带宽耗尽队列溢出，端到端延迟突破安全阈值"},
        ],
        "defaults": {"freq": 50, "loss": 5.0},
        "setters": "{'freq': slider_freq, 'loss': slider_loss}",
    },
    "show_g2_explorer": {
        "title": "ISO 26262 转向制动 FTTI 容错时间预算",
        "standard": "对标 ISO 26262-4 功能安全硬件与软件集成要求",
        "benchmarks": [
            ("ASIL-D 转向制动 FTTI", "≤ 100 ms", "danger"),
            ("服务快速失效 Fail-Silent", "Timeout ≤ 0.08s, 重试 1 次", "success"),
            ("重试过多次卡死", "总阻塞 > 500ms (失控风险)", "danger"),
        ],
        "presets": [
            {"title": "🛡️ 车规快速失效降级 (Timeout=0.08s, 重试 1 次)", "style": "success", "values": {"timeout": 0.08, "retries": 1}, "tip": "超时极短迅速转入备用降级控制器，保障 FTTI"},
            {"title": "🟡 宽容网络等待 (Timeout=0.30s, 重试 3 次)", "style": "warning", "values": {"timeout": 0.30, "retries": 3}, "tip": "重试累加阻塞近 1 秒，对高速底盘极为危险"},
            {"title": "🚨 极端阻塞卡死 (Timeout=0.55s, 重试 5 次)", "style": "danger", "values": {"timeout": 0.55, "retries": 5}, "tip": "主控制循环完全挂起，造成严重功能安全违规"},
        ],
        "defaults": {"timeout": 0.2, "retries": 2},
        "setters": "{'timeout': slider_timeout, 'retries': slider_retries}",
    },
    "show_h1_explorer": {
        "title": "Euro NCAP 目标车切入加塞试验工况",
        "standard": "对标 Euro NCAP 2023 C2C Cut-in Test Protocol",
        "benchmarks": [
            ("试验加塞初距 d0", "10 ~ 30 m", "info"),
            ("相对加塞速差 dv", "10 ~ 40 km/h", "warning"),
            ("致命碰撞高危红区", "d0 < 15m 且 dv > 30km/h", "danger"),
        ],
        "presets": [
            {"title": "🚨 致命极近加塞 (d0=12m, dv=45km/h)", "style": "danger", "values": {"d0": 12, "dv": 45}, "tip": "深红高危死区，超出机械制动物理极限"},
            {"title": "🎯 临界边缘测试 (d0=22m, dv=25km/h)", "style": "warning", "values": {"d0": 22, "dv": 25}, "tip": "处于黄绿过渡边界，刚好检验 AEB 灵敏度"},
            {"title": "🟢 安全宽裕变道 (d0=40m, dv=15km/h)", "style": "success", "values": {"d0": 40, "dv": 15}, "tip": "绿区安全工况，仅需轻踩制动平顺跟车"},
        ],
        "defaults": {"d0": 25, "dv": 30},
        "setters": "{'d0': slider_d0, 'dv': slider_dv}",
    },
    "show_h2_explorer": {
        "title": "智能网联汽车极端工况挖掘量规",
        "standard": "对标 ISO 21448 SOTIF 预期功能安全极限场景库",
        "benchmarks": [
            ("Corner Case 碰撞检出率", "目标 > 15%", "warning"),
            ("变异摄动范围 σ", "0.2 ~ 0.6", "info"),
            ("测试代际迭代轮数", "30 ~ 120 iters", "neutral"),
        ],
        "presets": [
            {"title": "🔥 高强度变异挖掘 (120 轮, Sigma=0.7)", "style": "danger", "values": {"iters": 120, "sigma": 0.7}, "tip": "大范围激进扰动，快速挖掘出极难复现的边缘死角"},
            {"title": "⚖️ 标准引导式搜索 (50 轮, Sigma=0.3)", "style": "info", "values": {"iters": 50, "sigma": 0.3}, "tip": "梯度平稳下降，高效锁定边界脆弱区"},
            {"title": "🔍 局部精细探测 (30 轮, Sigma=0.15)", "style": "success", "values": {"iters": 30, "sigma": 0.15}, "tip": "小步长局部微调，精确勘测安全边界分界线"},
        ],
        "defaults": {"iters": 50, "sigma": 0.3},
        "setters": "{'iters': slider_iters, 'sigma': slider_sigma}",
    },
    "show_capstone_explorer": {
        "title": "乘用车全域协同与制动能量回收量规",
        "standard": "对标 GB 21670 乘用车制动系统技术要求与试验方法",
        "benchmarks": [
            ("单踏板最大电回收力", "0.2 ~ 0.3g (约 2~3 m/s²)", "info"),
            ("综合节能潜力", "15% ~ 25% (视市区工况)", "success"),
            ("紧急制动防抱死优先", "ABS 激活时切除电回收", "danger"),
        ],
        "presets": [
            {"title": "🌱 极致节能大回收 (TTC=2.5s, Th=1.2s, Regen=0.80)", "style": "success", "values": {"ttc": 2.5, "headway": 1.2, "regen": 0.80}, "tip": "电制动回收拉满，市区综合电耗大幅降低"},
            {"title": "🛋️ 舒适巡航低回收 (TTC=3.0s, Th=2.0s, Regen=0.30)", "style": "info", "values": {"ttc": 3.0, "headway": 2.0, "regen": 0.30}, "tip": "时距充裕电回收柔和，乘坐无任何拖拽感"},
            {"title": "🚨 紧急避碰极限制动 (TTC=1.6s, Th=1.0s, Regen=0.50)", "style": "danger", "values": {"ttc": 1.6, "headway": 1.0, "regen": 0.50}, "tip": "追求极限刹停距离，液压机械制动全力介入"},
        ],
        "defaults": {"ttc": 2.2, "headway": 1.6, "regen": 0.50},
        "setters": "{'ttc': slider_ttc, 'headway': slider_headway, 'regen': slider_regen}",
    },
}

HELPER_CODE = '''

def _create_benchmark_badge(title: str, items: list, standard: str = ""):
    """创建行业工程量规与物理锚点标签条"""
    if not _HAS_WIDGETS:
        return None
    badge_colors = {
        "info": ("#e0f2fe", "#0369a1", "#38bdf8"),
        "success": ("#dcfce7", "#15803d", "#4ade80"),
        "warning": ("#fef3c7", "#92400e", "#facc15"),
        "danger": ("#fee2e2", "#991b1b", "#f87171"),
        "neutral": ("#f1f5f9", "#334155", "#cbd5e1"),
    }
    badges_html = []
    for label, val_range, ctype in items:
        bg, fg, border = badge_colors.get(ctype, badge_colors["neutral"])
        badges_html.append(
            f'<span style="background: {bg}; color: {fg}; border: 1px solid {border}; padding: 2px 7px; border-radius: 4px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px; font-weight: 500;">'
            f'<b>{label}</b>: {val_range}</span>'
        )
    std_html = f'<span style="color: #64748b; font-size: 11px; margin-left: auto;">({standard})</span>' if standard else ""
    html = f"""
    <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px; margin: 4px 0 8px 0; font-size: 12px; color: #475569; display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-family: system-ui, -apple-system, sans-serif;">
        <span style="font-weight: 600; color: #1e293b;">📐 {title}：</span>
        {' '.join(badges_html)}
        {std_html}
    </div>
    """
    return widgets.HTML(html)


def _create_preset_bar(presets: list, default_dict: dict, setter_dict: dict, apply_callback: callable):
    """创建教师一键案例快照对标与恢复默认按钮栏"""
    if not _HAS_WIDGETS:
        return None

    label = widgets.HTML("<span style='font-size: 12px; font-weight: 700; color: #334155; margin-right: 6px;'>🎯 典型工况快照:</span>")
    btn_list = [label]

    def _apply_values(v_dict):
        for k, v in v_dict.items():
            if k in setter_dict and hasattr(setter_dict[k], 'value'):
                setter_dict[k].value = v
        if apply_callback:
            apply_callback()

    for p in presets:
        raw_style = p.get("style", "")
        b_style = raw_style if raw_style in ("primary", "success", "info", "warning", "danger") else ""
        b = widgets.Button(
            description=p["title"],
            button_style=b_style,
            tooltip=p.get("tip", ""),
            layout=widgets.Layout(height="30px", margin="2px 4px", width="auto")
        )
        def _make_handler(vals):
            return lambda _: _apply_values(vals)
        b.on_click(_make_handler(p["values"]))
        btn_list.append(b)

    if default_dict:
        b_reset = widgets.Button(
            description="↺ 恢复默认",
            button_style="",
            tooltip="恢复出厂基准参数",
            layout=widgets.Layout(height="30px", margin="2px 4px 2px 10px", width="auto")
        )
        b_reset.on_click(lambda _: _apply_values(default_dict))
        btn_list.append(b_reset)

    return widgets.HBox(
        btn_list,
        layout=widgets.Layout(
            display='flex',
            flex_flow='row wrap',
            align_items='center',
            margin='4px 0 6px 0',
            width='100%'
        )
    )
'''

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    explorers_path = os.path.join(repo_root, "labs", "common", "lab_explorers.py")
    
    with open(explorers_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. 注入辅助函数 (若尚未注入)
    if "_create_preset_bar" not in content:
        # 寻找 _wrap_hbox 的结束位置
        wrap_pos = content.find("def _wrap_hbox(")
        if wrap_pos == -1:
            raise ValueError("_wrap_hbox not found!")
        # 找到 _wrap_hbox 函数末尾 (return widgets.HBox(...))
        end_return = content.find("    )\n\n", wrap_pos)
        insert_pos = end_return + 7
        content = content[:insert_pos] + HELPER_CODE + content[insert_pos:]
        print("✅ Injected HELPER_CODE into lab_explorers.py")

    # 2. 为每个函数注入快照栏与行业量规
    for fn_name, cfg in CONFIGS.items():
        fn_pattern = f"def {fn_name}():"
        fn_start = content.find(fn_pattern)
        if fn_start == -1:
            print(f"⚠️ Function {fn_name} not found!")
            continue

        # 找到下一个函数开头以限定范围
        next_fn_start = content.find("\ndef show_", fn_start + 10)
        fn_block = content[fn_start:next_fn_start] if next_fn_start != -1 else content[fn_start:]

        # 检查是否已经注入过
        if "benchmarks_widget = _create_benchmark_badge" in fn_block:
            print(f"ℹ️ {fn_name} already contains presets/benchmarks, skipping.")
            continue

        # 构建要插入的代码块
        bm_items_repr = repr(cfg["benchmarks"])
        presets_repr = repr(cfg["presets"])
        defaults_repr = repr(cfg["defaults"])
        setters_code = cfg["setters"]
        title_str = cfg["title"]
        standard_str = cfg["standard"]

        injection = f'''
    benchmarks_widget = _create_benchmark_badge("{title_str}", {bm_items_repr}, "{standard_str}")
    presets = {presets_repr}
    default_vals = {defaults_repr}
    setter_map = {setters_code}
    preset_bar = _create_preset_bar(presets, default_vals, setter_map, update_view)
'''

        # 寻找插入点：在 controls = widgets.VBox([ 前面插入 injection
        vbox_pos = fn_block.find("controls = widgets.VBox([")
        if vbox_pos == -1:
            print(f"⚠️ controls = widgets.VBox([ not found in {fn_name}!")
            continue

        # 修改 controls = widgets.VBox([ 为包含 preset_bar, benchmarks_widget,
        old_vbox_str = "controls = widgets.VBox(["
        new_vbox_str = "controls = widgets.VBox([\n        preset_bar,\n        benchmarks_widget,"
        
        fn_block_mod = fn_block[:vbox_pos] + injection + "\n    " + new_vbox_str + fn_block[vbox_pos + len(old_vbox_str):]

        if next_fn_start != -1:
            content = content[:fn_start] + fn_block_mod + content[next_fn_start:]
        else:
            content = content[:fn_start] + fn_block_mod

        print(f"✅ Enhanced {fn_name}")

    # 3. 校验 Python 语法
    try:
        ast.parse(content)
        print("🎉 AST parse verification passed! No syntax errors.")
    except SyntaxError as e:
        print(f"❌ Syntax error in modified content: {e}")
        return 1

    with open(explorers_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("💾 Successfully written updated lab_explorers.py!")
    return 0

if __name__ == "__main__":
    exit(main())
