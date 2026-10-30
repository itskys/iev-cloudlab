#!/usr/bin/env python3
"""主机端成绩汇总 | Collect grades from all student homes (run on VPS host)

扫描 /opt/ievlab/home/<user>/labs/data/results/*.json，
汇总为 {username: {exp_id: metrics}} 写入教师环境的 grades/all_results.json，
供教师面板notebook读取。

用法： python3 collect_grades.py [--home-root /opt/ievlab/home]
                                [--out /opt/ievlab/home/teacher/grades]
定时运行（可选）： cron 每小时执行一次。
"""
import argparse
import json
import os
import sys

SKIP_FILES = {'test_chain.json'}

# 非学生账号：即使其 home 下有结果文件也不计入成绩（2026-10-29 P0 修复：
# 教师成绩曾混入 admin / teacher / testuser 三个测试账号）。
SKIP_USERS = {'admin', 'teacher', 'testuser'}
# 名册文件（教师端 student_admin.py 维护，宿主机路径）：
# 若存在且能读出非空用户名单，则只收名册内用户；否则退化为 SKIP_USERS 黑名单。
ROSTER_PATHS = [
    '/opt/ievlab/home/teacher/labs/data/students.json',
    '/opt/ievlab/home/admin/labs/data/students.json',
]


def load_roster():
    """容忍多种名册格式，返回用户名集合；读不到/为空时返回 None。"""
    for path in ROSTER_PATHS:
        try:
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        users = set()
        items = None
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for key in ('students', 'roster', 'users'):
                if isinstance(data.get(key), list):
                    items = data[key]
                    break
            if items is None and data:
                # 字典本身以用户名为键
                users = {str(k) for k in data.keys()}
                items = []
        if items:
            for it in items:
                if isinstance(it, str):
                    users.add(it)
                elif isinstance(it, dict):
                    for key in ('username', 'name', 'id', 'student_id'):
                        if it.get(key):
                            users.add(str(it[key]))
                            break
        if users:
            return users
    return None


def collect(home_root):
    all_results = {}
    if not os.path.isdir(home_root):
        return all_results
    roster = load_roster()
    for user in sorted(os.listdir(home_root)):
        if roster is not None:
            if user not in roster:
                continue
        elif user in SKIP_USERS:
            continue
        rdir = os.path.join(home_root, user, 'labs', 'data', 'results')
        if not os.path.isdir(rdir):
            continue
        exps = {}
        for fname in os.listdir(rdir):
            if not fname.endswith('.json') or fname in SKIP_FILES:
                continue
            exp_id = fname[:-5]
            try:
                with open(os.path.join(rdir, fname)) as f:
                    data = json.load(f)
                exps[exp_id] = data.get('metrics', data)
            except (json.JSONDecodeError, OSError):
                continue
        if exps:
            all_results[user] = exps
    return all_results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--home-root', default='/opt/ievlab/home')
    ap.add_argument('--out', default='/opt/ievlab/home/teacher/grades')
    args = ap.parse_args()

    all_results = collect(args.home_root)
    outs = [args.out]
    if args.out.endswith('/teacher/grades'):
        outs.append(args.out.replace('/teacher/grades', '/admin/grades'))
    out_path = None
    for out_dir in outs:
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, 'all_results.json')
        with open(out_path, 'w') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        # [权限收紧 - 2026-10-25 Muse 复核]：
        # Host cron 通常以 root 身份运行，写入的文件属主若为 root:root 且仅 0644，
        # teacher 容器（以 jovyan UID 1000 运行）在调用 gradebook 或归档时会报 PermissionDenied。
        # chown 到 1000:1000 已足够保证教师面板读写；0666/0775 属于过度放宽，
        # 故收紧为文件 0644、目录 0755（属主可写，他人只读）。
        try:
            os.chown(out_path, 1000, 1000)
            os.chown(out_dir, 1000, 1000)
            os.chmod(out_path, 0o644)
            os.chmod(out_dir, 0o755)
        except (PermissionError, OSError):
            pass
    n_exp = sum(len(v) for v in all_results.values())
    print(f'Collected: {len(all_results)} students, {n_exp} experiment '
          f'results -> {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
