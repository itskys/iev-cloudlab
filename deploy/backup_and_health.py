"""IEV CloudLab 自动化备份与系统健康监控脚本 | Backup & Health Monitor

功能 (采纳 Muse 2026-10-28 评估建议 §5.2 与 §5.3)：
  1. 自动化快照备份 (--backup):
     - 打包 Hub 数据库 (jupyterhub.sqlite)、各学生 home 目录下的成绩结果 (results/) 与核心部署配置
     - 归档存储于 /opt/ievlab/backups/ievlab_backup_YYYYMMDD_HHMMSS.tar.gz
     - 自动保留最近 7 份每日快照，轮转淘汰旧备份，防止吃满磁盘
  2. 系统健康诊断与告警 (--check):
     - 检查 Hub HTTP 8000 端口可用性
     - 检查 Docker 关键容器运行状态 (jupyterhub, cloudflared)
     - 检查磁盘剩余空间 (超过 85% 告警)
     - 检查 Hub SQLite 权限规范 (防 644 漏洞)
"""

import argparse
import datetime
import glob
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import urllib.request

BASE_DIR = os.environ.get("IEVLAB_BASE", "/opt/ievlab")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
MAX_BACKUPS_RETAINED = 7
DISK_WARN_PERCENT = 85


def run_backup():
    """执行系统级核心数据原子快照备份。"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"ievlab_backup_{now_str}.tar.gz"
    archive_path = os.path.join(BACKUP_DIR, archive_name)

    items_to_pack = []

    # 1. Hub 核心数据库 (使用 SQLite 在线备份 API，保证事务一致性)
    hub_db = os.path.join(BASE_DIR, "hub_data", "jupyterhub.sqlite")
    temp_db_copy = os.path.join(BACKUP_DIR, f".tmp_db_{now_str}.sqlite")
    if os.path.isfile(hub_db):
        src_conn = None
        dst_conn = None
        try:
            src_conn = sqlite3.connect(hub_db)
            dst_conn = sqlite3.connect(temp_db_copy)
            with dst_conn:
                src_conn.backup(dst_conn)
            items_to_pack.append((temp_db_copy, "hub_data/jupyterhub.sqlite"))
        except Exception as e:
            print(f"[Backup Warning] SQLite online backup failed: {e}, falling back to file copy")
            items_to_pack.append((hub_db, "hub_data/jupyterhub.sqlite"))
        finally:
            if dst_conn:
                try:
                    dst_conn.close()
                except Exception:
                    pass
            if src_conn:
                try:
                    src_conn.close()
                except Exception:
                    pass

    # 2. 部署配置与密钥清单
    deploy_dir = os.path.join(BASE_DIR, "deploy")
    if os.path.isdir(deploy_dir):
        items_to_pack.append((deploy_dir, "deploy"))

    # 3. 仿真场景与模型资产 (OpenSCENARIO, OpenDRIVE, FMU 资产，防止路网场景意外丢失)
    scenarios_dir = os.path.join(BASE_DIR, "scenarios", "labs", "scenarios")
    if os.path.isdir(scenarios_dir):
        items_to_pack.append((scenarios_dir, "scenarios_assets"))

    # 4. 收集所有用户的成绩结果 (results/) 与分发记录 (manifest)
    homes_dir = os.path.join(BASE_DIR, "home")
    temp_results_dir = os.path.join(BACKUP_DIR, f".tmp_homes_{now_str}")
    if os.path.isdir(homes_dir):
        os.makedirs(temp_results_dir, exist_ok=True)
        for user in os.listdir(homes_dir):
            user_path = os.path.join(homes_dir, user)
            if not os.path.isdir(user_path):
                continue
            user_out = os.path.join(temp_results_dir, user)
            # 复制 results
            u_res = os.path.join(user_path, "labs", "data", "results")
            if os.path.isdir(u_res):
                shutil.copytree(u_res, os.path.join(user_out, "results"), dirs_exist_ok=True)
            # 复制 manifest
            u_man = os.path.join(user_path, ".ievlab_manifest.json")
            if os.path.isfile(u_man):
                os.makedirs(user_out, exist_ok=True)
                shutil.copy2(u_man, os.path.join(user_out, ".ievlab_manifest.json"))
        items_to_pack.append((temp_results_dir, "student_records"))

    # 压缩打包
    with tarfile.open(archive_path, "w:gz") as tar:
        for src, arcname in items_to_pack:
            if os.path.exists(src):
                tar.add(src, arcname=arcname)

    # 清理临时文件
    if os.path.exists(temp_db_copy):
        try: os.remove(temp_db_copy)
        except OSError: pass
    if os.path.exists(temp_results_dir):
        try: shutil.rmtree(temp_results_dir)
        except OSError: pass

    # 保留最近 N 份备份，自动清理旧快照
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "ievlab_backup_*.tar.gz")))
    while len(backups) > MAX_BACKUPS_RETAINED:
        oldest = backups.pop(0)
        try:
            os.remove(oldest)
            print(f"[Backup Pruned] Removed expired backup: {os.path.basename(oldest)}")
        except OSError:
            pass

    size_mb = os.path.getsize(archive_path) / (1024 * 1024)
    print(f"✓ [Backup Success] Snapshot saved: {archive_path} ({size_mb:.2f} MB)")
    return archive_path


def run_health_check():
    """检查系统运行健康度指标并输出报告。"""
    issues = []

    # 1. 检查磁盘占用
    stat = shutil.disk_usage(BASE_DIR)
    used_pct = (stat.used / stat.total) * 100
    avail_gb = stat.free / (1024 ** 3)
    print(f"• 磁盘占用率: {used_pct:.1f}% (剩余空间: {avail_gb:.2f} GB)")
    if used_pct >= DISK_WARN_PERCENT:
        issues.append(f"磁盘占用过高 ({used_pct:.1f}% >= {DISK_WARN_PERCENT}%)")

    # 2. 检查 Hub 服务 HTTP 响应
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/hub/health", headers={"User-Agent": "IEVLab-Monitor"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            code = resp.getcode()
            if code in (200, 302):
                print(f"• JupyterHub HTTP 探针: 正常 (HTTP {code})")
            else:
                issues.append(f"JupyterHub HTTP 返回异常状态码: {code}")
    except Exception as e:
        # 尝试检查首页
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/hub/login", timeout=5) as resp:
                print(f"• JupyterHub HTTP 探针: 正常 (Login Page HTTP {resp.getcode()})")
        except Exception as e2:
            issues.append(f"JupyterHub 无法建立 HTTP 连接: {e2}")

    # 3. 检查 SQLite 文件权限安全
    hub_db = os.path.join(BASE_DIR, "hub_data", "jupyterhub.sqlite")
    if os.path.isfile(hub_db):
        mode = oct(os.stat(hub_db).st_mode & 0o777)
        if mode != "0o600":
            issues.append(f"SQLite 数据库权限非 600 安全模式: 当前为 {mode}")
        else:
            print("• SQLite 数据库权限: 安全 (600)")

    # 4. 检查 Docker 关键容器
    try:
        out = subprocess.check_output(["docker", "ps", "--format", "{{.Names}}"], text=True)
        running_containers = out.strip().split("\n")
        for expected in ["jupyterhub", "cloudflared"]:
            if any(expected in name for name in running_containers):
                print(f"• 容器 {expected}: 运行中 (Up)")
            else:
                issues.append(f"关键容器 {expected} 未处于运行状态")
    except Exception as e:
        issues.append(f"Docker 状态检查失败: {e}")

    # 总结
    if issues:
        print("\n⚠️ [Health Warning] 检测到异常项:")
        for iss in issues:
            print(f"  ✗ {iss}")
        return False
    else:
        print("\n✅ [Health OK] 系统核心指标全绿，运行正常！")
        return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IEV CloudLab 备份与健康检查")
    parser.add_argument("--backup", action="store_true", help="执行快照备份")
    parser.add_argument("--check", action="store_true", help="执行健康检查")

    args = parser.parse_args()
    if args.backup:
        run_backup()
    elif args.check:
        run_health_check()
    else:
        # 默认两项皆运行
        run_health_check()
        run_backup()
