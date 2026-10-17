# IEV CloudLab — jupyterhub_config.py（DockerSpawner 单机版）
# 落点：设计文档 §5 Step 3（6 条防坑铁律）
import os
import sys

# ---------- 铁律6：认证（默认 PAM 在容器内无系统账号，必须换掉） ----------
c.JupyterHub.authenticator_class = "nativeauthenticator.NativeAuthenticator"
c.NativeAuthenticator.open_signup = False  # 关闭公开注册，由管理员预建账号
c.Authenticator.admin_users = {"admin"}    # TODO: 改成实际管理员用户名

# ---------- Spawner ----------
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
# TODO: 把 <org> 换成实际 GHCR 组织名
c.DockerSpawner.image = "ghcr.io/<org>/iev-base:jazzy-24.04"
# 铁律3：容器停止即删除壳，防 409 Conflict
c.DockerSpawner.remove = True
# 铁律4：与 Hub 同一自定义网络，防 504
c.DockerSpawner.network_name = "ievlab_net"
c.DockerSpawner.mem_limit = "2G"
c.DockerSpawner.cpu_limit = 1.0
# 铁律4b：/dev/shm 512m，防 Gazebo/Rerun SIGBUS
c.DockerSpawner.extra_host_config = {"shm_size": "512m"}
# 用户卷：dict 形式 mode="z" 即 docker CLI 的 :z（SELinux 共享标签，已验 dockerspawner 14.x 源码）
c.DockerSpawner.volumes = {
    "/opt/ievlab/home/{username}": {"bind": "/home/jovyan", "mode": "z"},
}

# ---------- 铁律5：pre_spawn_hook 修用户目录属主 ----------
# （jupyterhub.yml 已把 /opt/ievlab/home 挂进 Hub 容器，这里操作的是宿主机同一目录）
def _ensure_home(spawner):
    d = f"/opt/ievlab/home/{spawner.user.name}"
    os.makedirs(d, exist_ok=True)
    os.system(f"chown 1000:1000 {d}")

c.DockerSpawner.pre_spawn_hook = _ensure_home

# ---------- idle-culler：1200s 空闲回收 ----------
c.JupyterHub.services = [
    {
        "name": "idle-culler",
        "admin": True,
        "command": [
            sys.executable, "-m", "jupyterhub_idle_culler",
            "--timeout=1200",
        ],
    }
]
