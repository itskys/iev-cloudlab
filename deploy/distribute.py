"""IEV CloudLab 内容分发器（在 Hub 容器内由 pre_spawn_hook 调用，也可独立运行测试）。

# [功能设计 - 2026-10-25 给 Muse 说明]：
# 解决学生首次登录 /opt/ievlab/home/<user> 目录空白无课件问题。
# 把标准实验内容（/opt/ievlab/scenarios 的 notebooks/ 与 labs/）自动分发补进用户 home。
# 保守同步规则，绝不覆盖学生成果：
#   - home 里缺失的文件 -> 复制，并把源哈希记入 home/.ievlab_manifest.json
#   - 此前由分发放入、学生未改动、且标准源已更新 -> 跟随更新
#   - 学生改过的文件（当前哈希 != 分发时记录） -> 跳过，永不覆盖
#   - 不是分发放入的文件（教师/管理员自有） -> 跳过，永不触碰
# 排除项：教师面板 notebook、notebooks/archive/、labs/data/results/ 的内容、
#         __pycache__、.ipynb_checkpoints。
# 附带：
#   1. 为新用户播种 student_quickstart.md 作为 home 目录的 README.md（新手引导）
#   2. 为新用户播种 JupyterLab 设置（.md 默认用 Markdown Preview 打开），仅补缺失。
# 任何异常都不向上抛（分发失败不能挡住学生登录），由调用方记日志。
"""

import hashlib
import json
import os
import shutil

SRC = os.environ.get("IEVLAB_SRC", "/opt/ievlab/scenarios")
HOMES = os.environ.get("IEVLAB_HOMES", "/opt/ievlab/home")
UID = GID = 1000
MANIFEST_NAME = ".ievlab_manifest.json"

EXCLUDE_DIRS = {"__pycache__", ".ipynb_checkpoints", "archive"}
EXCLUDE_FILES = {"教师面板_成绩与学生管理.ipynb"}
# results/ 只建空目录，不分发其中内容（那是学生自己的产出区）
EMPTY_DIRS = {"labs/data/results"}

SETTINGS_REL = (
    ".jupyter/lab/user-settings/@jupyterlab/"
    "docmanager-extension/plugin.jupyterlab-settings"
)
SETTINGS_BODY = '{\n  "defaultViewers": {\n    "markdown": "Markdown Preview"\n  }\n}\n'


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_sources():
    """产出 (相对路径, 源绝对路径)：notebooks/ 与 labs/ 下应分发的文件。"""
    for top in ("notebooks", "labs"):
        base = os.path.join(SRC, top)
        if not os.path.isdir(base):
            continue
        for root, dirs, files in os.walk(base):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            rel_root = os.path.relpath(root, SRC)
            if rel_root.replace(os.sep, "/") in EMPTY_DIRS:
                files = []
            for name in files:
                if name in EXCLUDE_FILES:
                    continue
                rel = os.path.join(rel_root, name).replace(os.sep, "/")
                yield rel, os.path.join(root, name)


def _ensure_dir(path, created):
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)
        created.append(path)


def distribute(username):
    home = os.path.join(HOMES, username)
    stats = {"copied": 0, "updated": 0, "skipped_modified": 0, "skipped_foreign": 0}
    created_dirs = []
    _ensure_dir(home, created_dirs)

    manifest_path = os.path.join(home, MANIFEST_NAME)
    manifest = {}
    if os.path.isfile(manifest_path):
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception:
            manifest = {}

    for rel, src_path in _iter_sources():
        dst = os.path.join(home, rel.replace("/", os.sep))
        src_hash = _sha(src_path)
        if not os.path.exists(dst):
            _ensure_dir(os.path.dirname(dst), created_dirs)
            shutil.copy2(src_path, dst)
            os.chown(dst, UID, GID)
            manifest[rel] = src_hash
            stats["copied"] += 1
        elif rel in manifest:
            cur_hash = _sha(dst)
            if cur_hash != manifest[rel]:
                stats["skipped_modified"] += 1  # 学生改过：不碰
            elif src_hash != manifest[rel]:
                shutil.copy2(src_path, dst)
                os.chown(dst, UID, GID)
                manifest[rel] = src_hash
                stats["updated"] += 1
        else:
            stats["skipped_foreign"] += 1  # 非分发放入：不碰

    # 空目录（学生产出区）只建目录本身
    for rel in EMPTY_DIRS:
        _ensure_dir(os.path.join(home, rel.replace("/", os.sep)), created_dirs)

    # [优化 - 2026-10-25 给 Muse 说明]：为学生目录自动补齐 README.md 快速入门指引
    quickstart_src = os.path.join(SRC, "student_quickstart.md")
    if not os.path.isfile(quickstart_src):
        quickstart_src = os.path.join(SRC, "notebooks", "student_quickstart.md")
    readme_dst = os.path.join(home, "README.md")
    if os.path.isfile(quickstart_src) and not os.path.exists(readme_dst):
        try:
            shutil.copy2(quickstart_src, readme_dst)
            os.chown(readme_dst, UID, GID)
            manifest["README.md"] = _sha(quickstart_src)
            stats["readme_seeded"] = 1
        except Exception:
            pass

    # JupyterLab 设置播种：仅补缺失，不覆盖已有
    settings_path = os.path.join(home, SETTINGS_REL.replace("/", os.sep))
    if not os.path.exists(settings_path):
        _ensure_dir(os.path.dirname(settings_path), created_dirs)
        with open(settings_path, "w", encoding="utf-8") as f:
            f.write(SETTINGS_BODY)
        os.chown(settings_path, UID, GID)
        stats["settings_seeded"] = 1

    for d in created_dirs:
        try:
            os.chown(d, UID, GID)
        except OSError:
            pass

    tmp_path = manifest_path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1, sort_keys=True)
    os.replace(tmp_path, manifest_path)
    os.chown(manifest_path, UID, GID)
    return stats


if __name__ == "__main__":
    import sys

    user = sys.argv[1] if len(sys.argv) > 1 else "testuser"
    print(user, distribute(user))
