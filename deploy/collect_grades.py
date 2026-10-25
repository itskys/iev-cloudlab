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


def collect(home_root):
    all_results = {}
    if not os.path.isdir(home_root):
        return all_results
    for user in sorted(os.listdir(home_root)):
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
        # [权限加固 - 2026-10-25 给 Muse 说明]：
        # Host cron 通常以 root 身份运行，写入的文件属主若为 root:root 且仅 0644，
        # teacher 容器（以 jovyan UID 1000 运行）在调用 gradebook 或归档时会报 PermissionDenied。
        # 故统一赋权 1000:1000 并给予 0666 权限，防止教师面板保存/刷新失败。
        try:
            os.chown(out_path, 1000, 1000)
            os.chown(out_dir, 1000, 1000)
            os.chmod(out_path, 0o666)
            os.chmod(out_dir, 0o775)
        except (PermissionError, OSError):
            pass
    n_exp = sum(len(v) for v in all_results.values())
    print(f'Collected: {len(all_results)} students, {n_exp} experiment '
          f'results -> {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
