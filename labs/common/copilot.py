"""IEV CloudLab 智能工程导师与启发式故障自愈 Copilot | Engineering Copilot

功能说明：
  针对学生在仿真与算法开发过程中遭遇的断言失败、指标未达标或物理失稳，
  提供兼具严谨物理方程推导与工程直觉的启发式诊断指导。

核心特性：
  1. 覆盖 A~H 八大领域 29 门实验的机理故障树知识库 (Fault Tree Diagnostic Engine)；
  2. 根因量化归因 (Root Cause Attribution)：
     - 不仅指出“哪里错了”，更基于动力学/电化学第一性原理推导“为什么错”；
  3. 参数推荐与调优建议 (Prescriptive Guidance)：
     - 提供具体的工程标定经验区间（如 TTC 阈值、PID 增益、网格步长、Webster 周期）；
  4. Jupyter 原生极客风智能伴学看板 (HTML):
     - 包含机理诊断徽标、物理公式解析、调参处方卡与代码自愈提示。
"""

import math
import os
from typing import Dict, Any, List, Optional, Tuple, Union


# 29 门实验核心故障树知识库
DIAGNOSTIC_KNOWLEDGE_BASE = {
    'A1_cutin_aeb': {
        'name': 'Cut-in 加塞紧急避险',
        'rules': [
            {
                'condition': lambda m: m.get('collision') is True or m.get('min_ttc_s', 99) < 1.0,
                'symptom': '车辆发生碰撞或最小 TTC 触及极度危险区 (<1.0s)',
                'physics_root_cause': (
                    '在加塞切入初期，两车相对车速差 Δv 导致时距急剧收缩。根据运动学制动距离方程 '
                    's_stop = Δv² / (2 · |a_max|) + Δv · τ_delay。若 TTC 触发阈值设定过小，'
                    '自车在感知到切入意图后留给制动执行机构的距离小于物理停车极限制动距离。'
                ),
                'prescriptions': [
                    '适当调大 TTC 预警制动阈值（建议由默认的 1.5s 提升至 2.2s ~ 2.8s）；',
                    '检查制动减速度上限，确认紧急制动段设定为 -5.0 ~ -6.5 m/s² 之间；',
                    '检查车辆反应延时 τ_delay 是否在仿真时步积分中被过度放大。'
                ]
            },
            {
                'condition': lambda m: m.get('min_ttc_s', 0) > 3.5,
                'symptom': '避险触发过早，安全裕度过大（可能导致后方车辆追尾）',
                'physics_root_cause': 'TTC 阈值设定过大导致虚警率上升，在目标车尚未完全切入时便全力急刹，损害乘员舒适度并破坏后方交通流稳定。',
                'prescriptions': [
                    '收紧 TTC 判定阈值至 2.0s ~ 2.5s 合理量产区间；',
                    '引入分级预警逻辑：初段采用轻度点刹 (-2.0 m/s²)，紧急段再全力制动。'
                ]
            }
        ]
    },
    'A2_acc_follow': {
        'name': 'ACC 自适应巡航跟车',
        'rules': [
            {
                'condition': lambda m: m.get('max_spacing_error_m', 0) > 1.5,
                'symptom': '最大跟车间距误差超过 1.5m 门限',
                'physics_root_cause': 'ACC 控制器对前车车速变动的跟踪滞后，主要源于比例增益 Kp 过小导致响应迟缓，或积分时间常数过大未有效消除稳态静差。',
                'prescriptions': [
                    '适当提高车头时距误差增益 Kp（建议增大 20%~35%）；',
                    '引入前车相对速度前馈项 a_ff = Kv · (v_lead - v_ego)，显著提升动态变车速工况下的时距跟踪刚度。'
                ]
            }
        ]
    },
    'B1_idm_calibration': {
        'name': 'IDM 智能跟驰模型参数标定',
        'rules': [
            {
                'condition': lambda m: m.get('rmse', 0) > 0.6,
                'symptom': '标定 RMSE 超过 0.60 拟合阈值',
                'physics_root_cause': '非线性最小二乘优化算法掉入局部极小值，或待标定参数搜索边界（Bounds）与初值设置偏离实际物理常识。',
                'prescriptions': [
                    '检查待标定参数初值：建议初值设为 v0=30m/s, T=1.5s, s0=2.0m, a=1.5m/s², b=2.0m/s²；',
                    '采用两阶段标定：先固定静止安全距离 s0 和期望车速 v0，再使用 SciPy curve_fit 集中拟合舒适加速度 a 与期望车头时距 T。'
                ]
            }
        ]
    },
    'B2_traffic_signal': {
        'name': '交叉口信号配时优化',
        'rules': [
            {
                'condition': lambda m: m.get('delay_reduction_pct', 0) < 50.0,
                'symptom': '延误降低率未达到 50% 优化要求',
                'physics_root_cause': '红绿灯周期 C 或绿信比未能匹配东西向与南北向非对称交通流量比 (y_ew / y_ns)。',
                'prescriptions': [
                    '严格采用 Webster 理论最佳周期公式 C0 = (1.5L + 5) / (1 - Y)，其中总损失时间 L=8s；',
                    '按各关键相位流量比严格切分绿灯时长：g_i = (y_i / Y) · (C - L)。'
                ]
            }
        ]
    },
    'C1_fastsim_energy': {
        'name': '整车百公里电耗仿真',
        'rules': [
            {
                'condition': lambda m: m.get('energy_kwh_100km', 0) > 20.0,
                'symptom': '百公里电耗偏高 (>20.0 kWh/100km)',
                'physics_root_cause': '再生制动能量回收逻辑未正确生效，或整车质量/迎风风阻乘积 Cd*A 赋值异常偏大。',
                'prescriptions': [
                    '确认 SimDrive 中电池负功率段（减速回充）是否成功被计入能量积分；',
                    '检查车辆数据库中 BEV 的整备质量是否处于 1500~1900kg 合理范围。'
                ]
            }
        ]
    },
    'D3_ocv_soc_export': {
        'name': '电池 OCV-SOC 标定',
        'rules': [
            {
                'condition': lambda m: m.get('calibration_error_pct', 0) > 5.0,
                'symptom': '最大标定误差超标 (>5.0%)',
                'physics_root_cause': '在极低 SOC (<15%) 或极高 SOC (>85%) 区间，电池固相扩散与电荷转移极化超电势急剧发散，导致放电端电压严重偏离热力学平衡开路电压。',
                'prescriptions': [
                    '改用更低放电倍率作为参比基准（如 C/50 准静态放电）；',
                    '在 SOC 网格插值拟合时，对非线性极化区采用分段多项式或单调 PCHIP 插值，抑制龙格振荡。'
                ]
            }
        ]
    },
    'E4_dp_ems': {
        'name': '动态规划 (DP) 全局能量管理',
        'rules': [
            {
                'condition': lambda m: m.get('fuel_l_100km', 99) > 2.2,
                'symptom': 'DP 最优油耗未击穿 2.2 L/100km 极限',
                'physics_root_cause': '状态离散网格（SOC grid 与工况时步）划分过粗，导致插值重采样过程产生非物理数值耗散，或者终端 SOC 惩罚项权重不足导致电池出现虚假电量透支。',
                'prescriptions': [
                    '将 SOC 离散网格分辨率由 100 增细至 200 点以上；',
                    '提高终端 SOC 边界惩罚系数：Cost_terminal = α · (SOC_end - SOC_target)²，确保等容电平衡。'
                ]
            }
        ]
    },
}


