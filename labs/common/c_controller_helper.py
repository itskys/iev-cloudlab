"""IEV CloudLab 车规级 C 语言控制器构建与性能评测辅助模块
Automotive Embedded C Controller Helper & Benchmarking Toolkit
"""
import os
import sys
import time
import subprocess
from typing import Dict, Any, Tuple

def compile_c_shared_lib(
    c_source_path: str,
    output_so_path: str = None,
    opt_level: str = "-O2",
    extra_flags: list = None
) -> Tuple[bool, str]:
    """调用系统 GCC 编译器将 C 语言源码编译为车规级动态共享库 (.so)

    :param c_source_path: C 源码路径
    :param output_so_path: 目标 .so 输出路径 (默认在同一目录下生成)
    :param opt_level: 优化等级 (-O0, -O2, -O3)
    :param extra_flags: 额外编译参数 (如 -Wall, -Wextra)
    :return: (是否成功, 编译器输出日志或错误信息)
    """
    if not os.path.isfile(c_source_path):
        return False, f"C source file not found: {c_source_path}"

    if output_so_path is None:
        base, _ = os.path.splitext(c_source_path)
        output_so_path = base + ".so"

    cmd = ["gcc", opt_level, "-shared", "-fPIC"]
    if extra_flags:
        cmd.extend(extra_flags)
    else:
        cmd.extend(["-Wall"])
    cmd.extend([c_source_path, "-o", output_so_path])

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if res.returncode == 0:
            return True, output_so_path
        else:
            return False, f"Compilation failed (code {res.returncode}):\n{res.stderr}"
    except Exception as e:
        return False, f"Failed to invoke GCC: {e}"


def benchmark_controllers(
    py_controller,
    c_controller,
    sample_obs: dict,
    n_iterations: int = 50000
) -> Dict[str, Any]:
    """高精度微秒级对比测试 Python 控制器与 C 原生控制器的执行时延与吞吐率

    :param py_controller: 继承自 BaseController 的 Python 控制器实例
    :param c_controller: 继承自 BaseController 的 C ctypes 封装实例
    :param sample_obs: 用于测试的标准传感器观测字典
    :param n_iterations: 压测循环轮数
    :return: 包含耗时、单步微秒数与提速比的统计字典
    """
    # 1. 预热 (Warm-up)
    for _ in range(100):
        py_controller.step(sample_obs)
        c_controller.step(sample_obs)

    # 2. 测量 Python 单步时延
    t0 = time.perf_counter()
    for _ in range(n_iterations):
        py_controller.step(sample_obs)
    t_py_total = time.perf_counter() - t0
    py_us_per_step = (t_py_total / n_iterations) * 1e6

    # 3. 测量 C 语言原生动态库单步时延
    t0 = time.perf_counter()
    for _ in range(n_iterations):
        c_controller.step(sample_obs)
    t_c_total = time.perf_counter() - t0
    c_us_per_step = (t_c_total / n_iterations) * 1e6

    speedup = py_us_per_step / max(c_us_per_step, 1e-9)

    return {
        "n_iterations": n_iterations,
        "py_total_s": round(t_py_total, 4),
        "py_us_per_step": round(py_us_per_step, 3),
        "c_total_s": round(t_c_total, 4),
        "c_us_per_step": round(c_us_per_step, 3),
        "speedup_ratio": round(speedup, 1),
        "realtime_margin_pct": round((1.0 - (c_us_per_step / 1000.0)) * 100, 2) # 相对于 1ms (1000us) 控制周期的裕度
    }


