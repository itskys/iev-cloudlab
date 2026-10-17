# IEV CloudLab — iev-base：CPU 基础镜像（JupyterHub 单用户容器用）
# Ubuntu 24.04 + ROS 2 Jazzy + 仿真 CPU 栈 + FASTSim 独立 kernel
# 构建：GitHub Actions → ghcr.io/<owner>/iev-base:jazzy-24.04
# 版本锁见《IEV CloudLab详细设计方案和开发指南》§2.3

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    ROS_DISTRO=jazzy

# ---------- 0. 基础工具 ----------
RUN apt update && apt install -y --no-install-recommends \
      locales curl gnupg2 lsb-release software-properties-common \
      ca-certificates git wget unzip \
      build-essential pkg-config \
      python3-pip python3-venv python3-dev \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

# ---------- 1. ROS 2 Jazzy ----------
RUN curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
      -o /usr/share/keyrings/ros-archive-keyring.gpg \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
      > /etc/apt/sources.list.d/ros2.list \
 && apt update && apt install -y --no-install-recommends \
      ros-jazzy-ros-base \
      ros-jazzy-foxglove-bridge \
      python3-colcon-common-extensions \
 && rm -rf /var/lib/apt/lists/*

# ---------- 2. 系统库 ----------
# libomp5/libpng16-16：carla==0.9.16 wheel 依赖
# libgl1/libxrandr2/libxinerama1：esmini 二进制即使 --headless 也要链接（2026-10-17 VPS 实测）
RUN apt update && apt install -y --no-install-recommends \
      libomp5 libpng16-16 \
      libgl1 libxrandr2 libxinerama1 \
      sumo sumo-tools \
 && rm -rf /var/lib/apt/lists/*

# ---------- 3. Python 包 ----------
# numpy/scipy 必须 pin 1.x：scenariogeneration 0.9.3 与 numpy 2.x 不兼容（实测）
RUN pip install --no-cache-dir \
      "numpy==1.26.4" "scipy==1.13.1" \
      "scenariogeneration==0.9.3" \
      "carla==0.9.16" \
      pybamm fmpy \
      "jupyterhub==5.5.3" ipykernel

# f1tenth_gym（MIT，源码安装）
RUN pip install --no-cache-dir git+https://github.com/f1tenth/f1tenth_gym.git

# ---------- 4. esmini v3.10.0 预编译包 ----------
RUN mkdir -p /opt/esmini && cd /opt/esmini \
 && wget -q https://github.com/esmini/esmini/releases/download/v3.10.0/esmini-bin_Linux.zip \
 && unzip -q -o esmini-bin_Linux.zip && rm esmini-bin_Linux.zip
ENV PATH="/opt/esmini/esmini/bin:${PATH}"

# ---------- 5. FASTSim 2.1.5 独立 Python 3.10 kernel（uv 隔离） ----------
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN uv python install 3.10 \
 && uv venv --python 3.10 /opt/envs/py310-fastsim \
 && uv pip install --python /opt/envs/py310-fastsim/bin/python \
      "fastsim==2.1.5" ipykernel \
 && /opt/envs/py310-fastsim/bin/python -m ipykernel install \
      --name py310-fastsim --display-name "Python 3.10 (FASTSim)"

# ---------- 6. FastDDS 强制 UDPv4 配置 ----------
COPY deploy/fastdds_udp.xml /opt/ievlab/fastdds_udp.xml
ENV FASTRTPS_DEFAULT_PROFILES_FILE=/opt/ievlab/fastdds_udp.xml

# ---------- 7. jovyan 用户（把 ubuntu:24.04 内置的 ubuntu(UID 1000) 改名） ----------
RUN usermod -l jovyan ubuntu \
 && groupmod -n jovyan ubuntu \
 && usermod -d /home/jovyan -m jovyan \
 && echo "source /opt/ros/jazzy/setup.bash" >> /home/jovyan/.bashrc \
 && chown -R jovyan:jovyan /home/jovyan

USER jovyan
WORKDIR /home/jovyan
CMD ["jupyterhub-singleuser"]
