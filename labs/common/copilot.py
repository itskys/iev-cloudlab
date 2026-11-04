"""IEV CloudLab 智能工程导师与启发式故障自愈 Copilot | Engineering Copilot

功能说明：
  针对学生在智能新能源汽车仿真与算法开发过程中遭遇的断言失败、指标未达标、
  物理失稳或工况崩溃，提供兼具严谨物理方程第一性原理推导与量产工程调优处方的智能诊断系统。

核心特性：
  1. 覆盖 A~H 八大领域 29 门实验 + Capstone 全域大作业的汽车工程机理故障树知识库 (Fault Tree Diagnostic Engine)；
  2. 根因量化归因 (Root Cause Attribution)：
     - 基于运动学、动力学、电化学与交通流第一性原理，深入剖析失效机理；
  3. 参数调优处方矩阵 (Tuning Prescription Matrix)：
     - 结构化提供受影响参数、当前取值、调节方向（增大/减小）、步进建议与量产经验区间；
  4. 对标主机厂工业标准规范 (OEM Benchmarks)：
     - 深度对标 Euro NCAP 2023, ISO 15622, SAE J1634, GB 38031, Webster 等标准规范；
  5. 多端无缝集成：
     - 与 evaluator.py 评分器联动，在学生评测不达标时自动附带结构化诊断；
     - 与 student_cockpit.py 学生驾驶舱联动，一键展示薄弱项调优处方；
     - 原生支持 Jupyter Notebook 高保真工控交互卡片与 CLI 终端文本摘要。
"""

import math
import os
from typing import Dict, Any, List, Optional, Tuple, Union


def _val(metrics: Dict[str, Any], *keys, default=None):
    """鲁棒获取指标值，支持多个键名别名与大小写容错"""
    if not metrics:
        return default
    for k in keys:
        if k in metrics and metrics[k] is not None:
            return metrics[k]
        k_lower = k.lower()
        for mk, mv in metrics.items():
            if mk.lower() == k_lower and mv is not None:
                return mv
    return default


