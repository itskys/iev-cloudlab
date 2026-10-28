"""IEV CloudLab 跨实验数据链路门禁与关联分析 | Cross-Experiment Chain Validator

核心功能：
  1. D3 (电池电化学 OCV-SOC 标定) → C1 (FASTSim 整车百公里能耗仿真) 数据链路门禁校验；
  2. 智能前置条件自检与动态参数注入 (load_chained_battery_model)；
  3. 教学诊断反馈：
     - 若学生已完成 D3 且标定误差 < 5.0%，无缝接入其个人标定电池曲线；
     - 若未完成 D3 或标定误差超标，优雅回退至官方基准曲线，并给出高亮教学提示；
  4. 交互式数据链路状态卡片 (HTML/Markdown 渲染)；
  5. 全班“电池标定误差 vs 整车能耗预测方差”关联敏感性分析与散点回归图生成。
"""

import json
import math
import os
from typing import Dict, Any, Optional, Tuple, List, Union

try:
    from common.battery_adapter import BatteryFASTSimAdapter
except ImportError:
    try:
        from .battery_adapter import BatteryFASTSimAdapter
    except ImportError:
        BatteryFASTSimAdapter = None

DEFAULT_RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
DEFAULT_BATTERY_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'batteries')
DEFAULT_CSV_PATH = os.path.join(DEFAULT_BATTERY_DIR, 'chen2020_nmc_75ah.csv')


class ChainValidationResult:
    """数据链路校验结果对象"""

    def __init__(
        self,
        is_valid: bool,
        has_d3_record: bool,
        calibration_err_pct: Optional[float],
        csv_exists: bool,
        csv_path: str,
        using_student_model: bool,
        status_message: str,
        diagnostic_advice: str,
    ):
        self.is_valid = is_valid
        self.has_d3_record = has_d3_record
        self.calibration_err_pct = calibration_err_pct
        self.csv_exists = csv_exists
        self.csv_path = csv_path
        self.using_student_model = using_student_model
        self.status_message = status_message
        self.diagnostic_advice = diagnostic_advice

    def to_dict(self) -> Dict[str, Any]:
        return {
            'is_valid': self.is_valid,
            'has_d3_record': self.has_d3_record,
            'calibration_err_pct': self.calibration_err_pct,
            'csv_exists': self.csv_exists,
            'csv_path': self.csv_path,
            'using_student_model': self.using_student_model,
            'status_message': self.status_message,
            'diagnostic_advice': self.diagnostic_advice,
        }


def validate_d3_to_c1_chain(
    results_dir: Optional[str] = None,
    battery_csv_path: Optional[str] = None,
    max_error_threshold: float = 5.0,
) -> ChainValidationResult:
    """核验 D3 电池标定实验产出是否符合 C1 整车仿真准入条件。

    :param results_dir: 结果目录（默认为 labs/data/results）
    :param battery_csv_path: 标定 CSV 文件路径
    :param max_error_threshold: 允许的最大标定误差百分比（默认 5.0%）
    :return: ChainValidationResult
    """
    if results_dir is None:
        results_dir = DEFAULT_RESULTS_DIR
    if battery_csv_path is None:
        battery_csv_path = DEFAULT_CSV_PATH

    # 1. 查找 D3 运行记录
    d3_file = os.path.join(results_dir, 'D3_ocv_soc_export.json')
    if not os.path.exists(d3_file):
        d3_file = os.path.join(results_dir, 'D3_ocv_soc.json')

    has_d3 = os.path.exists(d3_file)
    cal_err = None

    if has_d3:
        try:
            with open(d3_file, 'r', encoding='utf-8') as f:
                d3_data = json.load(f)
            m = d3_data.get('metrics', d3_data)
            cal_err = m.get('calibration_max_err_pct', m.get('calibration_error_pct', m.get('mean_err_pct')))
        except Exception:
            has_d3 = False

    csv_exists = os.path.exists(battery_csv_path)

    # 2. 判断准入状态
    if not has_d3:
        return ChainValidationResult(
            is_valid=False,
            has_d3_record=False,
            calibration_err_pct=None,
            csv_exists=csv_exists,
            csv_path=battery_csv_path,
            using_student_model=False,
            status_message='未检测到 D3 实验归档记录',
            diagnostic_advice='请先运行并完成 D3_ocv_soc_export 实验，生成属于您自己的电池 OCV-SOC 特性模型。当前仿真将采用官方默认基准参数。',
        )

    if cal_err is not None and cal_err > max_error_threshold:
        return ChainValidationResult(
            is_valid=False,
            has_d3_record=True,
            calibration_err_pct=float(cal_err),
            csv_exists=csv_exists,
            csv_path=battery_csv_path,
            using_student_model=False,
            status_message=f'D3 标定误差超标 ({cal_err:.2f}% > {max_error_threshold}%)',
            diagnostic_advice='您的 D3 电池标定误差过大，直接注入整车仿真会导致电耗估算失真。建议返回 D3 优化低倍率放电拟合后重新导出。',
        )

    if not csv_exists:
        return ChainValidationResult(
            is_valid=False,
            has_d3_record=True,
            calibration_err_pct=float(cal_err) if cal_err else None,
            csv_exists=False,
            csv_path=battery_csv_path,
            using_student_model=False,
            status_message='D3 标定数据 CSV 文件未生成',
            diagnostic_advice='已检测到 D3 运行评分，但标准 CSV 导出文件缺失。请确认 D3 导出单元格已成功执行。',
        )

    # 全部满足
    return ChainValidationResult(
        is_valid=True,
        has_d3_record=True,
        calibration_err_pct=float(cal_err) if cal_err else 0.0,
        csv_exists=True,
        csv_path=battery_csv_path,
        using_student_model=True,
        status_message=f'链路闭环成功 (D3 标定误差: {cal_err:.2f}%)',
        diagnostic_advice='已成功加载您的 D3 个人标定电池模型，整车百公里电耗仿真将基于真实电化学特性进行积分计算。',
    )


