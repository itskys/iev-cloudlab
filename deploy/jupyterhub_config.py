# IEV CloudLab — jupyterhub_config.py（DockerSpawner 单机版）
# 落点：设计文档 §5 Step 3（6 条防坑铁律）
import os
import sys
from tornado.web import StaticFileHandler

# 自研认证模块与模板挂在 /srv/jupyterhub，需进 sys.path
sys.path.insert(0, "/srv/jupyterhub")

# ---------- 品牌资产：Logo/Favicon/OG 图片静态服务 ----------
# 访问路径：/hub/assets/<文件名>（如 /hub/assets/logo-navbar.png）
c.JupyterHub.extra_handlers = [
    (r"/assets/(.*)", StaticFileHandler, {"path": "/srv/jupyterhub/assets"}),
]

# ---------- 认证：邮箱验证码（无密码登录） ----------
# 登录页只显示空邮箱输入框，不预置任何地址（防垃圾邮件收割）；
# 验证码经 Gmail SMTP 发送，10 分钟有效，一次性，限流。
c.JupyterHub.authenticator_class = "otp_authenticator.EmailOTPAuthenticator"
c.EmailOTPAuthenticator.allowed_emails = {
    "beabaed@gmail.com": "admin",  # 管理员
    "itskys@gmail.com": "teacher",  # 教师
}
c.EmailOTPAuthenticator.allowed_domains = [
    "zhjpec.edu.cn",  # 学生域：用户名取 @ 前本地部分
]
c.EmailOTPAuthenticator.smtp_user = "itskys@gmail.com"  # 发件人（待用户确认）
c.EmailOTPAuthenticator.smtp_password_file = "/srv/jupyterhub/.smtp-password"
c.JupyterHub.template_paths = ["/srv/jupyterhub/templates"]
# OTP 的 authenticate() 只对验证通过的允许邮箱返回用户名，故可全放行
c.Authenticator.allow_all = True
c.Authenticator.admin_users = {"admin"}

# ---------- Spawner ----------
c.JupyterHub.spawner_class = "dockerspawner.DockerSpawner"
c.DockerSpawner.image = "ghcr.io/itskys/iev-base:jazzy-24.04"
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

# ---------- spawn超时修复（2026-10-19）：镜像5GB启动慢 ----------
c.Spawner.http_timeout = 120
c.Spawner.start_timeout = 120
c.JupyterHub.hub_connect_ip = 'jupyterhub'
