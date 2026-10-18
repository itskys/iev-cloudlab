# IEV CloudLab — 邮箱验证码登录（Passwordless Email OTP）
# 流程：登录页只显示邮箱输入框（不预置任何地址）→ 点"发送验证码" →
# 邮箱在允许列表才真发（Gmail SMTP），否则返回同样的"已发送"提示（防枚举）→
# 输入 6 位码 → 验证通过按映射得用户名。
import json
import re
import secrets
import smtplib
import time
from email.mime.text import MIMEText

from jupyterhub.auth import Authenticator
from jupyterhub.handlers import BaseHandler
from traitlets import Dict, Integer, List, Unicode

# 内存验证码库：email -> {code, expires, attempts, sends:[timestamps]}
# 注：Hub 重启后失效，可接受（验证码本就只有 10 分钟命）
_otp_store = {}


def _make_send_handler(auth):
    """闭包捕获 authenticator 实例（get_handlers 拿到的是 JH 应用对象，无 .settings）"""

    class _SendCodeHandler(BaseHandler):
        """AJAX：POST /hub/otp/send  {email} → {ok: true}（永远返回成功，防枚举）"""

        async def post(self):
            try:
                data = json.loads(self.request.body.decode("utf-8"))
            except Exception:
                data = {}
            email = (data.get("email") or "").strip().lower()
            try:
                await auth.send_code(email)
            except Exception:
                # 发信失败也不向前端暴露细节
                pass
            self.set_header("Content-Type", "application/json")
            # 无论邮箱是否在允许列表，都返回同样文案
            self.write(json.dumps({"ok": True, "message": "如果该邮箱已注册，验证码已发送"}))

    return _SendCodeHandler


class EmailOTPAuthenticator(Authenticator):
    # 显式邮箱 → 用户名（管理员）
    allowed_emails = Dict(
        default_value={},
        help="显式允许的邮箱 -> JupyterHub 用户名",
    ).tag(config=True)
    # 域名 → 允许该域所有邮箱，用户名取 @ 前本地部分
    allowed_domains = List(
        default_value=[],
        help="允许的邮箱域名列表，用户名取本地部分",
    ).tag(config=True)

    smtp_host = Unicode("smtp.gmail.com").tag(config=True)
    smtp_port = Integer(587).tag(config=True)
    smtp_user = Unicode("", help="发件 Gmail 地址").tag(config=True)
    smtp_password_file = Unicode(
        "/srv/jupyterhub/.smtp-password", help="存 Gmail App Password 的文件"
    ).tag(config=True)
    code_ttl = Integer(600, help="验证码有效期（秒）").tag(config=True)
    max_sends_per_hour = Integer(5, help="每邮箱每小时最多发送次数").tag(config=True)
    max_verify_attempts = Integer(5, help="每个验证码最多试错次数").tag(config=True)

    def get_handlers(self, app):
        return [(r"/otp/send", _make_send_handler(self))]

    # ---------- 内部 ----------
    # 保留用户名：域名派生时禁止占用（防 admin@学生域 提权）
    _reserved = {"admin", "teacher", "root", "administrator", "system"}

    def _resolve_username(self, email):
        """邮箱 → 用户名；不在允许范围返回 None"""
        email = email.strip().lower()
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            return None
        if email in self.allowed_emails:
            return self.allowed_emails[email]
        domain = email.split("@", 1)[1]
        if domain in self.allowed_domains:
            local = email.split("@", 1)[0]
            # 用户名只允许安全字符，防路径穿越；保留名不可占用
            if (
                re.match(r"^[a-z0-9._-]{1,32}$", local)
                and local not in self._reserved
                and local not in set(self.allowed_emails.values())
            ):
                return local
        return None

    def _smtp_password(self):
        with open(self.smtp_password_file) as f:
            return f.read().strip()

    def _send_mail(self, to_email, code):
        msg = MIMEText(
            f"你的 IEV CloudLab 登录验证码是：{code}\n\n"
            f"10 分钟内有效，请勿转发给他人。",
            "plain",
            "utf-8",
        )
        msg["Subject"] = "IEV CloudLab 登录验证码"
        msg["From"] = self.smtp_user
        msg["To"] = to_email
        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as s:
            s.starttls()
            s.login(self.smtp_user, self._smtp_password())
            s.send_message(msg)

    async def send_code(self, email):
        email = (email or "").strip().lower()
        now = time.time()
        entry = _otp_store.get(email, {"sends": []})
        # 限流：每小时最多 N 次
        entry["sends"] = [t for t in entry.get("sends", []) if now - t < 3600]
        username = self._resolve_username(email)
        if username is None:
            # 未注册：假装发送（防枚举），但记一条审计日志
            self.log.warning("OTP request for unregistered email (not sent)")
            return
        if len(entry["sends"]) >= self.max_sends_per_hour:
            self.log.warning("OTP rate limited for %s", email)
            return
        code = f"{secrets.randbelow(1000000):06d}"
        _otp_store[email] = {
            "code": code,
            "expires": now + self.code_ttl,
            "attempts": 0,
            "sends": entry["sends"] + [now],
        }
        try:
            self._send_mail(email, code)
            self.log.info("OTP sent to %s", email)
        except Exception as e:
            # 发送失败则作废该码，避免用户拿着收不到的码干等
            _otp_store.pop(email, None)
            self.log.error("OTP send failed for %s: %s", email, type(e).__name__)
            raise

    async def authenticate(self, handler, data):
        email = (data.get("email") or "").strip().lower()
        code = (data.get("code") or "").strip()
        username = self._resolve_username(email)
        if not username or not re.match(r"^\d{6}$", code):
            return None
        entry = _otp_store.get(email)
        if not entry:
            return None
        if time.time() > entry["expires"]:
            _otp_store.pop(email, None)
            return None
        entry["attempts"] += 1
        if entry["attempts"] > self.max_verify_attempts:
            _otp_store.pop(email, None)
            self.log.warning("OTP attempts exhausted for %s", email)
            return None
        # 常量时间比较，防时序攻击
        if not secrets.compare_digest(entry["code"], code):
            return None
        # 一次性：验证通过即作废
        _otp_store.pop(email, None)
        self.log.info("OTP login success: %s -> %s", email, username)
        return username
