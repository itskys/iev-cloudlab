"""新手模式驱动（lite drivers）| Beginner-mode drivers.

设计原则：
- 薄壳：只做“参数 -> 调用真实引擎 -> 整理结果”，不复制、不简化引擎本身。
- 与完整模式共用同一批引擎：esmini（A1）、SUMO TraCI（B2）、FASTSim（C1）、
  PyBaMM（D1）、CasADi MPC（E3）。新手本里看到的数字，和完整模式是同一口径。
- 基线缓存：每个实验的“默认参数”结果在同一 kernel 内只算一次，
  学生拖动滑杆后只需重算自己那一组，交互不卡顿。
- 成绩隔离：新手本只写 labs/data/lite/ 与 labs/data/preview_checkins/ 下的完成记录，
  绝不写 labs/data/results/，不进教师成绩册（见 save_lite_record）。
- 体验升级（Antigravity 优化）：
  1. 增加 silence_stdio() 抑制 esmini 与 SUMO 底层 C++ / TraCI 告警，还学生清爽界面；
  2. 自动挂载 CJK 中文字体，图表全面中文化；
  3. 提供统一的高质感 HTML 指标卡与物理因果解读。
"""

import os
import sys
import json
import tempfile
import warnings
import datetime
import contextlib
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

# 配置高清晰度 CJK 中文字体支持
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

