#!/bin/bash
# IEV CloudLab 沙箱恢复演练：解包指定备份到临时目录并校验，不触碰线上数据
# 用法：restore_drill.sh [tarball路径]（默认最新一份每日备份）
set -u
SRC="${1:-$(ls -t /opt/ievlab/backups/ievlab_backup_*.tar.gz | head -1)}"
WORK="/tmp/restore-drill-$(date +%Y%m%d_%H%M%S)"
echo "钻取备份：$SRC"
mkdir -p "$WORK"
tar -xzf "$SRC" -C "$WORK" || { echo "FAIL: tarball 解包失败"; exit 1; }
python3 - "$WORK" <<'PYEOF'
import json, sqlite3, sys, glob, py_compile, os
w = sys.argv[1]
ok = True
def check(name, cond, detail=""):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name} {detail}")
    if not cond: ok = False
db = os.path.join(w, "hub_data/jupyterhub.sqlite")
try:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    users = conn.execute("select count(*) from users").fetchone()[0]
    check("Hub sqlite 可读且含 users 表", True, f"({users} users)")
    conn.close()
except Exception as e:
    check("Hub sqlite 可读且含 users 表", False, f"({e})")
nbs = glob.glob(os.path.join(w, "notebooks_master/*.ipynb"))
check("notebooks_master 数量", len(nbs) >= 35, f"({len(nbs)} 本)")
xosc = glob.glob(os.path.join(w, "scenarios_assets/**/*.xosc"), recursive=True)
xodr = glob.glob(os.path.join(w, "scenarios_assets/**/*.xodr"), recursive=True)
check("场景资产 xosc/xodr", len(xosc) >= 3 and len(xodr) >= 2, f"({len(xosc)} xosc, {len(xodr)} xodr)")
try:
    json.load(open(os.path.join(w, "notebooks_master/A1_cutin_aeb_pro.ipynb"), encoding="utf-8"))
    check("抽查 A1 Pro JSON 可解析", True)
except Exception as e:
    check("抽查 A1 Pro JSON 可解析", False, f"({e})")
try:
    py_compile.compile(os.path.join(w, "common_libs/lab_explorers.py"), doraise=True)
    check("抽查 lab_explorers.py 可编译", True)
except Exception as e:
    check("抽查 lab_explorers.py 可编译", False, f"({e})")
check("student_records 目录存在", os.path.isdir(os.path.join(w, "student_records")))
check("deploy 目录存在", os.path.isdir(os.path.join(w, "deploy")))
print("OVERALL:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PYEOF
RC=$?
rm -rf "$WORK"
echo "沙箱已清理：$WORK"
exit $RC
