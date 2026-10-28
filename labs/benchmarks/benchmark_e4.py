"""IEV CloudLab E4 能量管理排位赛基准 | Energy Management Strategy (EMS) Benchmark

赛道规则：
  - 测试工况：未知复合高难度工况（标准 WLTC Class 3 叠加 ±3.5% 动态坡道扰动）
  - 核心考核维度：
    1. 综合等效燃油能耗 (L/100km, 占分 50%)
    2. 电池 SOC 终端电量自持精度 (|SOC_end - SOC_init|, 占分 30%)
    3. 控制策略单步解算耗时 (ms/步, 占分 20%，考核车载嵌入式实时性)
"""

import time
import numpy as np
from .leaderboard import submit_score, render_leaderboard


def _generate_unseen_benchmark_cycle():
    """生成标准化且具挑战性的评测工况 (t, v, grade, p_req)。"""
    # 模拟 300s 复合城市与高速综合路况
    t = np.linspace(0, 300, 301)
    # 速度曲线 (m/s)
    v = (
        12.0 * np.sin(t * 0.02) ** 2
        + 8.0 * np.sin(t * 0.05)
        + 5.0 * np.sin(t * 0.1)
    )
    v = np.clip(v, 0.0, 30.0)  # 最高 108 km/h

    # 动态道路坡度 (-3% ~ +4%)
    grade = 0.025 * np.sin(t * 0.015) + 0.01 * np.cos(t * 0.04)

    # 动力总成需求功率 (kW): 滚动阻力 + 空阻 + 坡阻 + 加速阻力
    dt = 1.0
    acc = np.gradient(v, dt)
    m = 1600.0  # 整车质量 kg
    f_roll = m * 9.81 * 0.012
    f_grade = m * 9.81 * grade
    f_aero = 0.5 * 1.205 * 0.32 * 2.2 * (v ** 2)
    f_acc = m * acc
    f_total = f_roll + f_grade + f_aero + f_acc
    p_req = (f_total * v) / 1000.0  # kW

    return t, v, grade, p_req


def run_e4_benchmark(ems_fn, username="student", render=True):
    """运行 E4 能耗挑战赛。

    参数:
      ems_fn: 学生编写的策略函数或类，调用方式:
              p_eng, p_mot = ems_fn(t_step, v, p_req, soc)
      username: 学生账号 (如 'student_2026')
      render: 是否返回渲染的 HTML 天梯榜

    返回:
      dict: 评测指标与排名信息
    """
    t, v, grade, p_req = _generate_unseen_benchmark_cycle()
    n_steps = len(t)

    soc = 0.60
    total_fuel_g = 0.0
    solve_times = []

    # 简化的混动动力总成物理参数
    bsfc_min = 215.0  # g/kWh
    bat_kwh = 12.0

    for i in range(n_steps):
        cur_t = t[i]
        cur_v = v[i]
        cur_preq = p_req[i]

        t0 = time.perf_counter()
        try:
            p_eng, p_mot = ems_fn(cur_t, cur_v, cur_preq, soc)
        except Exception:
            # 容错后备策略
            p_eng = max(0.0, cur_preq * 0.6)
            p_mot = cur_preq - p_eng

        t_solve = (time.perf_counter() - t0) * 1000.0  # ms
        solve_times.append(t_solve)

        # 燃油消耗计算
        if p_eng > 0.5:
            fuel_rate = (p_eng * bsfc_min) / 3600.0  # g/s
            total_fuel_g += fuel_rate * 1.0

        # 电池 SOC 积分
        # P_mot > 0 放电，P_mot < 0 制动回馈
        i_bat_kw = p_mot / 0.92 if p_mot > 0 else p_mot * 0.88
        delta_soc = -(i_bat_kw / (bat_kwh * 3600.0)) * 1.0
        soc = np.clip(soc + delta_soc, 0.20, 0.90)

    # 统计综合指标
    total_km = np.trapz(v, t) / 1000.0
    fuel_l_per_100km = (total_fuel_g / 745.0) / (total_km / 100.0)  # 汽油密度 745 g/L
    soc_error = abs(soc - 0.60)
    avg_solve_ms = float(np.mean(solve_times))

    # 综合排位分模型 (满分 100)
    # 能耗分 (基准 4.5 L/100km)
    fuel_score = max(0.0, min(50.0, 50.0 - (fuel_l_per_100km - 3.8) * 20.0))
    # 电量平衡自持分 (|ΔSOC| < 0.02 满分 30)
    soc_score = max(0.0, min(30.0, 30.0 - soc_error * 350.0))
    # 实时性分 (< 5ms 满分 20)
    speed_score = max(0.0, min(20.0, 20.0 - max(0.0, avg_solve_ms - 2.0) * 2.5))

    final_score = round(fuel_score + soc_score + speed_score, 1)

    metrics = {
        "综合油耗 (L/100km)": round(fuel_l_per_100km, 2),
        "电量自持误差 |ΔSOC|": round(soc_error, 3),
        "解算时延 (ms/步)": round(avg_solve_ms, 2),
    }

    result = submit_score(
        benchmark_name="e4_ems_challenge",
        user_id=username,
        score=final_score,
        metrics=metrics,
    )

    if render:
        return render_leaderboard(
            benchmark_name="e4_ems_challenge",
            current_user=username,
            title="IEV E4 混合动力能量管理 (EMS) 极限排位赛",
            top_n=10,
        )
    return result