# ==================== 29 门实验 + Capstone 全体系机理故障树知识库 ====================
DIAGNOSTIC_KNOWLEDGE_BASE = {
    # -------------------------------------------------- Track A: 智驾感知与极限规控
    'A1_cutin_aeb': {
        'name': 'Cut-in 加塞紧急避险',
        'rules': [
            {
                'condition': lambda m: _val(m, 'collision') is True or (_val(m, 'min_ttc_s', 'min_ttc', default=99) < 1.0),
                'severity': 'critical',
                'symptom': '车辆发生物理碰撞或最小安全时距触及极度危险区 (TTC < 1.0s)',
                'physics_root_cause': (
                    '在加塞切入初期，两车相对车速差 Δv = v_ego - v_lead 导致时距急剧收缩。根据运动学极限制动距离方程 '
                    's_stop = Δv² / (2 · |a_req|) + Δv · τ_delay。若 TTC 触发阈值设定过小，留给制动执行机构的距离 '
                    '小于物理停车安全制动距离，制动建压尚未达到峰值减速度即已追尾。'
                ),
                'tuning_matrix': [
                    {'param': 'ttc_threshold', 'current': lambda m: f"{_val(m, 'ttc_threshold', default='--')}s", 'action': '增大 ↑', 'step': '+0.3s', 'recommended': '2.2s ~ 2.6s'},
                    {'param': 'decel_req', 'current': lambda m: f"{_val(m, 'decel_req', default='--')} m/s²", 'action': '增强负向减速度 ↑', 'step': '-0.8 m/s²', 'recommended': '-5.5 ~ -6.5 m/s²'},
                ],
                'prescriptions': [
                    '适当调大 TTC 预警制动阈值（建议由默认的 1.5s 提升至 2.2s ~ 2.6s）；',
                    '检查制动减速度上限，确认紧急避碰段制动需求设定为 -5.5 ~ -6.5 m/s² 之间；',
                    '核实车辆反应时间常数与执行器建压时延是否在时步积分中被过度放大。'
                ],
                'oem_benchmark': '对标 Euro NCAP 2023 CCRs (Car-to-Car Rear Stationary) 标定规范：FCW 碰撞预警须于 TTC ≥ 2.7s 启动，AEB 全制动须于 TTC ≥ 1.8s 前介入以确保 0 碰撞。'
            },
            {
                'condition': lambda m: _val(m, 'min_ttc_s', 'min_ttc', default=0) > 3.5,
                'severity': 'info',
                'symptom': '避险触发过早，安全裕度过大（易引发后车追尾虚警与乘员不适）',
                'physics_root_cause': 'TTC 阈值设定过大导致系统虚警率升高，在目标车尚未跨越车道标线时便全力急刹，损害乘员舒适度并破坏后方交通流稳定。',
                'tuning_matrix': [
                    {'param': 'ttc_threshold', 'current': lambda m: f"{_val(m, 'ttc_threshold', default='--')}s", 'action': '减小 ↓', 'step': '-0.3s', 'recommended': '2.0s ~ 2.5s'},
                ],
                'prescriptions': [
                    '收紧 TTC 判定阈值至 2.0s ~ 2.5s 工业量产区间；',
                    '引入分级预警逻辑：初段采用轻度点刹 (-2.0 m/s²)，紧急段再全力制动。'
                ],
                'oem_benchmark': 'ISO 22839 前向虚警抑制规范：在邻道正常并线工况下，减速度超过 0.3g 的不必要制动发生率应 < 0.1%。'
            }
        ]
    },
    'A2_acc_follow': {
        'name': 'ACC 自适应巡航跟车',
        'rules': [
            {
                'condition': lambda m: _val(m, 'max_spacing_error_m', 'max_spacing_error', default=0) > 1.5,
                'severity': 'warning',
                'symptom': '最大跟车间距误差超过 1.5m 门限',
                'physics_root_cause': (
                    'ACC 控制器对前车车速变动的跟踪滞后。主要源于比例增益 Kp 过小导致响应迟缓，或积分时间常数过大未有效消除稳态静差。'
                    '车头时距常数 τ_headway 与传感器低通滤波延迟引起了控制回路相位滞后。'
                ),
                'tuning_matrix': [
                    {'param': 'kp_spacing', 'current': lambda m: '--', 'action': '增大 ↑', 'step': '+0.25', 'recommended': '0.8 ~ 1.2'},
                    {'param': 'kv_speed_ff', 'current': lambda m: '--', 'action': '引入前馈 ↑', 'step': '+0.30', 'recommended': '0.5 ~ 0.8'},
                ],
                'prescriptions': [
                    '适当提高车头时距误差增益 Kp（建议增大 20%~35%）；',
                    '引入前车相对速度前馈项 a_ff = Kv · (v_lead - v_ego)，显著提升动态变车速工况下的时距跟踪刚度。'
                ],
                'oem_benchmark': 'ISO 15622 (ACC 自适应巡航控制系统性能要求) 规定：稳态跟车间距误差容差必须收敛于 ±1.0m 以内。'
            }
        ]
    },
    'A3_aeb_closedloop': {
        'name': 'AEB 增强 TTC 闭环避险',
        'rules': [
            {
                'condition': lambda m: _val(m, 'collision') is True,
                'severity': 'critical',
                'symptom': '闭环动态制动失败，自车与目标车发生几何碰撞',
                'physics_root_cause': '闭环反馈控制律未能在前车制动减速度突变时形成足够的制动力建压斜率 (da/dt)，导致有效制动冲量不足。',
                'tuning_matrix': [
                    {'param': 'ttc_gain', 'current': lambda m: '--', 'action': '增大增益 ↑', 'step': '+0.5', 'recommended': '2.5 ~ 3.2'},
                ],
                'prescriptions': [
                    '提升闭环比例增益，缩短执行器制动压力建压死区时间；',
                    '确认闭环制动控制器中引入了前车减速度前馈观测器。'
                ],
                'oem_benchmark': 'GB/T 39901 乘用车自动紧急制动系统 (AEBS) 性能要求与试验方法。'
            },
            {
                'condition': lambda m: _val(m, 'false_trigger_rate', default=0) > 0.05,
                'severity': 'warning',
                'symptom': 'AEB 误触发率超标 (>5%)',
                'physics_root_cause': '横向切入重叠度 (Overlap) 判定门限过宽或滤波确认窗口过窄，导致相邻车道正常直行车辆被误当做切入危险目标。',
                'tuning_matrix': [
                    {'param': 'lateral_overlap_thresh', 'current': lambda m: '--', 'action': '收紧判定 ↑', 'step': '+10%', 'recommended': '35% ~ 50%'},
                ],
                'prescriptions': [
                    '提高横向重叠度门限，仅在目标车侵入本车道宽度 35% 以上时进入制动预警；',
                    '增加持续帧确认机制 (Debounce Filter)，防止雷达单帧航迹毛刺诱发刹车。'
                ],
                'oem_benchmark': 'Euro NCAP 误触发试验规范：相邻车道超车与弯道会车工况下误动作触发率必须为 0。'
            }
        ]
    },
    'A4_intersection_yield': {
        'name': '交叉口冲突让行',
        'rules': [
            {
                'condition': lambda m: _val(m, 'pet_s', default=99) < 1.0 or _val(m, 'collision') is True,
                'severity': 'critical',
                'symptom': '交叉口后侵入时间 PET < 1.0s 或发生路口冲突碰撞',
                'physics_root_cause': '冲突区域 (Conflict Zone) 预判时距未计入横向穿越车辆加速行为，导致两车通过冲突点的时空时间差 (Post-Encroachment Time) 侵入极限死区。',
                'tuning_matrix': [
                    {'param': 'yield_distance_thresh', 'current': lambda m: '--', 'action': '提前让行 ↑', 'step': '+5m', 'recommended': '25m ~ 35m'},
                ],
                'prescriptions': [
                    '扩大交叉口通行冲突检测包络盒，提前启动减速滑行让行；',
                    '在让行速度规划中，将目标 PET 安全裕量设为 2.0s 以上。'
                ],
                'oem_benchmark': '交通安全公认准则：交叉口车辆冲突 PET < 1.0s 即被认定为严重交通近碎碰撞冲突 (Traffic Conflict Technique)。'
            }
        ]
    },
    'A5_merge_kinematic_demo': {
        'name': '汇流运动学演示',
        'rules': [
            {
                'condition': lambda m: _val(m, 'completed') is False,
                'severity': 'warning',
                'symptom': '汇流运动学仿真演示未完整完成',
                'physics_root_cause': '主线可插车间隙 (Acceptable Gap) 估计过紧，或变道横向加加速度 (Lateral Jerk) 超出车辆动力学物理包线约束。',
                'tuning_matrix': [
                    {'param': 'min_gap_accept', 'current': lambda m: '--', 'action': '放宽间距 ↑', 'step': '+3m', 'recommended': '15m ~ 20m'},
                ],
                'prescriptions': [
                    '核查合流加速车道末端速度匹配逻辑，确保汇入车速与主车流速度差在 ±5km/h 以内。'
                ],
                'oem_benchmark': '高速公路匝道合流设计规范 (AASHTO / JTG D20)。'
            }
        ]
    },

    # -------------------------------------------------- Track B: 车联网车路协同与交通流
    'B1_idm_calibration': {
        'name': 'IDM 智能跟驰模型参数标定',
        'rules': [
            {
                'condition': lambda m: _val(m, 'rmse', default=0) > 0.6,
                'severity': 'warning',
                'symptom': '标定 RMSE 超过 0.60 拟合阈值 (实测对标基准 0.405)',
                'physics_root_cause': '非线性最小二乘优化算法陷入局部极小值，或待标定参数搜索边界（Bounds）与初值设置偏离实际物理常识。',
                'tuning_matrix': [
                    {'param': 'T_headway', 'current': lambda m: '--', 'action': '校正初值', 'step': '1.5s', 'recommended': '1.0s ~ 1.8s'},
                    {'param': 'a_max', 'current': lambda m: '--', 'action': '校正初值', 'step': '1.5 m/s²', 'recommended': '1.2 ~ 2.0 m/s²'},
                ],
                'prescriptions': [
                    '检查待标定参数初值：建议初值设为 v0=30m/s, T=1.5s, s0=2.0m, a=1.5m/s², b=2.0m/s²；',
                    '采用两阶段标定：先固定静止安全距离 s0 和期望车速 v0，再使用 SciPy curve_fit 集中拟合加速度 a 与车头时距 T。'
                ],
                'oem_benchmark': '微观交通仿真标定规范（Treiber & Kesting, 2013）：真实道路浮动车跟驰标定实测 RMSE 通常应处于 0.35 ~ 0.50 范围。'
            }
        ]
    },
    'B2_traffic_signal': {
        'name': '交叉口信号配时优化',
        'rules': [
            {
                'condition': lambda m: _val(m, 'delay_reduction_pct', default=0) < 50.0,
                'severity': 'warning',
                'symptom': '车均延误降低率未达到 50% 优化要求 (实测对标基准 72.8%)',
                'physics_root_cause': '红绿灯周期 C 或绿信比未能匹配东西向与南北向非对称交通流量比 (y_ew / y_ns)，导致次要方向空放而主要方向严重排队溢出。',
                'tuning_matrix': [
                    {'param': 'cycle_length_C', 'current': lambda m: '--', 'action': '依 Webster 迭代', 'step': 'C0 公式', 'recommended': '45s ~ 75s'},
                ],
                'prescriptions': [
                    '严格采用 Webster 理论最佳周期公式 C0 = (1.5L + 5) / (1 - Y)，其中总损失时间 L=8s；',
                    '按各关键相位流量比严格切分有效绿灯时长：g_i = (y_i / Y) · (C - L)。'
                ],
                'oem_benchmark': 'HCM (Highway Capacity Manual) 信号交叉口服务水平评定标准：最优配时应使主干线车均延误由 LOS-E 提升至 LOS-B (<20s/veh)。'
            }
        ]
    },
    'B3_sumo_cacc': {
        'name': 'CACC 编队控制与弦稳定性',
        'rules': [
            {
                'condition': lambda m: _val(m, 'max_spacing_error', 'max_spacing_error_m', default=0) > 2.0,
                'severity': 'critical',
                'symptom': 'CACC 编队间距误差超标 (>2.0m)，车队发生弦不稳定振荡',
                'physics_root_cause': (
                    'V2X 车车通信延时与丢包导致领航车加速度前馈信息失步。控制器闭环传递函数幅值上界 ‖H(jω)‖_∞ > 1.0，'
                    '导致前方车辆的轻微加减速扰动沿着车队队列向上游逐车放大，极易诱发第 4~5 辆车的幽灵堵车乃至连环追尾。'
                ),
                'tuning_matrix': [
                    {'param': 'ka_feedforward', 'current': lambda m: '--', 'action': '适度下调前馈 ↓', 'step': '-0.15', 'recommended': '0.55 ~ 0.75'},
                    {'param': 'kv_damping', 'current': lambda m: '--', 'action': '增加速度阻尼 ↑', 'step': '+0.25', 'recommended': '0.80 ~ 1.20'},
                ],
                'prescriptions': [
                    '严格校核弦稳定性频域判据：保证在全部频段 |E_i(jω) / E_{i-1}(jω)| ≤ 1.0；',
                    '在 CACC 控制律中加入时延补偿预测器（Smith Predictor 或卡尔曼滤波前推）。'
                ],
                'oem_benchmark': 'SAE J3161/1 联网车队协同自适应巡航 (CACC) 弦稳定性测试规范。'
            },
            {
                'condition': lambda m: _val(m, 'steps', default=0) < 300,
                'severity': 'warning',
                'symptom': '仿真步数不足 300 步 (实测不充分)',
                'physics_root_cause': '编队仿真运行时间过短，未经历减速波向下游完全传递并恢复稳态的完整周期。',
                'prescriptions': [
                    '延长仿真运行时长至 400 步以上，以完整观测第 5 辆尾车的动态恢复过程。'
                ],
                'oem_benchmark': 'SUMO 协同编队验证规范。'
            }
        ]
    },
    'B4_congestion_wave': {
        'name': '交通拥堵激波传播',
        'rules': [
            {
                'condition': lambda m: _val(m, 'wave_speed_kmh', default=1) >= 0.0,
                'severity': 'critical',
                'symptom': '拥堵激波波速方向非负 (违背交通流冲击波向上游传播定律)',
                'physics_root_cause': (
                    '依据 LWR (Lighthill-Whitham-Richards) 宏观交通流守恒定律，激波速度公式为 w = (q2 - q1) / (k2 - k1)。'
                    '在排队积压工况下，下游密度剧增 (k2 > k1) 且通行能力受抑 (q2 < q1)，冲击波波速 w 物理上必须严格为负，'
                    '表示排队波头正在向道路上游反向倒灌。'
                ),
                'tuning_matrix': [
                    {'param': 'density_gradient', 'current': lambda m: '--', 'action': '检查密度断点', 'step': 'k_jam - k_crit', 'recommended': '波速范围 -15 ~ -2 km/h'},
                ],
                'prescriptions': [
                    '核对时空图 (Time-Space Diagram) 中的排队起点检测逻辑，确保取拥堵界面的斜率；',
                    '确认流量 q 与密度 k 的统计断面时间窗口未倒置。'
                ],
                'oem_benchmark': '交通波理论与道路通行能力手册 (LWR Kinematic Wave Theory)。'
            },
            {
                'condition': lambda m: _val(m, 'r_squared', default=0) < 0.5,
                'severity': 'warning',
                'symptom': '激波传播轨迹拟合 R² 优度低于 0.5 (实测基准 0.663)',
                'physics_root_cause': '微观随机扰动过大或排队波头识别算法存在时空噪点。',
                'prescriptions': [
                    '在激波前锋提取前对浮动车速度矩阵应用低通高斯滤波，过滤车辆偶发换道尖刺。'
                ],
                'oem_benchmark': '交通时空轨迹数据平滑处理标准。'
            }
        ]
    },
    'B5_green_wave': {
        'name': '干线连续绿波带协调',
        'rules': [
            {
                'condition': lambda m: _val(m, 'stops_reduction_pct', default=0) < 50.0,
                'severity': 'warning',
                'symptom': '干线停车次数减少幅度低于 50% (实测对标基准 76.5%)',
                'physics_root_cause': '相邻交叉口之间的相位差 Offset 与设计协调车速不匹配，绿波带宽度过窄被上游慢车或路段红灯阻截。',
                'tuning_matrix': [
                    {'param': 'offset_delta', 'current': lambda m: '--', 'action': '按车速重算', 'step': 'Δt = Distance / V', 'recommended': '协调速度 45 ~ 55 km/h'},
                ],
                'prescriptions': [
                    '计算理论相位差：Offset_i = (D_i / V_green) mod Cycle，其中协调车速建议设为 50km/h；',
                    '保证绿信比 λ ≥ 0.5，以留出至少 15s 以上的连续绿波通行带宽 (Bandwidth)。'
                ],
                'oem_benchmark': '《城市道路交通信号控制系统设计规范》(GB/T 50647)。'
            }
        ]
    },

    # -------------------------------------------------- Track C: 整车动力学与能耗流
    'C1_fastsim_energy': {
        'name': '整车百公里动力学电耗',
        'rules': [
            {
                'condition': lambda m: _val(m, 'energy_kwh_100km', default=0) > 20.0,
                'severity': 'warning',
                'symptom': '百公里电耗偏高 (>20.0 kWh/100km，实测基准 12.5)',
                'physics_root_cause': (
                    '整车行驶阻力方程 F_total = mg·f_r + 0.5·ρ·Cd·A·v² + mg·sinθ + m·a。'
                    '电耗严重超标通常由三方面引起：①整车整备质量严重偏大；②迎风面积风阻 Cd*A 过高；'
                    '③未启用电机再生制动 (Regen)，频繁刹车减速动能全部被机械摩擦夹钳转化为无效热量损耗。'
                ),
                'tuning_matrix': [
                    {'param': 'drag_coeff_cd', 'current': lambda m: f"{_val(m, 'cd', default='--')}", 'action': '降低风阻 ↓', 'step': '-0.03', 'recommended': '0.22 ~ 0.28'},
                    {'param': 'curb_mass_kg', 'current': lambda m: f"{_val(m, 'mass', default='--')}kg", 'action': '整车轻量化 ↓', 'step': '-150kg', 'recommended': '1500 ~ 1800 kg'},
                ],
                'prescriptions': [
                    '确认 FASTSim 中电机再生制动开关 `has_regen = True`，并设置合理的制动能量回充效率 (75%~85%)；',
                    '检查输入车型参数库，纯电中型轿跑风阻系数 Cd 推荐设定在 0.22 ~ 0.28 之间。'
                ],
                'oem_benchmark': '工信部/WLTC 纯电动乘用车典型能耗指标：紧凑型~中型纯电轿车正常工况能耗区间为 11.5 ~ 14.5 kWh/100km。'
            },
            {
                'condition': lambda m: _val(m, 'energy_kwh_100km', default=99) < 10.0,
                'severity': 'warning',
                'symptom': '百公里电耗非物理偏低 (<10.0 kWh/100km，违背能量守恒公理)',
                'physics_root_cause': '仿真模型忽略了轮胎滚动阻力做功 (f_r 设为 0)，或电驱逆变器与电机效率被理想化设为 100%。',
                'tuning_matrix': [
                    {'param': 'rolling_res_fr', 'current': lambda m: '--', 'action': '补充真实滚阻 ↑', 'step': '+0.008', 'recommended': '0.008 ~ 0.012'},
                ],
                'prescriptions': [
                    '在动力学平衡方程中计入轮胎滚阻系数 f_r = 0.009；',
                    '电机平均驱动效率映射表综合效率应限定在 88% ~ 94% 工程可达上限。'
                ],
                'oem_benchmark': 'SAE J1634 纯电动汽车能耗测试规程。'
            }
        ]
    },
    'C2_vehicle_comparison': {
        'name': '不同车型谱系横向能耗对比',
        'rules': [
            {
                'condition': lambda m: _val(m, 'n_vehicles', default=0) < 5,
                'severity': 'warning',
                'symptom': '对比车型数量不足 5 款 (实测对标基准 6 款)',
                'physics_root_cause': '未完整加载车型库中的轿跑、SUV、MPV 及越野车型，无法构建跨车身形态的风阻与质量能耗谱系。',
                'prescriptions': [
                    '调用 `fastsim_helper.load_bev_list()` 遍历加载完整的 6 款基准车型。'
                ],
                'oem_benchmark': '中国汽车工程学会 (CSAE) 乘用车空气动力学对标数据库。'
            }
        ]
    },
    'C3_sensitivity_analysis': {
        'name': '质量与风阻无量纲灵敏度分析',
        'rules': [
            {
                'condition': lambda m: _val(m, 's_mass', default=0) <= 0.0 or _val(m, 's_cd', default=0) <= 0.0,
                'severity': 'warning',
                'symptom': '质量或风阻灵敏度系数未成功计算或符号异常反转',
                'physics_root_cause': (
                    '弹性灵敏度定义为 S_x = (ΔE / E0) / (Δx / x0)。质量与风阻均为正向阻力消耗源，其对电耗的偏导数必然严格为正。'
                    '出现非正数通常是由于差分步长取值过大或分母基准电耗归一化失误。'
                ),
                'tuning_matrix': [
                    {'param': 'perturb_step', 'current': lambda m: '--', 'action': '微小有限差分', 'step': '±10%', 'recommended': '+10% 扰动'},
                ],
                'prescriptions': [
                    '采用单侧有限差分：S = (E_perturbed - E_baseline) / E_baseline / 0.10；',
                    '牢记核心工程因果：低速市区工况质量主导 (S_m ≈ 0.61)，高速工况风阻逆转主导 (S_cd ≈ 0.58)。'
                ],
                'oem_benchmark': '《汽车理论》（余志生）：汽车功率平衡图与速度三次方能耗敏感度演化规律。'
            }
        ]
    },
    'C4_ems_comparison': {
        'name': '混动能量管理策略对比',
        'rules': [
            {
                'condition': lambda m: _val(m, 'n_strategies', default=0) < 3,
                'severity': 'warning',
                'symptom': '对比策略不足 3 种 (要求覆盖 CD/CS 规则基与 ECMS 等效能耗最小化)',
                'physics_root_cause': '未完整仿真 CD (Charge Depleting)、CS (Charge Sustaining) 与 ECMS 策略，无法展示瞬态等效伴随状态变量 s 的自适应节油机制。',
                'prescriptions': [
                    '在 EMS 求解脚本中同时运行纯电优先 CD、电量维持 CS 及全局动态搜索 ECMS。'
                ],
                'oem_benchmark': 'IEEE Transactions on Vehicular Technology: 混动动力总成等效油耗最小化策略 (ECMS) 理论对标。'
            }
        ]
    },

    # -------------------------------------------------- Track D: 动力电池与微观电化学
    'D1_pybamm_battery': {
        'name': '电芯恒流放电电化学仿真',
        'rules': [
            {
                'condition': lambda m: _val(m, 'capacity_ah', default=0) < 4.6 or _val(m, 'capacity_ah', default=0) > 5.1,
                'severity': 'warning',
                'symptom': '1C 容量偏离 4.85Ah 标称区间 (实测基准 4.96Ah)',
                'physics_root_cause': 'PyBaMM 单粒子模型 (SPM) 中正负极初始嵌锂化学计量比 (x_100, x_0, y_100, y_0) 或活性物质涂布厚度未校准，导致可用锂离子总摩尔量发生偏差。',
                'tuning_matrix': [
                    {'param': 'electrode_thickness', 'current': lambda m: '--', 'action': '校准几何尺寸', 'step': '75 μm', 'recommended': '70 ~ 85 μm'},
                ],
                'prescriptions': [
                    '采用 Chen 2020 经典高能量密度三元锂电芯参数集 (Chen2020 parameter set)；',
                    '检查放电截止电压，确认截止下限设定为 2.5V。'
                ],
                'oem_benchmark': 'GB/T 31486 电动汽车用动力蓄电池电性能要求及试验方法。'
            }
        ]
    },
    'D2_rate_capacity': {
        'name': '电池大倍率容量衰减特性',
        'rules': [
            {
                'condition': lambda m: _val(m, 'peukert_k', default=0) < 1.0 or _val(m, 'peukert_k', default=0) > 1.15,
                'severity': 'warning',
                'symptom': 'Peukert 指数偏离 1.0 ~ 1.15 理化常模 (实测基准 1.0511)',
                'physics_root_cause': (
                    'Peukert 方程 I^k · t = C 表征了大倍率极化导致的有效容量缩水。'
                    'k < 1.0 违反浓差极化随电流增大而加剧的热力学规律；k > 1.15 则说明模型中欧姆内阻或固相传质阻抗被非物理虚高。'
                ),
                'prescriptions': [
                    '在 0.5C、1C、2C、3C 四组放电电量上取对数进行线性拟合：ln(t) = ln(C) - k·ln(I)；',
                    '检查固相扩散系数 D_s 与电解液电导率是否随温升正常修正。'
                ],
                'oem_benchmark': '经典电化学储能 Peukert 容量效应物理模型。'
            }
        ]
    },
    'D3_ocv_soc_export': {
        'name': '电池 OCV-SOC 准静态标定',
        'rules': [
            {
                'condition': lambda m: _val(m, 'calibration_error_pct', default=0) > 5.0,
                'severity': 'warning',
                'symptom': '最大标定误差超标 (>5.0%)',
                'physics_root_cause': (
                    '在极低 SOC (<15%) 或极高 SOC (>85%) 区间，电池固相扩散与电荷转移极化超电势急剧发散，'
                    '导致放电端电压严重偏离热力学平衡开路电压。分段插值拟合出现龙格震荡。'
                ),
                'tuning_matrix': [
                    {'param': 'current_rate', 'current': lambda m: '--', 'action': '降低测试倍率 ↓', 'step': 'C/20 → C/50', 'recommended': 'C/50 准静态放电'},
                ],
                'prescriptions': [
                    '改用更低放电倍率作为参比基准（如 C/50 准静态放电）；',
                    '在 SOC 网格插值拟合时，对非线性极化区采用单调 PCHIP 插值或局部高斯平滑。'
                ],
                'oem_benchmark': 'BMS 电池管理系统状态估计工程规范：开路电压 OCV 查表误差必须抑制在 15mV 以内以确保 SOC 精度 ≤3%。'
            }
        ]
    },
    'D4_lithium_plating': {
        'name': '极端快充负极界面枝晶析锂',
        'rules': [
            {
                'condition': lambda m: _val(m, 'min_potential_3c_v', default=0) >= 0.0,
                'severity': 'warning',
                'symptom': '3C 极端大倍率快充未能复现析锂过电位跌破 0V 红线 (实测基准 -0.64V)',
                'physics_root_cause': '本实验旨在暴露大倍率充电时由于固相嵌锂饱和与液相扩散传质受限导致的负极电位击穿 0V 失效边界，未跌穿说明未施加大倍率或未在低温恶劣工况下考核。',
                'tuning_matrix': [
                    {'param': 'charge_rate', 'current': lambda m: f"{_val(m, 'c_rate', default='--')}C", 'action': '施加大倍率 ↑', 'step': '+0.5C', 'recommended': '2.5C ~ 3.5C'},
                    {'param': 'temperature', 'current': lambda m: f"{_val(m, 'temp_c', default='--')}°C", 'action': '低温考核 ↓', 'step': '-10°C', 'recommended': '-10°C ~ 10°C'},
                ],
                'prescriptions': [
                    '将快充倍率调至 3.0C，或降低环境温度至 0°C / -10°C 模拟极寒未预热快充；',
                    '密切观察隔膜界面处负极局部电位 Φ_s - Φ_e 的跌落轨迹。'
                ],
                'oem_benchmark': '宁德时代超充安全边界规范 & GB 38031：全生命周期严禁负极界面过电位跌破 0V vs Li/Li+ 以杜绝金属锂枝晶短路。'
            }
        ]
    },

    # -------------------------------------------------- Track E: 运筹优化与最优控制
    'E1_single_objective': {
        'name': '单目标参数优化',
        'rules': [
            {
                'condition': lambda m: _val(m, 'saving_pct', default=0) <= 0.0,
                'severity': 'warning',
                'symptom': '优化算法后未实现有效节油 (实测对标基准 4.23%)',
                'physics_root_cause': '优化算法搜索步长过大越过局部极值，或发动机最优工作线 (OOL) 目标函数权重矩阵配置有误。',
                'prescriptions': [
                    '调低 SciPy minimize 求解收敛容差 tol=1e-5，并采用有约束 SLSQP 优化器。'
                ],
                'oem_benchmark': '整车燃油经济性单目标凸优化标定准则。'
            }
        ]
    },
    'E2_pymoo_multiobj': {
        'name': '多目标优化 Pareto 前沿求解',
        'rules': [
            {
                'condition': lambda m: _val(m, 'n_pareto', default=0) < 50,
                'severity': 'warning',
                'symptom': 'Pareto 最优前沿解数量不足 50 个 (实测基准 60 个)',
                'physics_root_cause': 'NSGA-II 遗传算法种群规模过小或迭代代数过少，导致解集在燃油经济性与动力性双目标之间分布过于稀疏。',
                'tuning_matrix': [
                    {'param': 'pop_size', 'current': lambda m: '--', 'action': '扩大种群 ↑', 'step': '+30', 'recommended': '80 ~ 100'},
                    {'param': 'n_gen', 'current': lambda m: '--', 'action': '增加代数 ↑', 'step': '+20', 'recommended': '50 ~ 80'},
                ],
                'prescriptions': [
                    '将种群规模 pop_size 设置为 80 以上，代数设置为 60 代；',
                    '增大模拟二进制交叉算子 (SBX) 的分布指数，增强前沿多样性。'
                ],
                'oem_benchmark': '多目标进化计算在汽车动力总成匹配中的工程规范。'
            }
        ]
    },
    'E3_mpc_follow': {
        'name': 'CasADi MPC 非线性跟车控制',
        'rules': [
            {
                'condition': lambda m: _val(m, 'avg_solve_ms', default=0) > 50.0,
                'severity': 'critical',
                'symptom': 'MPC 平均单步求解时间超过 50ms 实时看门狗 (实测基准 11.5ms)',
                'physics_root_cause': (
                    '预测时域步长 N 过大或状态/控制约束采用硬边界惩罚，导致 IPOPT 内点法 Hessian 矩阵求逆迭代步数激增，'
                    '无法满足车载域控制器 20ms~50ms 的实时控制周期要求，极易导致控制周期溢出。'
                ),
                'tuning_matrix': [
                    {'param': 'prediction_horizon_N', 'current': lambda m: '--', 'action': '缩短时域 ↓', 'step': '-5', 'recommended': '10 ~ 15 步'},
                ],
                'prescriptions': [
                    '缩短预测时域 N 至 10~15 步（时距覆盖 1.0s~1.5s 足够保证闭环稳定性）；',
                    '将硬约束松弛为罚函数软约束，启用 IPOPT 的 warm-start 热启动技术。'
                ],
                'oem_benchmark': 'ISO 26262 ASIL-D 级电控单元硬实时调度时限：主控制循环执行时间必须严格 ≤ 50ms。'
            }
        ]
    },
    'E4_dp_ems': {
        'name': '动态规划 (DP) 全局能量管理',
        'rules': [
            {
                'condition': lambda m: _val(m, 'fuel_l_100km', default=99) > 2.2,
                'severity': 'warning',
                'symptom': 'DP 最优油耗未击穿 2.2 L/100km 极限 (实测基准 1.92 L/100km)',
                'physics_root_cause': '状态离散网格（SOC grid 与工况时步）划分过粗，导致插值重采样过程产生非物理数值耗散，或者终端 SOC 惩罚项权重不足导致电池出现虚假电量透支。',
                'tuning_matrix': [
                    {'param': 'n_soc_grid', 'current': lambda m: '--', 'action': '增密网格 ↑', 'step': '+50', 'recommended': '150 ~ 250 点'},
                    {'param': 'soc_terminal_weight', 'current': lambda m: '--', 'action': '强化端点约束 ↑', 'step': '×2.0', 'recommended': '严控电量等容'},
                ],
                'prescriptions': [
                    '将 SOC 离散网格分辨率由 100 增细至 200 点以上；',
                    '提高终端 SOC 边界惩罚系数：Cost_terminal = α · (SOC_end - SOC_target)²，确保等容电平衡。'
                ],
                'oem_benchmark': '混合动力汽车动态规划理论最低油耗基准线（Bellman 最优性原理）。'
            }
        ]
    },

    # -------------------------------------------------- Track F: FMI 联合仿真
    'F1_fmu_load': {
        'name': 'FMU 模型加载与概念验证',
        'rules': [
            {
                'condition': lambda m: _val(m, 'fmu_loaded') is False,
                'severity': 'critical',
                'symptom': 'FMU 共享库或接口规范加载失败',
                'physics_root_cause': 'FMI 跨平台二进制接口（Linux x86_64 so 动态库）与主机运行环境架构失配或环境变量缺失。',
                'prescriptions': [
                    '核对 pyfmi 与 fmpy 依赖，确认 FMU 为 64 位 Linux 兼容格式。'
                ],
                'oem_benchmark': 'FMI 2.0 / 3.0 Model Exchange & Co-Simulation 标准。'
            }
        ]
    },
    'F2_openmodelica_fmu': {
        'name': 'OpenModelica 手建 FMU 精度校验',
        'rules': [
            {
                'condition': lambda m: _val(m, 'max_error', default=1) > 1e-6,
                'severity': 'critical',
                'symptom': 'FMU 求解结果与物理微积分方程解析解误差超标 (>1e-6)',
                'physics_root_cause': '积分器步长设定过大或 Modelica 连续时间状态方程中引入了不恰当的高阶截断误差。',
                'prescriptions': [
                    '采用定步长四阶 Runge-Kutta (RK4) 或自适应步长 CVODE 积分器。'
                ],
                'oem_benchmark': '机电系统多领域物理建模精度认证标准。'
            }
        ]
    },
    'F3_multi_fmu': {
        'name': '多 FMU 联合仿真协同',
        'rules': [
            {
                'condition': lambda m: _val(m, 'v_err_pct', default=0) > 1.0 or _val(m, 'x_err_pct', default=0) > 2.0,
                'severity': 'warning',
                'symptom': '多 FMU 协仿真速度或位移耦合误差超标',
                'physics_root_cause': '主控器协同通信步长 (Communication Step Size) 大于子系统物理特征时间尺度，在接口变量传递时形成了数值代数环与相位迟滞。',
                'tuning_matrix': [
                    {'param': 'macro_step_h', 'current': lambda m: '--', 'action': '缩减通信步长 ↓', 'step': 'h/2', 'recommended': '0.001s ~ 0.005s'},
                ],
                'prescriptions': [
                    '缩减各 FMU 间的数据交换通信宏步长 h；',
                    '采用预测-校正高阶外插算法传递接口状态量。'
                ],
                'oem_benchmark': '跨域联合仿真协同协议标准。'
            }
        ]
    },

    # -------------------------------------------------- Track G: ROS 通信中间件
    'G1_ros_topics': {
        'name': 'ROS 2 话题实时通信',
        'rules': [
            {
                'condition': lambda m: _val(m, 'messages_received', default=0) < 1,
                'severity': 'critical',
                'symptom': 'ROS 2 订阅者未收到任何发布消息 (通信断流)',
                'physics_root_cause': '话题命名空间不匹配、DDS 域 (Domain ID) 隔离或 QoS 策略 (Reliability/Durability) 不兼容导致无法握手。',
                'prescriptions': [
                    '确保发布端与订阅端使用相同的 QoS Profile (如 `ReliabilityPolicy.RELIABLE`)；',
                    '检查 ROS_DOMAIN_ID 是否一致。'
                ],
                'oem_benchmark': 'AUTOSAR Adaptive 与 ROS 2 车载中间件通信规范。'
            }
        ]
    },
    'G2_ros_services': {
        'name': 'ROS 2 服务请求响应',
        'rules': [
            {
                'condition': lambda m: _val(m, 'service_ok') is False,
                'severity': 'critical',
                'symptom': 'ROS 2 服务端调用超时或返回失败',
                'physics_root_cause': '服务端回调处理耗时过长阻塞了主执行器线程，或客户端在服务启动就绪前便发起阻塞等待。',
                'prescriptions': [
                    '在调用 call_async 前调用 `client.wait_for_service(timeout_sec=5.0)`；',
                    '使用多线程执行器 (MultiThreadedExecutor) 处理并发服务请求。'
                ],
                'oem_benchmark': '车控操作系统客户端/服务端通信超时重试机制。'
            }
        ]
    },

    # -------------------------------------------------- Track H: 场景工程与预期功能安全
    'H1_batch_generation': {
        'name': 'OpenSCENARIO 场景批量生成',
        'rules': [
            {
                'condition': lambda m: _val(m, 'n_scenarios', default=0) < 9,
                'severity': 'warning',
                'symptom': '生成的有效测试用例数量少于 9 个',
                'physics_root_cause': '加塞车速与横向切入时距离散网格点数不足，无法形成覆盖临界安全边界的参数空间。',
                'prescriptions': [
                    '设置 3×3 交叉网格：切入车速取 [10, 15, 20] m/s，初始时距取 [1.5, 2.5, 3.5] s。'
                ],
                'oem_benchmark': 'ISO 21448 (SOTIF) 预期功能安全场景参数空间覆盖率要求。'
            },
            {
                'condition': lambda m: _val(m, 'monotonic') is False,
                'severity': 'critical',
                'symptom': '加塞危险度对 TTC 的物理单调性被破坏',
                'physics_root_cause': '场景生成脚本在排列相对车速与切入距离时存在索引错位。',
                'prescriptions': [
                    '核对切入相对车速差 Δv 增大时，TTC 必须单调递减。'
                ],
                'oem_benchmark': '智能驾驶虚拟仿真测试场景置信度规范。'
            }
        ]
    },
    'H2_scenario_fuzzing': {
        'name': '加塞场景模糊测试与失效边界探查',
        'rules': [
            {
                'condition': lambda m: _val(m, 'pass_rate', default=0.5) < 0.10 or _val(m, 'pass_rate', default=0.5) > 0.95,
                'severity': 'warning',
                'symptom': '模糊测试通过率未落在 10%~95% 的临界边界探查区间 (实测对标基准 31.58%)',
                'physics_root_cause': (
                    '若通过率 > 95%，说明扰动参数空间过于保守，未探查到被测算法的失效临界边界 (ODD 边缘工况)；'
                    '若通过率 < 10%，说明扰动过大直接产生非物理的“开局即撞”无效测试用例。'
                ),
                'tuning_matrix': [
                    {'param': 'fuzz_perturbation_range', 'current': lambda m: '--', 'action': '收缩/扩展扰动范围', 'step': '±15%', 'recommended': '切入距离 15~40m, 相对车速差 2~8m/s'},
                ],
                'prescriptions': [
                    '校准蒙特卡洛随机采样分布，切入车头时距建议使用均值 2.0s、方差 0.5s 的截断正态分布。'
                ],
                'oem_benchmark': 'ISO 34502 基于场景的自动驾驶安全评估体系。'
            }
        ]
    },

    # -------------------------------------------------- Capstone: 全域协同集成
    'Capstone_iev_integrated': {
        'name': '全域协同整车大作业集成',
        'rules': [
            {
                'condition': lambda m: _val(m, 'collision') is True or (_val(m, 'min_ttc_s', 'min_ttc', default=99) < 1.5),
                'severity': 'critical',
                'symptom': '全域集成避险控制发生碰撞或安全裕度不足 (<1.5s)',
                'physics_root_cause': (
                    '在全域跨跨链协同推演中，智驾纵向制动减速请求 (Decel Request) 与整车动力总成控制器 (VCU) 的驱动扭矩'
                    '仲裁出现逻辑冲突或响应延时，导致前向加塞出现时全制动未能第一优先级覆盖驱动输出。'
                ),
                'tuning_matrix': [
                    {'param': 'torque_arbitration_mode', 'current': lambda m: '--', 'action': '制动仲裁最高级', 'step': 'Priority=0', 'recommended': 'AEB 立即切断电驱动扭矩'},
                    {'param': 'ttc_threshold', 'current': lambda m: '--', 'action': '提前制动介入 ↑', 'step': '+0.4s', 'recommended': '2.2s ~ 2.6s'},
                ],
                'prescriptions': [
                    '在控制器仲裁逻辑中，确认 AEB 制动请求对动力驱动扭矩具有绝对抢占式最高优先级；',
                    '检查三链数据汇流时是否存在时步不同步造成的跨域通信时延滞后。'
                ],
                'oem_benchmark': 'ISO 26262 动力与底盘跨域协同功能安全 ASIL-D 级最高仲裁规范。'
            },
            {
                'condition': lambda m: _val(m, 'window_net_kwh', default=0.02) < 0.0 or _val(m, 'window_net_kwh', default=0.02) > 0.05,
                'severity': 'warning',
                'symptom': '机动工况窗口净耗电量级异常 (应处于 [0, 0.05] kWh 合理物理窗口)',
                'physics_root_cause': '避险机动窗口（约 30 秒 / 420 米行程）能量积分未正确同步计算电机正向驱动功与制动反向回充功的代数和。',
                'prescriptions': [
                    '核对机动窗口动力学电耗数值：Net_kWh = ∫ (P_drive - P_regen + P_aux) dt / 3600。'
                ],
                'oem_benchmark': '整车全域协同仿真能量流闭环核算标准。'
            }
        ]
    }
}


