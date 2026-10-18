"""esmini 仿真环境封装 v0.5

解决 BaseController 控制量（加速度/转向角）与
SE_ReportObjectPos（绝对位姿）之间的运动学断层。

内置离散化运动学单车模型（Kinematic Bicycle Model）。
"""

import math
import ctypes
import os


class SE_ScenarioObjectState(ctypes.Structure):
    """esmini SE_ScenarioObjectState 结构体（按头文件顺序）"""
    _fields_ = [
        ('id', ctypes.c_int),
        ('model_id', ctypes.c_int),
        ('ctrl_type', ctypes.c_int),
        ('timestamp', ctypes.c_double),
        ('x', ctypes.c_double),
        ('y', ctypes.c_double),
        ('z', ctypes.c_double),
        ('h', ctypes.c_double),
        ('p', ctypes.c_double),
        ('r', ctypes.c_double),
        ('roadId', ctypes.c_uint32),
        ('junctionId', ctypes.c_uint32),
        ('t', ctypes.c_double),
        ('laneId', ctypes.c_int),
        ('laneOffset', ctypes.c_double),
        ('s', ctypes.c_double),
        ('speed', ctypes.c_double),
        # 后续字段省略（我们只需要前面的）
    ]


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
        # 实测：SE_Init/SE_InitWithString 返回 -1，必须用 SE_InitWithArgs
        lib.SE_InitWithArgs.argtypes = [ctypes.c_int,
                                        ctypes.POINTER(ctypes.c_char_p)]
        lib.SE_InitWithArgs.restype = ctypes.c_int
        lib.SE_StepDT.argtypes = [ctypes.c_float]
        lib.SE_StepDT.restype = ctypes.c_int
        lib.SE_Close.restype = None
        lib.SE_GetObjectState.argtypes = [ctypes.c_int,
                                          ctypes.POINTER(SE_ScenarioObjectState)]
        lib.SE_GetObjectState.restype = ctypes.c_int
        lib.SE_GetNumberOfObjects.restype = ctypes.c_int
        # SE_ReportObjectPos(id, timestamp, x, y, z, h, p, r)
        lib.SE_ReportObjectPos.argtypes = [ctypes.c_int, ctypes.c_float,
                                           ctypes.c_float, ctypes.c_float,
                                           ctypes.c_float, ctypes.c_float,
                                           ctypes.c_float, ctypes.c_float]

    def reset(self, ego_x=10.0, ego_y=0.0, ego_yaw=0.0, ego_v=15.0):
        """初始化场景，返回初始观测。"""
        if self._initialized:
            self._lib.SE_Close()
        # 用 SE_InitWithArgs (argc/argv)，实测唯一可用的初始化方式
        # 注意：不传 --road，xosc 文件内已引用 xodr
        arg_list = ['esmini', '--headless', '--osc', self.scenario,
                    '--fixed_timestep', str(self.dt)]
        argv = (ctypes.c_char_p * len(arg_list))(
            *[a.encode() for a in arg_list])
        # 切换到场景文件目录（esmini 用相对路径解析）
        _cwd = os.getcwd()
        scenario_dir = os.path.dirname(os.path.abspath(self.scenario))
        if scenario_dir:
            os.chdir(scenario_dir)
            # argv 中的路径改为相对路径
            arg_list[3] = os.path.basename(self.scenario)
            argv = (ctypes.c_char_p * len(arg_list))(
                *[a.encode() for a in arg_list])
        try:
            ret = self._lib.SE_InitWithArgs(len(arg_list), argv)
        finally:
            os.chdir(_cwd)
        if ret != 0:
            raise RuntimeError(f'esmini SE_InitWithArgs failed: {ret}')
        self._initialized = True
        self.sim_time = 0.0
        self.vehicle.reset(x=ego_x, y=ego_y, yaw=ego_yaw, v=ego_v)
        return self._get_obs()

    def _get_obs(self):
        """从真实 esmini 读取所有车辆状态。"""
        # 自车状态（运动学模型积分，esmini 场景中的 Ego）
        ego_state = {
            'x': self.vehicle.x, 'y': self.vehicle.y,
            'yaw': self.vehicle.yaw, 'v': self.vehicle.v, 'a': 0.0,
        }
        # 从 esmini 读取其他目标车（真实场景数据）
        targets = []
        try:
            n = self._lib.SE_GetNumberOfObjects()
            for i in range(n):
                st = SE_ScenarioObjectState()
                if self._lib.SE_GetObjectState(i, ctypes.byref(st)) == 0:
                    # 跳过自车（id=0 为 Ego，由 SE_ReportObjectPos 控制）
                    if i == 0:
                        continue
                    targets.append({
                        'id': st.id, 'x': st.x, 'y': st.y, 'v': st.speed,
                    })
        except Exception:
            pass  # esmini 未初始化时返回空
        return {
            'ego': ego_state,
            'targets': targets,
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
