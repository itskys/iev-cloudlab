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
    all_previews = {}
    reports_manifest = {}
    if not os.path.isdir(home_root):
        return all_results, all_previews, reports_manifest

    roster = load_roster()
    ignore_md_files = {
        'readme.md', 'teacher_guide.md', 'syllabus_16weeks.md',
        '学生快速上手指南.md', '教师指导手册.md', '课程大纲_16周.md', '实验手册.md',
        'demo_script_10min.md', 'student_quickstart.md', '实验报告模板_示例.md'
    }

    for user in sorted(os.listdir(home_root)):
        if roster is not None:
            if user not in roster:
                continue
        elif user in SKIP_USERS:
            continue

        u_home = os.path.join(home_root, user)
        if not os.path.isdir(u_home):
            continue

        # 1. 收集客观实验仿真结果 (results/)
        rdir = os.path.join(u_home, 'labs', 'data', 'results')
        if os.path.isdir(rdir):
            exps = {}
            for fname in os.listdir(rdir):
                if not fname.endswith('.json') or fname in SKIP_FILES:
                    continue
                exp_id = fname[:-5]
                try:
                    with open(os.path.join(rdir, fname), encoding='utf-8') as f:
                        data = json.load(f)
                    exps[exp_id] = data.get('metrics', data)
                except (json.JSONDecodeError, OSError):
                    continue
            if exps:
                all_results[user] = exps

        # 2. 收集 Phase 0 新手直觉预习打卡 (preview_checkins/ 与 lite/)
        p_dirs = [
            os.path.join(u_home, 'labs', 'data', 'preview_checkins'),
            os.path.join(u_home, 'labs', 'data', 'lite')
        ]
        user_previews = {}
        for pdir in p_dirs:
            if os.path.isdir(pdir):
                for fname in os.listdir(pdir):
                    if not fname.endswith('.json'):
                        continue
                    exp_id = fname.replace('_preview.json', '').replace('.json', '')
                    try:
                        with open(os.path.join(pdir, fname), encoding='utf-8') as f:
                            pdata = json.load(f)
                        user_previews[exp_id] = pdata
                    except (json.JSONDecodeError, OSError):
                        continue
        if user_previews:
            all_previews[user] = user_previews

        # 3. 收集学生撰写的实验报告 Markdown
        search_dirs = [
            os.path.join(u_home, 'reports'),
            os.path.join(u_home, 'notebooks'),
            u_home
        ]
        user_reports = []
        for sdir in search_dirs:
            if os.path.isdir(sdir):
                for fname in os.listdir(sdir):
                    if fname.lower().endswith('.md') and fname.lower() not in ignore_md_files:
                        full_p = os.path.join(sdir, fname)
                        if os.path.isfile(full_p):
                            user_reports.append({
                                'file_name': fname,
                                'source_path': full_p,
                                'size_bytes': os.path.getsize(full_p),
                                'mtime': os.path.getmtime(full_p)
                            })
        if user_reports:
            reports_manifest[user] = user_reports

    return all_results, all_previews, reports_manifest


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--home-root', default='/opt/ievlab/home')
    ap.add_argument('--out', default='/opt/ievlab/home/teacher/grades')
    args = ap.parse_args()

    all_results, all_previews, reports_manifest = collect(args.home_root)
    outs = [args.out]
    if args.out.endswith('/teacher/grades'):
        outs.append(args.out.replace('/teacher/grades', '/admin/grades'))

    for out_dir in outs:
        os.makedirs(out_dir, exist_ok=True)

        # 写入 1: all_results.json
        out_path = os.path.join(out_dir, 'all_results.json')
        tmp_path = out_path + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, out_path)

        # 写入 2: all_previews.json (Phase 0 打卡汇总)
        prev_path = os.path.join(out_dir, 'all_previews.json')
        tmp_prev = prev_path + '.tmp'
        with open(tmp_prev, 'w', encoding='utf-8') as f:
            json.dump(all_previews, f, ensure_ascii=False, indent=2)
        os.replace(tmp_prev, prev_path)

        # 写入 3: all_reports_manifest.json (学生报告索引与实体归集)
        rep_dir = os.path.join(out_dir, 'submitted_reports')
        os.makedirs(rep_dir, exist_ok=True)
        for user, rlist in reports_manifest.items():
            u_rep_dest = os.path.join(rep_dir, user)
            os.makedirs(u_rep_dest, exist_ok=True)
            for rinfo in rlist:
                try:
                    import shutil
                    shutil.copy2(rinfo['source_path'], os.path.join(u_rep_dest, rinfo['file_name']))
                except Exception:
                    pass

        rep_manifest_path = os.path.join(out_dir, 'all_reports_manifest.json')
        tmp_rep = rep_manifest_path + '.tmp'
        with open(tmp_rep, 'w', encoding='utf-8') as f:
            json.dump(reports_manifest, f, ensure_ascii=False, indent=2)
        os.replace(tmp_rep, rep_manifest_path)

        # 递归修复权限为 1000:1000
        try:
            for root, dirs, files in os.walk(out_dir):
                for d in dirs:
                    dp = os.path.join(root, d)
                    os.chown(dp, 1000, 1000)
                    os.chmod(dp, 0o755)
                for fn in files:
                    fp = os.path.join(root, fn)
                    os.chown(fp, 1000, 1000)
                    os.chmod(fp, 0o644)
            os.chown(out_dir, 1000, 1000)
            os.chmod(out_dir, 0o755)
        except (PermissionError, OSError):
            pass

    n_exp = sum(len(v) for v in all_results.values())
    n_prev = sum(len(v) for v in all_previews.values())
    n_rep = sum(len(v) for v in reports_manifest.values())
    print(f'Collected: {len(all_results)} students with {n_exp} results, '
          f'{len(all_previews)} students with {n_prev} previews, '
          f'{len(reports_manifest)} students with {n_rep} reports -> {outs[0]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