def record_c_track_achievement(
    experiment_id: str,
    bench_res: dict = None,
    extra_metrics: dict = None,
    results_dir: str = None
) -> bool:
    """自动将车规量产 C 轨认证成果记录至 results/<exp_id>.json，无缝联动教师面板与能力画像。

    :param experiment_id: 实验编号，如 'A1_cutin_aeb'
    :param bench_res: benchmark_controllers 的返回字典
    :param extra_metrics: 额外自定义指标 (如闭环验证结果)
    :param results_dir: 结果目录 (自动探测 /home/jovyan/labs/data/results、labs/data/results 或 results)
    :return: 是否成功保存
    """
    import json
    from datetime import datetime

    candidate_dirs = [
        results_dir,
        os.path.expanduser("~/labs/data/results"),
        "/home/jovyan/labs/data/results",
        os.path.join(os.path.dirname(__file__), "..", "data", "results"),
        "labs/data/results",
        "results",
    ]
    target_dir = None
    for d in candidate_dirs:
        if d and (os.path.isdir(d) or os.path.isdir(os.path.dirname(os.path.abspath(d)))):
            try:
                os.makedirs(d, exist_ok=True)
                target_dir = d
                break
            except OSError:
                continue

    if not target_dir:
        target_dir = "labs/data/results"
        os.makedirs(target_dir, exist_ok=True)

    json_path = os.path.join(target_dir, f"{experiment_id}.json")
    record = {}
    if os.path.isfile(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                record = json.load(f)
        except Exception:
            record = {}

    if "metrics" not in record:
        record["metrics"] = {}

    record["experiment"] = experiment_id
    record["timestamp"] = datetime.now().isoformat()
    record["metrics"]["c_track_verified"] = True
    record["metrics"]["c_track_timestamp"] = record["timestamp"]

    if bench_res:
        record["metrics"]["c_us_per_step"] = bench_res.get("c_us_per_step")
        # 加速比只登记实测值：未实测的课程不写该字段，并清除旧记录中的残留比值，
        # 避免徽章把历史比值当成当次结果展示。
        if bench_res.get("speedup_ratio") is not None:
            record["metrics"]["c_speedup_ratio"] = bench_res.get("speedup_ratio")
        else:
            record["metrics"].pop("c_speedup_ratio", None)
        record["metrics"]["c_realtime_margin_pct"] = bench_res.get("realtime_margin_pct")

    if extra_metrics:
        record["metrics"].update(extra_metrics)

    try:
        tmp_path = json_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, json_path)

        try:
            from IPython.display import display, HTML
            badge_html = f"""
            <div style="background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
                        border: 1.5px solid #6366f1; border-radius: 10px; padding: 14px 18px;
                        margin: 14px 0; color: #f8fafc; font-family: system-ui, sans-serif;
                        box-shadow: 0 4px 16px rgba(99, 102, 241, 0.2);">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 22px;">🎖️</span>
                        <div>
                            <div style="font-weight: 700; font-size: 14px; color: #a5b4fc;">
                                恭喜！已达成【⚡ MISRA-C 车规量产轨认证】
                            </div>
                            <div style="font-size: 12px; color: #94a3b8; margin-top: 2px;">
                                C 原生动态库单步时延: <b style="color: #38bdf8;">{record['metrics'].get('c_us_per_step', '--')} μs</b>
                                (相对 Python 实测比值 <b style="color: #4ade80;">{record['metrics'].get('c_speedup_ratio', '--')}x</b>，1ms 控制裕度 <b style="color: #fbbf24;">{record['metrics'].get('c_realtime_margin_pct', '--')}%</b>)
                            </div>
                        </div>
                    </div>
                    <span style="background: rgba(99, 102, 241, 0.25); border: 1px solid #818cf8; color: #c7d2fe;
                                 padding: 4px 12px; border-radius: 14px; font-size: 12px; font-weight: 700;">
                        +1 分荣誉加分已登记（C 轨累计封顶 +5 分）
                    </span>
                </div>
            </div>
            """
            display(HTML(badge_html))
        except Exception:
            print(f"✓ 车规量产 C 轨认证成功！结果已归档至: {json_path}")
        return True
    except Exception as e:
        print(f"⚠️ 写入 C 轨结果失败: {e}")
        return False

