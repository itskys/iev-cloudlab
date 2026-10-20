"""
车辆参数库 - 打通"车型设计链" D → C → A

数据流：
  D1 (PyBaMM) → labs/data/batteries/*.csv (OCV-SOC曲线)
       ↓ BatteryFASTSimAdapter
  C1 (FASTSim) → labs/data/vehicles/*.yaml (整车参数)
       ↓
  A1/A2 (esmini) ← 读取车辆参数用于Ego动力学

文件格式：
  batteries/*.csv: soc,ocv_v,max_discharge_pwr_kw,max_charge_pwr_kw,coulombic_eff
  vehicles/*.yaml: mass_kg, drag_coefficient, frontal_area_m2, 等
"""
import os
import csv
import yaml

DATA_ROOT = os.path.join(os.path.dirname(__file__), '..', 'data')
BATTERY_DIR = os.path.join(DATA_ROOT, 'batteries')
VEHICLE_DIR = os.path.join(DATA_ROOT, 'vehicles')
RESULTS_DIR = os.path.join(DATA_ROOT, 'results')


def list_batteries():
    """列出可用的电池数据文件"""
    if not os.path.exists(BATTERY_DIR):
        return []
    return [f for f in os.listdir(BATTERY_DIR) if f.endswith('.csv')]


def list_vehicles():
    """列出可用的车辆参数文件"""
    if not os.path.exists(VEHICLE_DIR):
        return []
    return [f for f in os.listdir(VEHICLE_DIR) if f.endswith('.yaml')]


def load_battery(name):
    """加载电池OCV-SOC曲线，返回dict列表
    
    Args:
        name: 电池名，可带或不带.csv后缀，如 'chen2020_nmc_75ah'
    """
    if not name.endswith('.csv'):
        name = name + '.csv'
    path = os.path.join(BATTERY_DIR, name)
    with open(path) as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_vehicle(name):
    """加载车辆参数，返回dict
    
    Args:
        name: 车辆名，可带或不带.yaml后缀，如 'bev_sedan'
    """
    if not name.endswith('.yaml'):
        name = name + '.yaml'
    path = os.path.join(VEHICLE_DIR, name)
    with open(path) as f:
        return yaml.safe_load(f)


def save_result(experiment_id, data):
    """保存实验结果到标准位置，供下游实验调用
    
    Args:
        experiment_id: 如 'A1_cutin_aeb', 'C1_fastsim_energy'
        data: dict，必须包含 'experiment', 'timestamp', 'metrics'
    """
    import json
    from datetime import datetime
    os.makedirs(RESULTS_DIR, exist_ok=True)
    data['experiment'] = experiment_id
    data['timestamp'] = datetime.now().isoformat()
    path = os.path.join(RESULTS_DIR, f'{experiment_id}.json')
    with open(path, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path


def load_result(experiment_id):
    """加载上游实验的结果"""
    import json
    path = os.path.join(RESULTS_DIR, f'{experiment_id}.json')
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