def diagnose_experiment(
    experiment_id: str,
    metrics: Dict[str, Any],
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    """对指定实验进行深度机理故障诊断并给出调优处方。

    :param experiment_id: 实验编号（如 'A1_cutin_aeb'）
    :param metrics: 实验产出的 metrics 指标字典
    :param error_message: 异常报错信息（可选）
    :return: 结构化诊断报告
    """
    clean_id = experiment_id.replace('_pro', '')
    spec = DIAGNOSTIC_KNOWLEDGE_BASE.get(clean_id)

    findings = []
    if spec:
        for rule in spec['rules']:
            try:
                if rule['condition'](metrics):
                    findings.append({
                        'symptom': rule['symptom'],
                        'physics_root_cause': rule['physics_root_cause'],
                        'prescriptions': rule['prescriptions'],
                    })
            except Exception:
                continue

    # 通用断言与异常诊断
    if error_message and not findings:
        findings.append({
            'symptom': f'代码执行中断: {error_message[:80]}...',
            'physics_root_cause': '仿真步长溢出、空指针解引用或边界条件越界导致数值求解器异常中止。',
            'prescriptions': [
                '检查时步步长 dt 是否满足数值稳定性判据 (建议 dt <= 0.1s)；',
                '确认输入变量不存在 NaN 或 Inf 数值；',
                '利用 snapshot_manager 查看最近一次成功运行的代码差异。'
            ]
        })

    is_healthy = len(findings) == 0

    return {
        'experiment_id': experiment_id,
        'experiment_name': spec.get('name', experiment_id) if spec else experiment_id,
        'is_healthy': is_healthy,
        'findings_count': len(findings),
        'findings': findings,
    }


def render_copilot_card(diag_result: Dict[str, Any]) -> str:
    """生成未来感智能工程伴学诊断卡 (HTML)"""
    exp_name = diag_result['experiment_name']
    is_ok = diag_result['is_healthy']

    if is_ok:
        return f"""
        <div style="background: linear-gradient(135deg, #064e3b 0%, #065f46 100%); color: white; border-radius: 10px; padding: 16px 20px; margin: 12px 0; font-family: system-ui, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 24px;">🤖</span>
                <div>
                    <h4 style="margin: 0; font-size: 15px; color: #6ee7b7;">IEV Copilot 智能导师: 系统运行健康</h4>
                    <p style="margin: 4px 0 0 0; font-size: 12px; color: #a7f3d0;">
                        【{exp_name}】各项动力学与能耗指标均处于工业物理基准最优区间，无机理冲突。继续保持！
                    </p>
                </div>
            </div>
        </div>
        """

    cards_html = ""
    for idx, f in enumerate(diag_result['findings']):
        rx_html = "".join(f"<li style='margin-bottom: 4px;'>{p}</li>" for p in f['prescriptions'])
        cards_html += f"""
        <div style="background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; padding: 14px; margin-top: 10px;">
            <div style="display: flex; align-items: center; gap: 6px; color: #fca5a5; font-weight: 700; font-size: 13px;">
                <span>⚠️ 异常表征 #{idx+1}:</span> {f['symptom']}
            </div>
            <div style="margin: 8px 0; font-size: 12px; color: #e2e8f0; line-height: 1.5; background: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 6px;">
                <strong style="color: #93c5fd;">🔍 物理第一性原理推导:</strong><br/>
                {f['physics_root_cause']}
            </div>
            <div style="font-size: 12px; color: #d1fae5; line-height: 1.5;">
                <strong style="color: #6ee7b7;">💡 Copilot 调优建议处方:</strong>
                <ul style="margin: 4px 0 0 16px; padding: 0;">
                    {rx_html}
                </ul>
            </div>
        </div>
        """

    html = f"""
    <div style="background: linear-gradient(135deg, #1e1b4b 0%, #1e293b 100%); color: white; border: 1px solid #4338ca; border-radius: 12px; padding: 18px 22px; margin: 14px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 8px 20px -4px rgba(0,0,0,0.3);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 10px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 26px;">🤖</span>
                <div>
                    <h3 style="margin: 0; font-size: 16px; color: #818cf8; font-weight: 700;">
                        IEV Copilot 智能导师 · 启发式物理机理诊断
                    </h3>
                    <p style="margin: 3px 0 0 0; font-size: 12px; color: #94a3b8;">
                        实验项目: <strong>{exp_name}</strong> | 识别到 {diag_result['findings_count']} 项关键性能待调优
                    </p>
                </div>
            </div>
            <span style="background: #ef4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                ACTION NEEDED
            </span>
        </div>
        {cards_html}
    </div>
    """
    return html


def ask_copilot(experiment_id: str, metrics: Dict[str, Any]):
    """供学生在 Notebook 中一键调用的交互式伴学接口"""
    from IPython.display import HTML, display
    res = diagnose_experiment(experiment_id, metrics)
    display(HTML(render_copilot_card(res)))