def load_chained_battery_model(
    veh: Any,
    nominal_capacity_ah: float = 75.0,
    n_cells: int = 40,
    results_dir: Optional[str] = None,
    battery_csv_path: Optional[str] = None,
) -> Tuple[Any, ChainValidationResult]:
    """为 FASTSim 整车对象动态绑定前置 D3 标定电池数据。

    :param veh: FASTSim Vehicle 对象
    :param nominal_capacity_ah: 单体标称容量 (Ah)
    :param n_cells: 动力电池包串并联等效成组系数 (默认 40 串，匹配 ~10kWh Pack)
    :param results_dir: 结果目录
    :param battery_csv_path: 电池 CSV 文件路径
    :return: (updated_veh, chain_result)
    """
    chain_res = validate_d3_to_c1_chain(results_dir, battery_csv_path)

    if chain_res.is_valid and BatteryFASTSimAdapter is not None:
        try:
            adapter = BatteryFASTSimAdapter(chain_res.csv_path)
            # 成组动力总成等效映射：单体积分能量 × 成组系数
            veh = adapter.apply_to_vehicle(veh, nominal_capacity_ah * n_cells)
            veh._chain_validation = chain_res.to_dict()
            return veh, chain_res
        except Exception as e:
            chain_res.is_valid = False
            chain_res.using_student_model = False
            chain_res.status_message = f'加载标定电池模型失败: {str(e)}'
            chain_res.diagnostic_advice = '读取 CSV 格式异常，已切换至系统默认电池包模型。'

    # 回退模式
    if hasattr(veh, '_chain_validation'):
        delattr(veh, '_chain_validation')
    return veh, chain_res


def render_chain_status_html(chain_res: ChainValidationResult) -> str:
    """生成可在 Jupyter Notebook 中展示的高保真链路状态卡片"""
    is_ok = chain_res.is_valid
    accent_color = "#10b981" if is_ok else "#f59e0b"
    bg_gradient = "linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%)" if is_ok else "linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)"
    border_color = "#34d399" if is_ok else "#fbbf24"
    icon = "🔗" if is_ok else "⚠️"
    status_title = "D3 电池电化学 → C1 整车能耗跨实验数据链路已连接" if is_ok else "D3 → C1 跨实验数据链路未闭环 (已使用默认模型)"

    err_badge = ""
    if chain_res.calibration_err_pct is not None:
        err_badge = f"""
        <span style="background: white; border: 1px solid {border_color}; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; color: #374151;">
            D3 标定误差: {chain_res.calibration_err_pct:.2f}%
        </span>
        """

    html = f"""
    <div style="background: {bg_gradient}; border: 1px solid {border_color}; border-radius: 10px; padding: 14px 18px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 2px 4px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 20px;">{icon}</span>
                <strong style="color: #111827; font-size: 14px;">{status_title}</strong>
            </div>
            <div>{err_badge}</div>
        </div>
        <div style="margin-top: 8px; font-size: 13px; color: #4b5563; line-height: 1.5;">
            <p style="margin: 0;"><strong>链路状态</strong>: {chain_res.status_message}</p>
            <p style="margin: 4px 0 0 0; color: #1f2937;"><strong>工程诊断建议</strong>: {chain_res.diagnostic_advice}</p>
        </div>
    </div>
    """
    return html