def diagnose_experiment(
    experiment_id: str,
    metrics: Dict[str, Any],
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """对指定实验进行深度机理故障诊断并给出结构化工程调优处方。

    :param experiment_id: 实验编号（如 'A1_cutin_aeb' 或 'A1'）
    :param metrics: 实验产出的 metrics 指标字典
    :param error_message: 异常报错信息（可选）
    :return: 结构化诊断报告
    """
    clean_id = experiment_id.replace('_pro', '').replace('_export', '')
    spec = DIAGNOSTIC_KNOWLEDGE_BASE.get(clean_id)
    if not spec:
        for k, v in DIAGNOSTIC_KNOWLEDGE_BASE.items():
            if k == clean_id or k.startswith(f"{clean_id}_") or clean_id.startswith(f"{k}_") or clean_id.split('_')[0].upper() == k.split('_')[0].upper():
                spec = v
                clean_id = k
                break

    findings = []
    if spec:
        for rule in spec['rules']:
            try:
                if rule['condition'](metrics):
                    t_matrix = []
                    for item in rule.get('tuning_matrix', []):
                        cur_val = item['current']
                        if callable(cur_val):
                            try:
                                cur_val = cur_val(metrics)
                            except Exception:
                                cur_val = '--'
                        t_matrix.append({
                            'param': item['param'],
                            'current': cur_val,
                            'action': item['action'],
                            'step': item.get('step', '--'),
                            'recommended': item.get('recommended', '--'),
                        })

                    findings.append({
                        'severity': rule.get('severity', 'warning'),
                        'symptom': rule['symptom'],
                        'physics_root_cause': rule['physics_root_cause'],
                        'tuning_matrix': t_matrix,
                        'prescriptions': rule.get('prescriptions', []),
                        'oem_benchmark': rule.get('oem_benchmark', ''),
                    })
            except Exception:
                continue

    # 通用断言与异常诊断
    if error_message and not findings:
        findings.append({
            'severity': 'critical',
            'symptom': f'代码执行中断: {error_message[:80]}...',
            'physics_root_cause': '数值求解发散、时钟步长越界或物理量空指针导致仿真进程非正常终止。',
            'tuning_matrix': [],
            'prescriptions': [
                '检查时步步长 dt 是否满足数值稳定性判据 (建议 dt <= 0.05s)；',
                '确认输入状态量不存在 NaN 或 Inf 数值；',
                '调用 snapshot_manager 查看最近一次成功运行的安全快照并进行代码 Diff 对比。'
            ],
            'oem_benchmark': '汽车电控系统软件架构鲁棒性容错与看门狗复位标准。'
        })

    is_healthy = len(findings) == 0

    return {
        'experiment_id': experiment_id,
        'experiment_name': spec.get('name', experiment_id) if spec else experiment_id,
        'is_healthy': is_healthy,
        'findings_count': len(findings),
        'findings': findings,
    }


def explain_failure(experiment_id: str, metrics: Dict[str, Any]) -> str:
    """生成简洁明了的纯文本/终端诊断摘要（供命令行与日志输出）"""
    res = diagnose_experiment(experiment_id, metrics)
    if res['is_healthy']:
        return f"✅ [{res['experiment_name']}] 各项动力学与能耗指标运行健康，未检出机理失效。"

    lines = [f"⚠️ [{res['experiment_name']}] 智能工程诊断发现 {res['findings_count']} 项关键失效风险:"]
    for i, f in enumerate(res['findings'], 1):
        lines.append(f"\n[{i}] 异常表征 ({f['severity'].upper()}): {f['symptom']}")
        lines.append(f"    • 物理根因: {f['physics_root_cause']}")
        if f['tuning_matrix']:
            lines.append("    • 推荐调参:")
            for t in f['tuning_matrix']:
                lines.append(f"      - {t['param']} (当前: {t['current']}) -> {t['action']} [{t['recommended']}]")
        if f['oem_benchmark']:
            lines.append(f"    • 行业规范: {f['oem_benchmark']}")
    return "\n".join(lines)


def render_copilot_card(diag_result: Dict[str, Any]) -> str:
    """生成高保真工业汽车级智能伴学诊断看板 (HTML)"""
    exp_name = diag_result['experiment_name']
    is_ok = diag_result['is_healthy']

    if is_ok:
        return f"""
        <div style="background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); color: white; border-radius: 10px; padding: 14px 18px; margin: 12px 0; font-family: system-ui, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08);">
            <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 26px;">🤖</span>
                <div>
                    <h4 style="margin: 0; font-size: 14px; color: #6ee7b7; font-weight: 700;">
                        IEV Diagnostic Tutor: 系统物理运行健康
                    </h4>
                    <p style="margin: 3px 0 0 0; font-size: 12px; color: #a7f3d0; line-height: 1.4;">
                        【{exp_name}】所有实测指标均处于汽车工程第一性原理最优区间，无动力学/电化学约束冲突。继续保持！
                    </p>
                </div>
            </div>
        </div>
        """

    cards_html = ""
    for idx, f in enumerate(diag_result['findings']):
        sev = f.get('severity', 'warning')
        if sev == 'critical':
            sev_badge = '<span style="background: #dc2626; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700;">🚨 致命失效 (CRITICAL)</span>'
            border_c = '#f87171'
        elif sev == 'warning':
            sev_badge = '<span style="background: #ea580c; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700;">⚠️ 性能超标 (WARNING)</span>'
            border_c = '#fb923c'
        else:
            sev_badge = '<span style="background: #0284c7; color: white; padding: 2px 7px; border-radius: 4px; font-size: 10px; font-weight: 700;">ℹ️ 策略偏保守 (INFO)</span>'
            border_c = '#38bdf8'

        # 调参处方矩阵表格
        matrix_html = ""
        if f.get('tuning_matrix'):
            rows = ""
            for row in f['tuning_matrix']:
                rows += f"""
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.08);">
                    <td style="padding: 6px 8px; font-family: monospace; color: #e2e8f0; font-weight: 600;">{row['param']}</td>
                    <td style="padding: 6px 8px; color: #94a3b8;">{row['current']}</td>
                    <td style="padding: 6px 8px; color: #38bdf8; font-weight: 700;">{row['action']}</td>
                    <td style="padding: 6px 8px; color: #cbd5e1;">{row['step']}</td>
                    <td style="padding: 6px 8px; color: #4ade80; font-weight: 600;">{row['recommended']}</td>
                </tr>
                """
            matrix_html = f"""
            <div style="margin-top: 10px; background: rgba(0,0,0,0.3); border-radius: 6px; padding: 10px; border: 1px solid rgba(255,255,255,0.06);">
                <div style="font-size: 11.5px; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">
                    🎛️ 推荐调参处方矩阵 (Actionable Parameter Tuning Matrix):
                </div>
                <table style="width: 100%; border-collapse: collapse; font-size: 11px; text-align: left;">
                    <thead>
                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.15); color: #94a3b8;">
                            <th style="padding: 4px 8px;">控制参数</th>
                            <th style="padding: 4px 8px;">当前估计</th>
                            <th style="padding: 4px 8px;">调节动作</th>
                            <th style="padding: 4px 8px;">建议步长</th>
                            <th style="padding: 4px 8px;">量产推荐区间</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            """

        rx_html = "".join(f"<li style='margin-bottom: 3px;'>{p}</li>" for p in f.get('prescriptions', []))
        oem_text = f.get('oem_benchmark', '')
        oem_html = f"""
        <div style="margin-top: 8px; font-size: 11px; color: #cbd5e1; background: rgba(59, 130, 246, 0.12); border-left: 3px solid #3b82f6; padding: 6px 10px; border-radius: 0 4px 4px 0;">
            <strong style="color: #93c5fd;">🏭 主机厂量产工程对标规范:</strong> {oem_text}
        </div>
        """ if oem_text else ""

        cards_html += f"""
        <div style="background: rgba(255,255,255,0.05); border: 1px solid {border_c}; border-radius: 8px; padding: 14px; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; flex-wrap: wrap; gap: 6px;">
                <span style="color: #f1f5f9; font-weight: 700; font-size: 13px;">
                    失效模式 #{idx+1}: {f['symptom']}
                </span>
                {sev_badge}
            </div>

            <div style="margin: 8px 0; font-size: 12px; color: #e2e8f0; line-height: 1.5; background: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 6px; border-left: 3px solid #f87171;">
                <strong style="color: #fca5a5;">🔍 物理与控制第一性原理因果剖析:</strong><br/>
                {f['physics_root_cause']}
            </div>

            {matrix_html}

            <div style="margin-top: 8px; font-size: 11.5px; color: #d1fae5; line-height: 1.5;">
                <strong style="color: #6ee7b7;">💡 工程师排障行动指南:</strong>
                <ul style="margin: 4px 0 0 16px; padding: 0;">
                    {rx_html}
                </ul>
            </div>

            {oem_html}
        </div>
        """

    html = f"""
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); color: white; border: 1px solid #6366f1; border-radius: 12px; padding: 16px 20px; margin: 14px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 8px 20px -4px rgba(0,0,0,0.35);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.12); padding-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 26px;">🤖</span>
                <div>
                    <h3 style="margin: 0; font-size: 15px; color: #a5b4fc; font-weight: 700;">
                        IEV Automotive Diagnostic Tutor · 汽车工程失效归因与调优助理
                    </h3>
                    <p style="margin: 3px 0 0 0; font-size: 11.5px; color: #94a3b8;">
                        目标实验: <strong style="color: #f8fafc;">{exp_name}</strong> | 自动捕获并归因 <strong style="color: #f87171;">{diag_result['findings_count']}</strong> 项物理/控制待整定项
                    </p>
                </div>
            </div>
            <span style="background: #dc2626; color: white; padding: 3px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;">
                ACTION REQUIRED
            </span>
        </div>
        {cards_html}
    </div>
    """
    return html


def ask_copilot(experiment_id: str, metrics: Dict[str, Any]):
    """供学生在 Notebook 中一键调用的交互式伴学诊断接口"""
    from IPython.display import HTML, display
    res = diagnose_experiment(experiment_id, metrics)
    display(HTML(render_copilot_card(res)))
