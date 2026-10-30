"""C1 新手模式 FASTSim 调用桥（CLI）。

背景：FASTSim 引擎住在独立的 Python 3.10 环境（/opt/envs/py310-fastsim），
而新手本的滑杆（ipywidgets）只在主 python3 内核里有。
新手本用 subprocess 调这个脚本跑 FASTSim，结果口径与完整模式一致。

用法：
  /opt/envs/py310-fastsim/bin/python c1_lite_runner.py --vnum 17 --kg 200 --cd 0.35
输出：单行 JSON {"kwh_per_100km": ...}
"""

import argparse
import json
import sys

sys.path.insert(0, "/home/jovyan/labs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vnum", type=int, required=True)
    ap.add_argument("--kg", type=float, default=0.0)
    ap.add_argument("--cd", type=float, required=True)
    args = ap.parse_args()
    from fastsim.vehicle import Vehicle, DEFAULT_VEH_DB
    from common.fastsim_helper import run_udds
    veh = Vehicle.from_file(DEFAULT_VEH_DB, vnum=args.vnum)
    veh.glider_kg = float(veh.glider_kg) + float(args.kg)
    veh.drag_coef = float(args.cd)
    # 必须重新汇总质量：只改 glider 不调 set_veh_mass() 时仿真仍用旧质量（实测）
    veh.set_veh_mass()
    out = run_udds(args.vnum, "udds", veh=veh, apply_chained_battery=False)
    print(json.dumps({"kwh_per_100km": round(float(out["kwh_per_100km"]), 2)}))


if __name__ == "__main__":
    main()