def analyze_battery_energy_chain(all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """全班“电池标定误差 vs 整车百公里电耗”关联统计分析。

    :param all_results: {username: {exp_id: metrics_dict}}
    :return: 统计指标字典，包含数据点对、相关系数、均值与方差
    """
    points = []
    for user, exps in all_results.items():
        d3_res = exps.get('D3_ocv_soc_export', exps.get('D3_ocv_soc'))
        c1_res = exps.get('C1_fastsim_energy')

        if not d3_res or not c1_res:
            continue

        d3_m = d3_res.get('metrics', d3_res)
        c1_m = c1_res.get('metrics', c1_res)

        cal_err = d3_m.get('calibration_max_err_pct', d3_m.get('calibration_error_pct'))
        energy = c1_m.get('energy_kwh_100km', c1_m.get('electric_kwh_100km'))

        if cal_err is not None and energy is not None:
            try:
                points.append({
                    'user': user,
                    'cal_err_pct': float(cal_err),
                    'energy_kwh': float(energy),
                })
            except (ValueError, TypeError):
                continue

    if len(points) < 2:
        return {
            'n_samples': len(points),
            'correlation_r': 0.0,
            'mean_cal_err': 0.0,
            'mean_energy': 0.0,
            'points': points,
        }

    xs = [p['cal_err_pct'] for p in points]
    ys = [p['energy_kwh'] for p in points]

    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    # 计算 Pearson 相关系数 r
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)

    if var_x > 1e-12 and var_y > 1e-12:
        cov_xy = sum((xs[i] - mean_x) * (ys[i] - mean_y) for i in range(n))
        r = cov_xy / math.sqrt(var_x * var_y)
    else:
        r = 0.0

    return {
        'n_samples': n,
        'correlation_r': round(r, 4),
        'mean_cal_err': round(mean_x, 3),
        'mean_energy': round(mean_y, 2),
        'points': points,
    }


def plot_chain_correlation(
    all_results: Dict[str, Dict[str, Any]],
    output_png: Optional[str] = None,
) -> Optional[str]:
    """生成“D3 标定误差 vs C1 电耗仿真”关联散点与回归拟合图（供教师看板）。

    :param all_results: {username: {exp_id: metrics}}
    :param output_png: 输出图片路径
    :return: 图像保存路径，若无足够样本则返回 None
    """
    analysis = analyze_battery_energy_chain(all_results)
    if analysis['n_samples'] < 2:
        return None

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np

        if output_png is None:
            chart_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'results', 'charts')
            os.makedirs(chart_dir, exist_ok=True)
            output_png = os.path.join(chart_dir, 'chain_d3_c1_correlation.png')
        else:
            os.makedirs(os.path.dirname(os.path.abspath(output_png)), exist_ok=True)

        xs = np.array([p['cal_err_pct'] for p in analysis['points']])
        ys = np.array([p['energy_kwh'] for p in analysis['points']])

        fig, ax = plt.subplots(figsize=(8, 5), dpi=150)
        ax.scatter(xs, ys, color='#2563eb', alpha=0.7, s=45, edgecolors='white', linewidth=1, label='Student Experiments')

        # 线性拟合趋势线
        if len(xs) >= 2:
            poly = np.polyfit(xs, ys, 1)
            line_x = np.linspace(min(xs), max(xs), 50)
            line_y = np.polyval(poly, line_x)
            ax.plot(line_x, line_y, color='#dc2626', linestyle='--', linewidth=2,
                    label=f'Linear Fit (r = {analysis["correlation_r"]:.3f})')

        ax.set_title('Cross-Lab Data Chain: Battery Calibration Error vs. Vehicle Energy', fontsize=12, pad=10, fontweight='bold')
        ax.set_xlabel('D3 Battery OCV-SOC Calibration Max Error (%)', fontsize=10)
        ax.set_ylabel('C1 FASTSim UDDS Energy Consumption (kWh/100km)', fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend(frameon=True, loc='upper left')

        plt.tight_layout()
        plt.savefig(output_png, bbox_inches='tight')
        plt.close(fig)
        return output_png
    except Exception as e:
        print(f"[ChainValidator] Plotting error: {e}")
        return None
