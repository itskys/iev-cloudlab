"""统一控制器接口 v0.5

仅适用于时序步进式环境（esmini / SUMO）。
FASTSim（向量化）和 PyBaMM（PDE积分）不适用此接口。
"""


class BaseController:
    """学生算法基类。继承并实现 step() 即可接入仿真闭环。"""

    def __init__(self, config: dict = None):
        self.config = config or {}

    def reset(self):
        """每个仿真 Episode 开始时重置内部状态。"""
        pass

    def step(self, observation: dict) -> dict:
        """单步控制决策。

        :param observation: dict, 包含
            - 'ego': {'x','y','yaw','v','a'} 自车状态
            - 'targets': [{'id','x','y','v',...}] 周围目标
            - 'sim_time': float 当前仿真时间 (s)
            - 'dt': float 步长 (s)
        :return: dict, 控制量
            - 纵向: {'target_a': float} (m/s^2) 或 {'throttle','brake'}
            - 横向: {'steer_angle': float} (rad) 或 {'target_yaw_rate'}
        """
        raise NotImplementedError("子类必须实现 step()")


class PIDController(BaseController):
    """示例：简单的 PID 跟车控制器，供学生参考。"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.kp = self.config.get('kp', 1.0)
        self.ki = self.config.get('ki', 0.1)
        self.kd = self.config.get('kd', 0.05)
        self._integral = 0.0
        self._prev_error = 0.0
        self.target_headway = self.config.get('target_headway', 1.5)

    def reset(self):
        self._integral = 0.0
        self._prev_error = 0.0

    def step(self, observation: dict) -> dict:
        ego = observation['ego']
        targets = observation.get('targets', [])
        dt = observation.get('dt', 0.05)

        if not targets:
            return {'target_a': 1.0, 'steer_angle': 0.0}  # 无前车，加速

        # 取最近前车
        lead = min(targets, key=lambda t: abs(t['x'] - ego['x']))
        gap = abs(lead['x'] - ego['x']) - 4.5  # 车长补偿
        desired_gap = ego['v'] * self.target_headway
        error = gap - desired_gap

        self._integral += error * dt
        derivative = (error - self._prev_error) / dt if dt > 0 else 0
        self._prev_error = error

        a = self.kp * error + self.ki * self._integral + self.kd * derivative
        a = max(-4.0, min(2.0, a))  # 限幅

        return {'target_a': a, 'steer_angle': 0.0}