plt.rcParams['font.sans-serif'] = ['Noto Sans CJK SC', 'WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

LITE_DIR = "/home/jovyan/labs/data/lite"
_CACHE = {}


@contextlib.contextmanager
def silence_stdio():
    """静默 C/C++ 底层 stdout/stderr 输出与警告（避免 esmini/SUMO/IPOPT 打印底层日志干扰初学者）"""
    sys.stdout.flush()
    sys.stderr.flush()
    try:
        devnull_fd = os.open(os.devnull, os.O_RDWR)
        saved_stdout_fd = os.dup(1)
        saved_stderr_fd = os.dup(2)
        os.dup2(devnull_fd, 1)
        os.dup2(devnull_fd, 2)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            yield
    except Exception:
        yield
    finally:
        sys.stdout.flush()
        sys.stderr.flush()
        try:
            os.dup2(saved_stdout_fd, 1)
            os.dup2(saved_stderr_fd, 2)
            os.close(saved_stdout_fd)
            os.close(saved_stderr_fd)
            os.close(devnull_fd)
        except Exception:
            pass


# ---------------------------------------------------------------- A1
def _a1_controller_class():
    try:
        from common.controller import BaseController
    except ImportError:  # pragma: no cover
        from .controller import BaseController

    class LiteAEBController(BaseController):
        """TTC 分级制动：触发阈值就是滑杆值（基础版此处写死 3.0）."""

        def __init__(self, config=None):
            super().__init__(config)
            self.ttc_threshold = float(self.config.get("ttc_threshold", 3.0))

        def step(self, observation):
            ego = observation["ego"]
            targets = observation.get("targets", [])
            if not targets:
                return {"target_a": 0.5, "steer_angle": 0.0}
            lead = min(targets, key=lambda t: abs(t["x"] - ego["x"]))
            rel_dist = abs(lead["x"] - ego["x"]) - 4.5
            rel_v = ego["v"] - lead["v"]
            ttc = float("inf") if rel_v <= 0 else rel_dist / rel_v
            a = -5.0 if ttc < self.ttc_threshold else 0.0
            return {"target_a": a, "steer_angle": 0.0}

    return LiteAEBController


def run_a1_lite(ttc_threshold, scenario=None, road=None):
    """真 esmini 闭环：Cut-in 加塞 + TTC 制动。返回轨迹与指标。"""
    try:
        from common.esmini_env import EsminiEnv
    except ImportError:  # pragma: no cover
        from .esmini_env import EsminiEnv

    scenario = scenario or "/home/jovyan/labs/scenarios/A_esmini/A1_cutin/cutin.xosc"
    road = road or "/home/jovyan/labs/scenarios/A_esmini/A1_cutin/cutin.xodr"
    controller = _a1_controller_class()(config={"ttc_threshold": float(ttc_threshold)})

    times, speeds, gaps = [], [], []
    replay_ego, replay_tgt = [], []
    min_ttc, min_gap, is_collision, brake_steps = float("inf"), float("inf"), False, 0

    with silence_stdio():
        env = EsminiEnv(scenario=scenario, road=road, dt=0.05)
        obs = env.reset(ego_x=10.0, ego_y=0.0, ego_yaw=0.0, ego_v=14.0)
        controller.reset()
        for _ in range(400):
            action = controller.step(obs)
            if action["target_a"] < -0.5:
                brake_steps += 1
            obs, done, _info = env.step(action)
            t = obs["sim_time"]
            ego = obs["ego"]
            times.append(t)
            speeds.append(ego["v"])
            replay_ego.append({"x": round(ego["x"], 2), "y": round(ego.get("y", 0.0), 2),
                               "speed": round(ego["v"], 2)})
            tgts = obs.get("targets", [])
            gap_step = None
            if tgts:
                tgt = tgts[0]
                replay_tgt.append({"x": round(tgt["x"], 2), "y": round(tgt.get("y", 0.0), 2),
                                   "speed": round(tgt["v"], 2)})
                rel_d = abs(tgt["x"] - ego["x"]) - 4.5
                gap_step = rel_d
                min_gap = min(min_gap, rel_d)
                rel_v = ego["v"] - tgt["v"]
                if rel_v > 0.1:
                    min_ttc = min(min_ttc, rel_d / rel_v)
                if rel_d < 0.5:
                    is_collision = True
            gaps.append(gap_step)
            if done or is_collision:
                break
        env.close()

    return {
        "times": times, "speeds": speeds, "gaps": gaps,
        "replay_ego": replay_ego, "replay_tgt": replay_tgt,
        "min_ttc": None if min_ttc == float("inf") else round(min_ttc, 2),
        "min_gap": round(min_gap, 2),
        "collision": bool(is_collision),
        "brake_steps": brake_steps,
        "n_steps": len(times),
    }


def a1_baseline():
    if "a1" not in _CACHE:
        _CACHE["a1"] = run_a1_lite(3.0)
    return _CACHE["a1"]


def interpret_a1(res):
    if res["collision"]:
        return ("发生了碰撞（间距 <0.5m）：刹车介入太晚。把 TTC 阈值调大（更早刹车），"
                "再看碰撞能不能消除。")
    return (f"没有碰撞。最小 TTC {res['min_ttc']}s，最小间距 {res['min_gap']}m，"
            f"刹车介入 {res['brake_steps']} 步。"
            "阈值越大刹车越早、越安全，但也越容易‘没危险却刹车’——"
            "试着找到‘刚好不撞’的最小阈值（本实验把间距 <0.5m 记为碰撞）。")


# ---------------------------------------------------------------- B2
_B2_DIR = None


def _b2_network():
    """生成一次 SUMO 路网与路由（需求固定），之后只改信号配时。"""
    global _B2_DIR
    if _B2_DIR is not None:
        return _B2_DIR
    import subprocess
    workdir = tempfile.mkdtemp(prefix="b2_lite_")
    subprocess.run(
        ["netgenerate", "--grid", "--grid.x-number=3", "--grid.y-number=3",
         "--grid.length=400", "--tls.set", "B1",
         "--output-file=grid.net.xml"],
        cwd=workdir, capture_output=True, text=True, check=True)
    lines = ["<routes>\n",
             '  <vType id="car" accel="2.5" decel="4.5" maxSpeed="15" length="5" minGap="2.5"/>\n',
             '  <route id="r_we" edges="B0B1 B1B2"/>\n',
             '  <route id="r_ew" edges="B2B1 B1B0"/>\n',
             '  <route id="r_ns" edges="A1B1 B1C1"/>\n',
             '  <route id="r_sn" edges="C1B1 B1A1"/>\n']
    vid = 0
    t = 0.0
    while t < 300:  # EW：每 6 秒一辆/方向
        for route in ["r_we", "r_ew"]:
            lines.append(f'  <vehicle id="v{vid}" type="car" route="{route}" '
                         f'depart="{t:.1f}" departPos="50" departSpeed="10"/>\n')
            vid += 1
        t += 6.0
    t = 0.0
    while t < 300:  # NS：每 24 秒一辆/方向
        for route in ["r_ns", "r_sn"]:
            lines.append(f'  <vehicle id="v{vid}" type="car" route="{route}" '
                         f'depart="{t:.1f}" departPos="50" departSpeed="10"/>\n')
            vid += 1
        t += 24.0
    lines.append("</routes>\n")
    with open(os.path.join(workdir, "routes.rou.xml"), "w") as f:
        f.writelines(lines)
    _B2_DIR = workdir
    return workdir


def _b2_run(ew_green, ns_green, tag):
    """一次真 TraCI 仿真，返回（平均延误秒，平均排队辆，完成车辆数）。"""
    import xml.etree.ElementTree as ET
    os.environ["SUMO_HOME"] = "/usr/share/sumo"
    workdir = _b2_network()
    tripfile = os.path.join(workdir, f"trip_{tag}.xml")
    cfg = ("\n".join([
        "<configuration>",
        f'<input><net-file value="{workdir}/grid.net.xml"/>'
        f'<route-files value="{workdir}/routes.rou.xml"/></input>',
        '<time><begin value="0"/><end value="600"/><step-length value="1.0"/></time>',
        f'<output><tripinfo-output value="{tripfile}"/></output>',
        "</configuration>"]))
    with open(os.path.join(workdir, "sumo.sumocfg"), "w") as f:
        f.write(cfg)

    with silence_stdio():
        import traci
        from traci import trafficlight
        traci.start(["sumo", "-c", os.path.join(workdir, "sumo.sumocfg"),
                     "--no-warnings", "--no-step-log", "--seed", "42"])
        orig = traci.trafficlight.getCompleteRedYellowGreenDefinition("B1")[0]
        new_phases = []
        for i, ph in enumerate(orig.phases):
            dur = ph.duration
            if i == 0:
                dur = float(ew_green)
            elif i == 2:
                dur = float(ns_green)
            new_phases.append(trafficlight.Phase(dur, ph.state, ph.minDur, ph.maxDur))
        traci.trafficlight.setCompleteRedYellowGreenDefinition(
            "B1", trafficlight.Logic("custom", 0, 0, new_phases))
        queue_samples = []
        for step in range(600):
            traci.simulationStep()
            if step % 20 == 0:
                q = sum(traci.lane.getLastStepHaltingNumber(lane)
                        for lane in traci.trafficlight.getControlledLanes("B1"))
                queue_samples.append(q)
        traci.close()

    tree = ET.parse(tripfile)
    waits = [float(t.get("waitingTime", 0)) for t in tree.getroot().iter("tripinfo")]
    return {
        "avg_wait": round(sum(waits) / max(1, len(waits)), 1),
        "avg_queue": round(sum(queue_samples) / max(1, len(queue_samples)), 1),
        "n_done": len(waits),
    }


def run_b2_lite(ew_green):
    """东西向绿灯时长滑杆（南北向 = 54 - 东西向，周期 60s、黄灯各 3s）。
    返回固定配时 / 学生配时 / 流量比例配时三组真仿真结果。"""
    ew_green = int(ew_green)
    ns_green = 54 - ew_green
    if "b2_fixed" not in _CACHE:
        _CACHE["b2_fixed"] = _b2_run(27, 27, "fixed")
    if "b2_prop" not in _CACHE:
        _CACHE["b2_prop"] = _b2_run(43, 11, "prop")
    student = _b2_run(ew_green, ns_green, "student")
    return {"fixed": _CACHE["b2_fixed"], "student": student,
            "proportional": _CACHE["b2_prop"],
            "ew_green": ew_green, "ns_green": ns_green}


def interpret_b2(res):
    f, s = res["fixed"], res["student"]
    pct = (f["avg_wait"] - s["avg_wait"]) / f["avg_wait"] * 100 if f["avg_wait"] else 0
    direction = "减少" if pct >= 0 else "增加"
    return (f"你的配时（东西向 {res['ew_green']}s / 南北向 {res['ns_green']}s）："
            f"平均延误 {s['avg_wait']}s，固定配时是 {f['avg_wait']}s，"
            f"延误{direction}了 {abs(pct):.1f}%。东西向车多（600 辆/小时对 150 辆），"
            "绿灯向车多的方向倾斜一般更划算——但倾斜过头，南北向就会排长队。"
            "试着找到延误最小的那个绿灯时长。")


# ---------------------------------------------------------------- C1
def run_c1_lite(vnum, extra_kg, drag_coef):
    """FASTSim 单车 UDDS：额外载重 + 风阻系数 -> 百公里电耗。
    注意：改完 glider_kg 必须调 set_veh_mass() 重新汇总整车质量，
    否则仿真仍用旧质量（实测：只改 glider 不调 set_veh_mass，能耗纹丝不动）。"""
    from fastsim.vehicle import Vehicle, DEFAULT_VEH_DB
    veh = Vehicle.from_file(DEFAULT_VEH_DB, vnum=int(vnum))
    veh.glider_kg = float(veh.glider_kg) + float(extra_kg)
    veh.drag_coef = float(drag_coef)
    veh.set_veh_mass()
    try:
        from common.fastsim_helper import run_udds
    except ImportError:  # pragma: no cover
        from .fastsim_helper import run_udds
    out = run_udds(int(vnum), "udds", veh=veh, apply_chained_battery=False)
    return {"kwh_per_100km": round(float(out["kwh_per_100km"]), 2)}


def c1_baseline(vnum, base_drag):
    key = ("c1", vnum)
    if key not in _CACHE:
        _CACHE[key] = run_c1_lite(vnum, 0, base_drag)
    return _CACHE[key]


def interpret_c1(base_kwh, student_kwh):
    pct = (student_kwh - base_kwh) / base_kwh * 100 if base_kwh else 0
    direction = "增加" if pct >= 0 else "减少"
    return (f"百公里电耗从 {base_kwh} 度变成 {student_kwh} 度，{direction}了 {abs(pct):.1f}%。"
            "车越重、风阻越大，电耗越高；城市工况频繁加减速时，车重的影响尤其明显。"
            "试一试：只加 200kg 载重，和只把风阻从 0.29 调到 0.35，哪个更费电？")


# ---------------------------------------------------------------- D1
def run_d1_lite(c_rate):
    """PyBaMM SPM + Chen2020：恒流放电，倍率滑杆 -> 电压-容量曲线。"""
    import pybamm
    model = pybamm.lithium_ion.SPM()
    param = pybamm.ParameterValues("Chen2020")
    exp = pybamm.Experiment([f"Discharge at {c_rate} C until 3V"])
    sim = pybamm.Simulation(model, parameter_values=param, experiment=exp)
    with silence_stdio():
        sim.solve()
    sol = sim.solution
    cap = np.asarray(sol["Discharge capacity [A.h]"].entries, dtype=float)
    volt = np.asarray(sol["Terminal voltage [V]"].entries, dtype=float)
    return {"cap": cap, "volt": volt, "capacity": round(float(cap[-1]), 3),
            "c_rate": float(c_rate)}


def d1_baseline():
    if "d1" not in _CACHE:
        _CACHE["d1"] = run_d1_lite(1.0)
    return _CACHE["d1"]


def interpret_d1(base_cap, res):
    pct = (res["capacity"] - base_cap) / base_cap * 100 if base_cap else 0
    return (f"{res['c_rate']}C 放出的容量是 {res['capacity']} Ah，"
            f"1C 是 {base_cap} Ah（变化 {pct:+.1f}%）。"
            "倍率越高，能放出的电越少、电压平台越低——这就是倍率效应："
            "大电流下电池内阻极化更大，还没放完电压就先跌到了截止电压。"
            "下一门 D2 会专门量化这个效应。")


# ---------------------------------------------------------------- E3
def _e3_controller_class():
    import casadi as ca
    try:
        from common.controller import BaseController
    except ImportError:  # pragma: no cover
        from .controller import BaseController

    class LiteMPCController(BaseController):
        """CasADi + IPOPT MPC 跟驰（源自 E3 基础版格 7；期望间距按滑杆 headway 计算）。"""

        def __init__(self, config=None):
            super().__init__(config)
            self.N = 10
            self.dt_mpc = 0.2
            self.headway = float(self.config.get("headway", 1.0))
            self.Q_gap = float(self.config.get("Q_gap", 1.0))
            self.Q_v = float(self.config.get("Q_v", 0.5))
            self.R = float(self.config.get("R", 0.1))
            self.a_min, self.a_max = -3.0, 2.0
            self._build_optimizer()
            self._last_u = 0.0
            self._steps_since_solve = 999
            self.solve_times_ms = []

        def _build_optimizer(self):
            N, dt = self.N, self.dt_mpc
            opti = ca.Opti()
            X = opti.variable(2, N + 1)
            U = opti.variable(1, N)
            x0 = opti.parameter(2)
            lead = opti.parameter(2, N + 1)
            for k in range(N):
                opti.subject_to(X[:, k + 1] == X[:, k] + dt * ca.vertcat(X[1, k], U[0, k]))
            opti.subject_to(X[:, 0] == x0)
            opti.subject_to(opti.bounded(self.a_min, U, self.a_max))
            opti.subject_to(X[1, :] >= 0)
            cost = 0
            for k in range(N + 1):
                gap = lead[0, k] - X[0, k] - 4.5
                gap_des = X[1, k] * self.headway + 2.0
                gap_err = gap - gap_des
                v_err = X[1, k] - lead[1, k]
                cost += self.Q_gap * gap_err ** 2 + self.Q_v * v_err ** 2
            for k in range(N):
                cost += self.R * U[0, k] ** 2
            opti.minimize(cost)
            # 添加 ipopt.sb='yes' 消除开源许可证 Banner 打印
            opts = {"print_time": False, "ipopt.print_level": 0, "ipopt.sb": "yes",
                    "ipopt.tol": 1e-4, "ipopt.max_iter": 50}
            opti.solver("ipopt", opts)
            self.opti, self.X, self.U = opti, X, U
            self.p_x0, self.p_lead = x0, lead

        def _solve_mpc(self, ego_x, ego_v, lead_x, lead_v):
            import time
            N, dt = self.N, self.dt_mpc
            lead_pred = np.zeros((2, N + 1))
            for k in range(N + 1):
                lead_pred[0, k] = lead_x + lead_v * k * dt
                lead_pred[1, k] = lead_v
            self.opti.set_value(self.p_x0, [ego_x, ego_v])
            self.opti.set_value(self.p_lead, lead_pred)
            t0 = time.time()
            try:
                sol = self.opti.solve()
                a_opt = float(sol.value(self.U[0, 0]))
                self.opti.set_initial(self.X, sol.value(self.X))
                self.opti.set_initial(self.U, sol.value(self.U))
            except RuntimeError:
                a_opt = self._last_u
            self.solve_times_ms.append((time.time() - t0) * 1000)
            self._last_u = a_opt
            return a_opt

        def reset(self):
            self._last_u = 0.0
            self._steps_since_solve = 999
            self.solve_times_ms = []

        def step(self, observation):
            ego = observation["ego"]
            targets = observation.get("targets", [])
            sim_dt = observation.get("dt", 0.05)
            self._steps_since_solve += 1
            if self._steps_since_solve * sim_dt >= self.dt_mpc or not targets:
                if targets:
                    lead = min(targets, key=lambda t: abs(t["x"] - ego["x"]))
                    a = self._solve_mpc(ego["x"], ego["v"], lead["x"], lead["v"])
                else:
                    a = 1.0
                self._steps_since_solve = 0
            else:
                a = self._last_u
            return {"target_a": float(np.clip(a, self.a_min, self.a_max)),
                    "steer_angle": 0.0}

    return LiteMPCController


def run_e3_lite(headway):
    """MPC 真求解 + 纯运动学验证（10 秒）：跟驰时距滑杆 -> 间距误差。
    前车在第 3-5 秒减速到 10 m/s（模拟真实扰动），其余时间 14 m/s 匀速。"""
    headway = float(headway)
    controller = _e3_controller_class()(config={"headway": headway, "Q_gap": 1.0,
                                                "Q_v": 0.5, "R": 0.1})
    controller.reset()
    ego_x, ego_v = 0.0, 14.0
    lead_x = 14.0 * headway + 2.0 + 4.5
    dt = 0.05
    times, gap_errs, accels = [], [], []
    max_err, collision = 0.0, False
    for step in range(200):
        t_now = step * dt
        lead_v = 10.0 if 3.0 <= t_now < 5.0 else 14.0
        obs = {"ego": {"x": ego_x, "v": ego_v},
               "targets": [{"x": lead_x, "v": lead_v}], "dt": dt}
        a = controller.step(obs)["target_a"]
        ego_x += ego_v * dt
        ego_v = max(0.0, ego_v + a * dt)
        lead_x += lead_v * dt
        gap = lead_x - ego_x - 4.5
        err = abs(gap - (ego_v * headway + 2.0))
        max_err = max(max_err, err)
        if gap < 0.5:
            collision = True
            break
        times.append(step * dt)
        gap_errs.append(err)
        accels.append(a)
    avg_solve = float(np.mean(controller.solve_times_ms)) if controller.solve_times_ms else 0.0
    return {"times": times, "gap_errs": gap_errs, "accels": accels,
            "max_err": round(max_err, 3), "collision": bool(collision),
            "avg_solve_ms": round(avg_solve, 1), "n_solves": len(controller.solve_times_ms),
            "headway": headway}


def e3_baseline():
    if "e3" not in _CACHE:
        _CACHE["e3"] = run_e3_lite(1.0)
    return _CACHE["e3"]


def interpret_e3(res):
    base = e3_baseline()
    return (f"时距 {res['headway']}s：最大间距误差 {res['max_err']}m"
            f"（时距 1.0s 的基线是 {base['max_err']}m），"
            f"碰撞={res['collision']}，MPC 平均求解 {res['avg_solve_ms']}ms。"
            "时距是‘跟多远’：时距越大越安全、但跟车越松、道路利用率越低；"
            "前车在第 3-5 秒会减速到 10 m/s：时距太小，扰动一来误差就放大；"
            "时距太大，跟车又松。试着找到误差最小又不撞的时距。")


# ---------------------------------------------------------------- 通用可视化与打卡
def plot_curves(series, xlabel, ylabel, title, figsize=(10, 4)):
    """series: [(x, y, label, style), ...]，画对比曲线（全面支持高清晰度中文字体）。"""
    fig, ax = plt.subplots(figsize=figsize)
    for x, y, label, style in series:
        ax.plot(x, y, style, label=label, linewidth=2.2)
    ax.set_xlabel(xlabel, fontsize=10.5)
    ax.set_ylabel(ylabel, fontsize=10.5)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(frameon=True, facecolor="#f8fafc", framealpha=0.9)
    plt.tight_layout()
    return fig


def plot_bars(labels, values, ylabel, title, figsize=(8, 4)):
    """柱状对比图（带高对比度色带与数值标签）。"""
    fig, ax = plt.subplots(figsize=figsize)
    colors = ["#94a3b8", "#2563eb", "#16a34a"] if len(labels) == 3 else ["#94a3b8", "#2563eb"]
    bars = ax.bar(labels, values, color=colors[:len(labels)], width=0.5)
    ax.set_ylabel(ylabel, fontsize=10.5)
    ax.set_title(title, fontsize=12, fontweight="bold")
    for b in bars:
        h = b.get_height()
        ax.text(b.get_x() + b.get_width() / 2, h + 0.1,
                f"{h:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    plt.tight_layout()
    return fig


def render_lite_metric_card(exp: str, badge_text: str, badge_color: str, metrics_list: list, insight: str):
    """生成具有统一工业质感的富文本 HTML 指标卡与物理增量解读"""
    from IPython.display import HTML

    badge_bg = "#dcfce7" if badge_color == "green" else ("#fee2e2" if badge_color == "red" else "#fef3c7")
    badge_fg = "#15803d" if badge_color == "green" else ("#b91c1c" if badge_color == "red" else "#b45309")

    metrics_html = "".join([
        f'<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 12px; margin: 4px; min-width: 120px;">'
        f'<div style="font-size: 11px; color: #64748b;">{m[0]}</div>'
        f'<div style="font-size: 14px; font-weight: bold; color: #1e293b;">{m[1]}</div>'
        f'</div>'
        for m in metrics_list
    ])

    card_html = f"""
    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-left: 5px solid {badge_fg}; border-radius: 8px; padding: 14px 16px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.05); font-family: system-ui, sans-serif;">
        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; margin-bottom: 8px;">
            <span style="font-weight: bold; font-size: 14px; color: #0f172a;">📊 {exp} 探索结果即时研判</span>
            <span style="background: {badge_bg}; color: {badge_fg}; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                {badge_text}
            </span>
        </div>
        <div style="display: flex; flex-wrap: wrap; margin: 6px -4px;">
            {metrics_html}
        </div>
        <div style="margin-top: 10px; font-size: 13px; color: #334155; line-height: 1.6; background: #f8fafc; padding: 10px 12px; border-radius: 6px;">
            💡 <b>物理因果与工程解读</b>：<br/>{insight}
        </div>
    </div>
    """
    return HTML(card_html)


def save_lite_record(exp, params, metrics, note=""):
    """新手完成记录：同时写 labs/data/lite/ 与 labs/data/preview_checkins/，不进教师正式成绩册。"""
    os.makedirs(LITE_DIR, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rec = {
        "experiment": exp,
        "mode": "novice_preview",
        "params": params,
        "metrics": metrics,
        "student_insight": note,
        "note": note,
        "timestamp": now_str
    }
    path = os.path.join(LITE_DIR, f"{exp}_lite.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)

    # 统一存入 preview_checkins，打通后续教师面板预习核查
    preview_dir = os.path.expanduser("~/labs/data/preview_checkins")
    try:
        os.makedirs(preview_dir, exist_ok=True)
        p_path = os.path.join(preview_dir, f"{exp}_preview.json")
        with open(p_path + ".tmp", "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        os.replace(p_path + ".tmp", p_path)
    except Exception:
        pass
    return path


def a1_replay(res):
    """A1 新手回放：把 lite 轨迹转成双视角回放器 HTML（俯视 + 斜视角投影）。"""
    try:
        from common.visualizer3d import render_trajectory_replay
    except ImportError:  # pragma: no cover
        from .visualizer3d import render_trajectory_replay
    ego = res["replay_ego"]
    tgt = res["replay_tgt"]
    n = min(len(ego), len(tgt)) if tgt else len(ego)
    ego_d = {"x": [e["x"] for e in ego[:n]],
             "y": [e["y"] for e in ego[:n]],
             "v": [e["speed"] for e in ego[:n]]}
    targets = None
    if tgt:
        targets = [{"name": "目标车（加塞）",
                    "x": [t["x"] for t in tgt[:n]],
                    "y": [t["y"] for t in tgt[:n]],
                    "v": [t["speed"] for t in tgt[:n]]}]
    return render_trajectory_replay(
        t=res["times"][:n], ego=ego_d, targets=targets,
        metrics=None,
        title="A1 新手回放 · Cut-in 加塞",
        subtitle="你调的 TTC 阈值，决定了自车什么时候刹车")
