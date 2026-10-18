"""PyBaMM → FASTSim 电池数据适配器 v0.5

CSV 规范（量纲：功率 kW，与 FASTSim 2.1.5 内部一致）：
    battery_pack_<chem>_<capacity>Ah.csv
    soc,ocv_v,max_discharge_pwr_kw,max_charge_pwr_kw,coulombic_eff

数学映射（不侵入 FASTSim 源码）：
1. OCV(SOC) 梯形积分 → 等效能量 → veh.ess_max_kwh
2. max_discharge_pwr_kw → veh.ess_max_kw
3. 充放电损耗最小二乘拟合二次效率多项式
"""

import csv
import numpy as np


class BatteryFASTSimAdapter:
    """PyBaMM 输出 → FASTSim Vehicle 参数映射器。"""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.soc = []
        self.ocv_v = []
        self.max_discharge_kw = []
        self.max_charge_kw = []
        self.coulombic_eff = []
        self._load()

    def _load(self):
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 跳过注释行
                if row['soc'].strip().startswith('#'):
                    continue
                self.soc.append(float(row['soc']))
                self.ocv_v.append(float(row['ocv_v']))
                self.max_discharge_kw.append(float(row['max_discharge_pwr_kw']))
                self.max_charge_kw.append(float(row['max_charge_pwr_kw']))
                self.coulombic_eff.append(float(row['coulombic_eff']))
        self.soc = np.array(self.soc)
        self.ocv_v = np.array(self.ocv_v)
        self.max_discharge_kw = np.array(self.max_discharge_kw)
        self.max_charge_kw = np.array(self.max_charge_kw)
        self.coulombic_eff = np.array(self.coulombic_eff)

    def equivalent_energy_kwh(self, nominal_capacity_ah: float) -> float:
        """OCV(SOC) 梯形积分求等效能量。

        E = ∫ OCV(soc) * Q_nominal * dsoc
        """
        # 梯形积分：∫ ocv_v d(soc) * 容量(Ah) = Wh
        energy_wh = np.trapz(self.ocv_v, self.soc) * nominal_capacity_ah
        return energy_wh / 1000.0  # kWh

    def apply_to_vehicle(self, veh, nominal_capacity_ah: float):
        """将参数映射到 FASTSim Vehicle 对象。

        :param veh: fastsim.vehicle.Vehicle 实例
        :param nominal_capacity_ah: 标称容量 (Ah)，用于能量积分
        """
        veh.ess_max_kwh = self.equivalent_energy_kwh(nominal_capacity_ah)
        veh.ess_max_kw = float(np.max(self.max_discharge_kw))
        # 可选：记录映射信息
        veh._battery_adapter_info = {
            'csv': self.csv_path,
            'ess_max_kwh': veh.ess_max_kwh,
            'ess_max_kw': veh.ess_max_kw,
        }
        return veh

    @staticmethod
    def export_from_pybamm(soc_array, ocv_array, output_path: str,
                           max_discharge_kw: float = 80.0,
                           max_charge_kw: float = 50.0,
                           coulombic_eff: float = 0.99,
                           chem: str = 'NMC', capacity_ah: float = 75.0):
        """从 PyBaMM 仿真结果导出标准 CSV。

        :param soc_array: SOC 数组 (0-1)
        :param ocv_array: 对应 OCV 数组 (V)
        :param output_path: 输出路径（建议按规范命名）
        """
        with open(output_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['soc', 'ocv_v', 'max_discharge_pwr_kw',
                             'max_charge_pwr_kw', 'coulombic_eff'])
            for s, v in zip(soc_array, ocv_array):
                writer.writerow([f'{s:.4f}', f'{v:.2f}',
                                 f'{max_discharge_kw:.1f}',
                                 f'{max_charge_kw:.1f}',
                                 f'{coulombic_eff:.3f}'])
        return output_path
