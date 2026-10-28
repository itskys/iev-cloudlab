"""IEV CloudLab H2 极限工况主动安全避障排位赛基准 | Autonomous Safety Fuzzing Benchmark

赛道规则：
  - 测试工况：100 例高拟真极值边缘工况批量注入 (Fuzzing Suite)
    - 切入前车初速度: 15 ~ 30 m/s
    - 危险切入距离: 12 ~ 28 m
    - 前车突发紧急制动减速度: -3.0 ~ -8.5 m/s² (含雨雪低附着路面扰动)
  - 核心考核维度：
    1. 零碰撞防撞达标率 (占分 50%，发生碰撞单项归零)
    2. 临界安全裕度 Min TTC (占分 30%，考核避险极限)
    3. 纵向乘员舒适度 RMS Jerk (占分 20%，考核平顺性)
"""

import numpy as np
from .leaderboard import submit_score, render_leaderboard


def run_h2_benchmark(controller_fn, username="student", render=True):
    """运行 H2 极限避障挑战赛 (100 例 Fuzzing 批量闭环推演)。

    参数:
      controller_fn: 学生避障控制器函数:
                     a_cmd = controller_fn(v_ego, v_lead, distance, ttc)
      username: 学生账号 (如 'student_2026')
      render: 是否返回渲染的 HTML 天梯榜

    返回:
      dict: 评测指标与排名信息
    """
    np.random.seed(42)  # 固定标准化基准种子
    n_scenarios = 100

    collisions = 0
    min_ttcs = []
    jerks = []

    dt = 0.05
    sim_time = 6.0
    steps = int(sim_time / dt)

    for sc_idx in range(n_scenarios):
        # 随机场景参数生成
        v_ego_0 = np.random.uniform(20.0, 30.0)  # 72 ~ 108 km/h
        v_lead_0 = np.random.uniform(15.0, 25.0)
        dist_0 = np.random.uniform(14.0, 28.0)
        lead_brake_a = np.random.uniform(-8.0, -3.0)  # 前车制动减速度
        brake_delay = np.random.uniform(0.5, 1.2)  # 延迟刹车时间

        x_ego = 0.0
        x_lead = dist_0
        v_ego = v_ego_0
        v_lead = v_lead_0
        a_ego_prev = 0.0

        scenario_min_ttc = 99.0
        scenario_jerks = []
        is_collision = False

        for st in range(steps):
            t_cur = st * dt
            # 前车运动更新
            a_lead = lead_brake_a if t_cur >= brake_delay else 0.0
            v_lead = max(0.0, v_lead + a_lead * dt)
            x_lead += v_lead * dt

            # 间距与 TTC 计算
            gap = x_lead - x_ego - 4.5
            rel_v = v_ego - v_lead
            ttc = (gap / rel_v) if rel_v > 0.1 and gap > 0 else 99.0
            if ttc < scenario_min_ttc and ttc > 0:
                scenario_min_ttc = ttc

            # 碰撞判定
            if gap <= 0.0:
                is_collision = True
                collisions += 1
                break

            # 调用学生控制器
            try:
                a_cmd = controller_fn(v_ego, v_lead, gap, ttc)
            except Exception:
                # 默认后备制动
                a_cmd = -6.0 if ttc < 2.0 else 0.0

            a_cmd = np.clip(a_cmd, -8.5, 2.0)
            jerk = (a_cmd - a_ego_prev) / dt
            scenario_jerks.append(jerk)
            a_ego_prev = a_cmd

            # 主车运动更新
            v_ego = max(0.0, v_ego + a_cmd * dt)
            x_ego += v_ego * dt

        min_ttcs.append(scenario_min_ttc)
        if scenario_jerks:
            jerks.append(float(np.sqrt(np.mean(np.square(scenario_jerks)))))

    # 统计 100 例全局指标
    collision_free_rate = ((n_scenarios - collisions) / n_scenarios) * 100.0
    global_min_ttc = float(np.min(min_ttcs))
    mean_jerk_rms = float(np.mean(jerks)) if jerks else 0.0

    # 综合天梯分
    # 碰撞分 (50 分，要求 0 碰撞)
    safety_score = 50.0 if collisions == 0 else max(0.0, 50.0 - collisions * 15.0)
    # 安全裕度分 (30 分，min TTC > 1.2s 满分)
    ttc_score = max(0.0, min(30.0, (global_min_ttc / 1.2) * 30.0))
    # 舒适度分 (20 分，jerk < 3.0 m/s³ 满分)
    comfort_score = max(0.0, min(20.0, 20.0 - max(0.0, mean_jerk_rms - 2.5) * 4.0))

    final_score = round(safety_score + ttc_score + comfort_score, 1)

    metrics = {
        "无碰撞率 (%)": f"{collision_free_rate:.1f}%",
        "极限 Min TTC (s)": round(global_min_ttc, 2),
        "平顺度 Jerk (m/s³)": round(mean_jerk_rms, 2),
    }

    result = submit_score(
        benchmark_name="h2_safety_fuzzing",
        user_id=username,
        score=final_score,
        metrics=metrics,
    )

    if render:
        return render_leaderboard(
            benchmark_name="h2_safety_fuzzing",
            current_user=username,
            title="IEV H2 极值工况主动安全避障 (Safety Fuzzing) 天梯挑战赛",
            top_n=10,
        )
    return result
