"""esmini 仿真环境封装 v0.5

解决 BaseController 控制量（加速度/转向角）与
SE_ReportObjectPos（绝对位姿）之间的运动学断层。

内置离散化运动学单车模型（Kinematic Bicycle Model）。
"""

import math
import ctypes
import os


class KinematicBicycleModel:
    """离散化运动学单车模型。"""

    def __init__(self, l_f=1.4, l_r=1.4):
        self.l_f = l_f  # 前轴到质心
        self.l_r = l_r  # 后轴到质心
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.v = 0.0

    def reset(self, x=0.0, y=0.0, yaw=0.0, v=0.0):
        self.x, self.y, self.yaw, self.v = x, y, yaw, v

    def step(self, a: float, delta: float, dt: float):
        """单步积分。

        :param a: 纵向加速度 (m/s^2)
        :param delta: 前轮转向角 (rad)
        :param dt: 步长 (s)
        """
        # 质心侧偏角
        beta = math.atan((self.l_r / (self.l_f + self.l_r)) * math.tan(delta))
        # 状态更新
        self.x += self.v * math.cos(self.yaw + beta) * dt
        self.y += self.v * math.sin(self.yaw + beta) * dt
        self.yaw += (self.v / self.l_r) * math.sin(beta) * dt
        self.v = max(0.0, self.v + a * dt)
        return self.x, self.y, self.yaw, self.v


class EsminiEnv:
    """esmini Gym 风格封装。

    用法：
        env = EsminiEnv(scenario='cutin.xosc', road='cutin.xodr')
        obs = env.reset()
        for _ in range(steps):
            action = controller.step(obs)
            obs, done, info = env.step(action)
        env.close()
    """

    def __init__(self, scenario: str, road: str = None, dt: float = 0.05,
                 lib_path: str = '/opt/esmini/esmini/lib/libesminiLib.so'):
        self.scenario = scenario
        self.road = road
        self.dt = dt
        self.sim_time = 0.0
        self.vehicle = KinematicBicycleModel()

        # 加载 esmini 动态库
        if not os.path.exists(lib_path):
            # 尝试常见路径（实测：库在 bin/ 目录下）
            for p in ['/opt/esmini/esmini/bin/libesminiLib.so',
                      '/opt/esmini/esmini/lib/libesminiLib.so',
                      '/opt/esmini/lib/libesminiLib.so',
                      '/usr/local/lib/libesminiLib.so',
                      './libesminiLib.so']:
                if os.path.exists(p):
                    lib_path = p
                    break
        self._lib = ctypes.CDLL(lib_path)
        self._setup_ctypes()
        self._initialized = False

    def _setup_ctypes(self):
        lib = self._lib
        lib.SE_Init.argtypes = [ctypes.c_char_p, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_int]
        lib.SE_Init.restype = ctypes.c_int
        lib.SE_StepDT.argtypes = [ctypes.c_float]
        lib.SE_StepDT.restype = ctypes.c_int
        lib.SE_Close.restype = None
        # SE_ReportObjectPos(id, timestamp, x, y, z, h, p, r)
        lib.SE_ReportObjectPos.argtypes = [ctypes.c_int, ctypes.c_float,
                                           ctypes.c_float, ctypes.c_float,
                                           ctypes.c_float, ctypes.c_float,
                                           ctypes.c_float, ctypes.c_float]
        # SE_GetObjectState(id, *state) 简化版按需扩展
        lib.SE_GetObjectState.argtypes = [ctypes.c_int,
                                          ctypes.POINTER(ctypes.c_float) * 12]

    def reset(self, ego_x=10.0, ego_y=0.0, ego_yaw=0.0, ego_v=15.0):
        """初始化场景，返回初始观测。"""
        if self._initialized:
            self._lib.SE_Close()
        args = f'--headless --osc {self.scenario}'
        if self.road:
            args += f' --road {self.road}'
        # SE_Init 需要 argc/argv 风格，这里用简化调用
        ret = self._lib.SE_Init(args.encode(), 0, 0, 0, 0)
        if ret != 0:
            raise RuntimeError(f'esmini SE_Init failed: {ret}')
        self._initialized = True
        self.sim_time = 0.0
        self.vehicle.reset(x=ego_x, y=ego_y, yaw=ego_yaw, v=ego_v)
        return self._get_obs()

    def _get_obs(self):
        # 简化观测：实际应从 SE_GetObjectState 读取
        # 这里返回自车状态 + 空目标列表，完整版按需扩展
        return {
            'ego': {'x': self.vehicle.x, 'y': self.vehicle.y,
                    'yaw': self.vehicle.yaw, 'v': self.vehicle.v, 'a': 0.0},
            'targets': [],
            'sim_time': self.sim_time,
            'dt': self.dt,
        }

    def step(self, action: dict):
        """执行单步。

        :param action: {'target_a': float, 'steer_angle': float}
        :return: (obs, done, info)
        """
        a = action.get('target_a', 0.0)
        # 支持 throttle/brake 形式
        if 'throttle' in action or 'brake' in action:
            a = action.get('throttle', 0) * 2.0 - action.get('brake', 0) * 4.0
        delta = action.get('steer_angle', 0.0)

        # 运动学积分
        x, y, yaw, v = self.vehicle.step(a, delta, self.dt)

        # 上报 esmini（id=0 为 Ego，时间戳，x,y,z, 航向角, 俯仰, 翻滚）
        self._lib.SE_ReportObjectPos(0, self.sim_time, x, y, 0.0, yaw, 0.0, 0.0)

        # 推进一步
        self._lib.SE_StepDT(self.dt)
        self.sim_time += self.dt

        obs = self._get_obs()
        obs['ego']['a'] = a
        done = False  # 可根据场景结束条件扩展
        info = {}
        return obs, done, info

    def close(self):
        if self._initialized:
            self._lib.SE_Close()
            self._initialized = False
