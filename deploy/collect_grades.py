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
    os.makedirs(args.out, exist_ok=True)
    out_path = os.path.join(args.out, 'all_results.json')
    with open(out_path, 'w') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    n_exp = sum(len(v) for v in all_results.values())
    print(f'Collected: {len(all_results)} students, {n_exp} experiment '
          f'results -> {out_path}')
    # teacher容器内文件属主应为jovyan(1000)
    try:
        os.chown(out_path, 1000, 1000)
        os.chown(args.out, 1000, 1000)
    except PermissionError:
        pass
    return 0


if __name__ == '__main__':
    sys.exit(main())
