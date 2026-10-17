# IEV CloudLab

《智能电动汽车云仿真实验平台》（Intelligent Electric Vehicle Cloud Simulation Laboratory）

面向汽车专业大学生的云端一体化教学仿真平台：浏览器访问，从任一模块开始——选车型、加传感器、写算法、换路况，全部在云端仿真验证。算力按需弹性：1 人测试到 100 人课堂，零重新部署。

## 仓库结构

```
docker/                  # 镜像定义（GitHub Actions 构建 → GHCR）
  iev-base.Dockerfile    # CPU 基础镜像：Ubuntu 24.04 + ROS 2 Jazzy + 仿真 CPU 栈
deploy/                  # 单机部署文件（JupyterHub Compose 配置等）
labs/                    # 课程实验脚手架
  ad2026/                #   自动驾驶实验：cut-in 场景生成等
LICENSES/                # 第三方组件版权声明与许可证文本（合规）
```

## 镜像

| 镜像 | 内容 | 用途 |
|---|---|---|
| `ghcr.io/itskys/iev-base:jazzy-24.04` | Ubuntu 24.04, ROS 2 Jazzy, esmini 3.10.0, SUMO, CARLA wheel 0.9.16, FASTSim 2.1.5（独立 py310 kernel）, PyBaMM, FMPy, f1tenth_gym | JupyterHub 单用户容器（VPS） |

构建：push 到 `main` 自动触发 `.github/workflows/build-images.yml`（约 30–60 分钟）。

## 文档

完整设计见《IEV CloudLab详细设计方案和开发指南》（v2.4 终极封版施工图）。
