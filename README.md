# IEV CloudLab · 智能电动汽车云仿真实验平台

> **Release Version**: `v1.0.0` (Production Milestone & Educational Accreditation Ready)  
> **Online Service**: [https://ievlab.aisai.cc](https://ievlab.aisai.cc) (Cloudflare Tunnel 接入)  
> **Docker Base**: `ghcr.io/itskys/iev-base:jazzy-24.04` (Ubuntu 24.04 + ROS 2 Jazzy + esmini + SUMO + FASTSim + PyBaMM + FMPy)  
> **Grading Verification**: 30/30 项自动评分判据全绿通过 (100/100)

---

## 🌟 平台定位与设计哲学

《智能电动汽车云仿真实验平台》（Intelligent Electric Vehicle Cloud Simulation Laboratory）是面向高校汽车工程、智能车辆与自动化专业本科生及研究生打造的**全栈云端一体化仿真教学科研平台**。

平台彻底打破传统汽车仿真软件（MATLAB/Simulink、Carsim 等）高昂商业授权门槛、环境配置复杂以及孤立碎片化教学的困境。学生只需通过现代浏览器（邮箱验证码单点登录），即可在云端即时分配的专属容器算力舱中，从整车选型、电化学电池机理标定、动力总成能耗匹配、自动驾驶纵横向决策控制到车联网 V2X 协同仿真，完成贯通式跨域闭环验证。

---

## 🏗️ 核心架构与功能矩阵

### 1. 课程体系矩阵（8 大基础模块 + 1 项跨域综合大作业）
平台包含 **59 个精心调测的 Jupyter 实验笔记本**（29 个 Base 基础实验 + 29 个 Pro 工业进阶实验 + 1 个 Capstone 终极实验）：

| 模块代号 | 实验领域 | 核心仿真引擎与底层依赖 | 典型实验与工程产出 |
|---|---|---|---|
| **A 模块** | 自动驾驶决策与控制 | `esmini 3.10.0` (OpenSCENARIO) + 运动学闭环 | A1 Cut-in 加塞 AEB、A2 ACC 跟车、A3 增广 TTC、A4 交叉口让行、A5 汇流 |
| **B 模块** | 微观与宏观交通流仿真 | `SUMO 1.20` + `TraCI` | B1 IDM 跟车标定、B2 交叉口信号配时、B3 CACC 编队控制、B4 冲击波物理、B5 绿波带协调 |
| **C 模块** | 新能源动力总成与能耗 | `FASTSim 2.1.5` (py310-fastsim 独立内核) | C1 纯电整车能耗（加载 D3 电池）、C2 混合动力构型、C3 灵敏度正交方差、C4 三种能量管理策略 |
| **D 模块** | 锂电池电化学机理 | `PyBaMM 24.5` (SPM / DFN 机理模型) | D1 1C 单粒子放电、D2 Peukert 倍率衰减拟合、D3 OCV-SOC 标定（导出整车电池库）、D4 析锂物理临界判据 |
| **E 模块** | 优化控制与动态规划 | `CasADi` + `IPOPT` + `pymoo` + Bellman DP | E1 传动比单目标遗传算法、E2 NSGA-II 多目标 Pareto 前沿、E3 MPC 预测跟车、E4 Bellman 能量管理全局最优 (1.92L) |
| **F 模块** | 工业系统模型交换 | `FMPy` (FMI 2.0 Co-Simulation) | F1 FMI 标准架构验证、F2 手工 C 语言 FMU 封装、F3 Jacobi 并行步进多 FMU 协仿真 |
| **G 模块** | 智能汽车操作系统中间件 | `rclpy` (ROS 2 Jazzy) + MiniROS | G1 话题发布/订阅与 QoS 通信机制、G2 服务调用开关 AEB 与动态参数服务器 |
| **H 模块** | 仿真场景工程与模糊测试 | `scenariogeneration` + `esmini` | H1 批量场景矩阵生成与回放验证、H2 50 场景蒙特卡洛模糊测试 (Fuzzing) 探寻算法失效边界 |
| **Capstone** | **多物理场跨域一体化综合实验** | 电池 + 整车能耗 + 纵向跟踪 + 三维孪生 | `Capstone_iev_integrated_pro.ipynb`：D3 标定电池数据注入 FASTSim，联合 ACC 决策闭环，三维数字孪生回放 |

---

### 2. 三条贯穿式工程数据流（打破实验孤岛）
- **链 1 · 车型设计链**：`D3 标定输出的电池 CSV` $	o$ `C1/C2 加载（BatteryFASTSimAdapter）计算整车电耗` $	o$ `车型 YAML 动力学参数` $	o$ `A1–A4 自车动力学模型`。
- **链 2 · 算法开发链**：`common.BaseController` $	o$ `A/B 仿真闭环` $	o$ `提取 TTC/间距误差/PET 等量化指标` $	o$ `参数敏捷迭代调优`。
- **链 3 · 能量管理链**：`E4 动态规划全局理论最优 (1.92L/100km)` 作为标杆 $	o$ `C4 规则型工程策略 (CD/CS/ECMS-like 2.14L/100km)` 对比 $	o$ 深刻理解"理论极限"与"工程可实现性代价"。

---

### 3. 先进工程体验与学习支持中枢
- **7 项核心工程能力画像雷达 (`common.skills_profiler`)**：精准量化学生在电化学机理、整车能耗、控制算法、交通仿真、系统中间件、优化决策、场景工程 7 大维度的掌握度，生成交互式 SVG 能力画像。
- **IEV Copilot 智能助教 (`common.copilot`)**：内嵌机理故障诊断知识库。在学生调参遇到制动碰撞、能耗异常或超调震荡时，自动结合运动学制动距离方程和控制论给出精准物理归因与处方建议。
- **代码时光机 (Time Machine) 快照管理 (`common.snapshot_manager`)**：单实验历史快照无感存储，支持一键查看代码 AST 差异 Diff 并无损回滚。
- **分布式 V2X 车队编队引擎 (`common.v2x_fleet`)**：仿真 5 车 CACC 车队在不同无线时延（40ms）与丢包率下的协同响应，提供网联拓扑与弦稳定性 (String Stability) 频域验证。
- **工业级 OpenSCENARIO 1.1 导出 (`common.xosc_converter`)**：一键将学生在平台生成的轨迹和工况导出为标准 `.xosc` XML，支持直接导入 CARLA/VTD 等工业商用仿真器。
- **三维数字孪生轨迹回放看板 (`common.visualizer3d`)**：基于 Three.js/Canvas 渲染自车与多目标车的相对动态时空轨迹，支持动态鸟瞰俯视图、时速表与跟车雷达动态投影。
- **天梯榜竞技系统 (`benchmarks.leaderboard`)**：在 AEB 制动、SUMO 通行、FASTSim 油耗等关键赛道建立全班天梯榜，激发学生极致调参探索潜能。

---

### 4. 严苛的双轨学术诚信与质量护航体系
- **AST 语法树代码查重引擎 (`common.plagiarism_detector`)**：提取代码抽象语法树骨架，免疫变量更名、注释增删与格式排版混淆，计算 3-Gram Jaccard 相似度并高亮可疑抄袭对。
- **规则型报告数值真值校验器 (`common.report_checker`)**：自动解析学生提交的 Markdown 实验报告，与底层 `results/<exp_id>.json` 真实仿真数据交叉核验，在 5% 容差内判定真伪，彻底拦截假造数据与硬抄手册。
- **百份研报质性评估引擎 (`common.report_evaluator`)**：35% 数据真实性 + 65% 深度质性反思（机理背景、动力学响应、工程权衡），自动生成百分制评分与教师批注。
- **学期一键封存与归档导出 (`common.semester_archiver`)**：支持学生一键导出个人工程作品集 ZIP 包，支持教师一键封存全班成绩、查重报告与能力热力图。

---

## 🛠️ 运维与系统健康机制

| 机制项 | 规格与实现 | 作用 |
|---|---|---|
| **公平分母成绩聚合** | `deploy/collect_grades.py` (分母永久锁定 29 门必做) | 彻底杜绝加入挑战/大作业实验稀释总成绩，保障教务公平性 |
| **容器空闲看门狗** | JupyterHub Culler `3600s` 自动回收 | 确保学生离线后及时释放云端内存与算力资源 |
| **自动化备份守护** | `deploy/backup_and_health.py --backup` (每日凌晨 2:30) | SQLite 数据库、学生数据、日志加密轮转并保留 7 天 |
| **主动式健康自检探针** | `deploy/backup_and_health.py --check` (每小时第 15 分) | 实时监控磁盘空间、JupyterHub 200 探针与数据库 600 文件权限 |

---

## 📚 配套权威文档与教学资源

- **实验教学目录（唯一权威版）**：[notebooks/README.md](file:///Users/christingking/dev/iev-cloudlab/notebooks/README.md)
- **学生快速上手指南**：[student_quickstart.md](file:///Users/christingking/dev/iev-cloudlab/student_quickstart.md)
- **教师指导手册（评分细则与防作弊）**：[notebooks/teacher_guide.md](file:///Users/christingking/dev/iev-cloudlab/notebooks/teacher_guide.md)
- **16周课程教学大纲与学时规划**：[notebooks/syllabus_16weeks.md](file:///Users/christingking/dev/iev-cloudlab/notebooks/syllabus_16weeks.md)
- **自动化评分与判据指南**：[labs/auto_grading_guide.md](file:///Users/christingking/dev/iev-cloudlab/labs/auto_grading_guide.md)
- **10分钟现场教学演示脚本**：[demo_script_10min.md](file:///Users/christingking/dev/iev-cloudlab/demo_script_10min.md)

---

## 📄 许可证与开源合规

- 平台核心代码与实验教材采用 **MIT 许可证** 与 **教学开源许可**。
- 第三方组件与开源引擎（esmini、SUMO、FASTSim、PyBaMM、FMPy、ROS 2 等）遵循其各自原始许可证协议，详见 [LICENSES/](file:///Users/christingking/dev/iev-cloudlab/LICENSES/) 目录合规说明。
