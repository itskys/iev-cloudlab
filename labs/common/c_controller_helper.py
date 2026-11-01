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
