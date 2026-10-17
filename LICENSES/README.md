# LICENSES

本目录存放打包进 Docker 镜像的第三方开源组件的版权声明与许可证文本。

合规背景见《开源许可证核查报告_20261017.md》（31 项全量实测）：

- **Permissive（MIT / Apache-2.0 / BSD）**：保留版权声明即可（CARLA、Autoware、FASTSim、PyBaMM、FMPy、JupyterHub 等）。
- **弱 copyleft（MPL-2.0 / EPL-2.0）**：保留声明 + 注明上游源码地址（esmini、scenariogeneration、SUMO、OSI）。
- **GPL-3.0（OpenModelica / OMSimulator）**：随镜像分发，需法务确认合规路径（见核查报告第四节）。
- **CC BY-NC（AWSIM 素材）**：仅教学科研使用，存于私有盘，不再分发。

每个组件一个子目录：`<组件名>/` 内含 `NOTICE`（版权声明）与 `LICENSE`（许可证原文）。
