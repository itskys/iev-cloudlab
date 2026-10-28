"""FASTSim 极简封装层 v0.5

为教学 notebook 提供简洁的 FASTSim 2.x API，避免学生直接面对
Rust 绑定的复杂性。
"""

import numpy as np
import pandas as pd


def load_bev_list():
    """返回车型库中所有纯电车型的 vnum 列表。"""
    from fastsim.vehicle import DEFAULT_VEH_DB
    db = pd.read_csv(DEFAULT_VEH_DB)
    bevs = db[db['veh_pt_type'] == 'BEV']
    return [(int(idx), row.get('veh_year', '?')) for idx, row in bevs.iterrows()]


def run_udds(vnum: int, cycle_name: str = 'udds', veh=None, apply_chained_battery: bool = True) -> dict:
    """跑一条循环工况，返回关键指标。

    :param vnum: 车型编号（见 load_bev_list）
    :param cycle_name: 工况名（'udds' / 'hwfet' / 'us06'）
    :param veh: 自定义 Vehicle 实例（若为 None 则从数据库加载 vnum）
    :param apply_chained_battery: 是否尝试动态加载 D3 电池标定数据（默认开启）
    :return: {'kwh_per_100km': float, 'simdrive': SimDrive, 'vehicle': veh, 'cycle': cyc, 'chain_validation': dict}
    """
    from fastsim.vehicle import Vehicle, DEFAULT_VEH_DB
    from fastsim import cycle
    from fastsim.simdrive import SimDrive

    if veh is None:
        veh = Vehicle.from_file(DEFAULT_VEH_DB, vnum=vnum)
        if apply_chained_battery:
            try:
                from common.chain_validator import load_chained_battery_model
                veh, _ = load_chained_battery_model(veh)
            except Exception:
                try:
                    from .chain_validator import load_chained_battery_model
                    veh, _ = load_chained_battery_model(veh)
                except Exception:
                    pass

    cyc = cycle.Cycle.from_file(cycle_name)
    sd = SimDrive(cyc, veh)
    sd.sim_drive()

    kwh_per_mi = float(np.array(sd.electric_kwh_per_mi).mean())
    kwh_per_100km = kwh_per_mi * 62.137  # mi → 100km

    return {
        'kwh_per_100km': kwh_per_100km,
        'simdrive': sd,
        'vehicle': veh,
        'cycle': cyc,
        'chain_validation': getattr(veh, '_chain_validation', None),
    }


def compare_vehicles(vnums: list, cycle_name: str = 'udds') -> pd.DataFrame:
    """横向对比多款车型。"""
    rows = []
    for vnum in vnums:
        r = run_udds(vnum, cycle_name)
        rows.append({'vnum': vnum,
                     'kwh_per_100km': round(r['kwh_per_100km'], 1)})
    return pd.DataFrame(rows)


def plot_cycle(cycle_name: str = 'udds', ax=None):
    """画工况车速曲线。"""
    import matplotlib.pyplot as plt
    from fastsim import cycle
    cyc = cycle.Cycle.from_file(cycle_name)
    t = np.array(cyc.time_s)
    v = np.array(cyc.mps) * 3.6
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(t, v)
    ax.set_xlabel('时间 (s)')
    ax.set_ylabel('车速 (km/h)')
    ax.set_title(f'{cycle_name.upper()} 工况')
    ax.grid(True, alpha=0.3)
    return ax
