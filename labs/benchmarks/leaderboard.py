"""IEV CloudLab 天梯排位赛引擎与成绩持久化 | Leaderboard Core Engine

功能：
  1. submit_score(): 提交学生算法在基准挑战赛中的成绩并持久化
  2. get_leaderboard(): 获取指定赛道的排名数据列表
  3. render_leaderboard(): 渲染可视化 HTML 天梯榜单（支持勋章、段位胶囊、高亮当前用户）
"""

import fcntl
import hashlib
import html as html_lib
import json
import os
import time
from datetime import datetime

BENCHMARKS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "benchmarks")
)


def _ensure_dir():
    os.makedirs(BENCHMARKS_DIR, exist_ok=True)


def _get_benchmark_file(benchmark_name):
    _ensure_dir()
    clean_name = "".join(c for c in benchmark_name if c.isalnum() or c in ("_", "-"))
    return os.path.join(BENCHMARKS_DIR, f"{clean_name}.json")


def _generate_pseudonym(user_id):
    """根据用户名生成固定但具科技感的花名，用于保护隐私或匿名展示。"""
    h = hashlib.md5(user_id.encode("utf-8")).hexdigest()
    num = int(h[:4], 16) % 1000
    prefixes = ["Cyber", "Apex", "Nova", "Vector", "Quantum", "Hyper", "Vortex", "Titan"]
    p = prefixes[int(h[4:6], 16) % len(prefixes)]
    return f"{p}-Driver-{num:03d}"


def submit_score(
    benchmark_name,
    user_id,
    score,
    metrics,
    nickname=None,
    higher_is_better=True,
):
    """提交成绩并更新排行榜。

    参数:
      benchmark_name: 赛道名称，如 'e4_ems_challenge' 或 'h2_safety_fuzzing'
      user_id: 学生唯一 ID / 用户名 (如 'student_01')
      score: 综合排位分 (float)
      metrics: 详细工程指标字典 (dict)
      nickname: 显示昵称 (若为 None 则自动生成科技风花名)
      higher_is_better: 排序规则，True 为分数越高越好

    返回:
      dict: 包含当前用户排名、超越百分比及完整榜单记录
    """
    filepath = _get_benchmark_file(benchmark_name)
    lock_file = filepath + ".lock"

    # 使用文件排他锁保证并发读写一致性，若环境受限则优雅降级为无锁写入
    lf = None
    try:
        try:
            lf = open(lock_file, "w")
            fcntl.flock(lf, fcntl.LOCK_EX)
        except (OSError, PermissionError):
            lf = None

        data = {"benchmark": benchmark_name, "records": []}

        if os.path.isfile(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {"benchmark": benchmark_name, "records": []}

        records = data.get("records", [])

        if not nickname:
            nickname = _generate_pseudonym(user_id)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 检查该用户是否已有记录：若新成绩更优则更新，否则保留更优成绩
        existing_idx = None
        for idx, r in enumerate(records):
            if r.get("user_id") == user_id:
                existing_idx = idx
                break

        new_record = {
            "user_id": user_id,
            "nickname": nickname,
            "score": round(float(score), 2),
            "metrics": {k: round(float(v), 3) if isinstance(v, (int, float)) else str(v) for k, v in metrics.items()},
            "timestamp": now_str,
        }

        if existing_idx is not None:
            old_score = records[existing_idx].get("score", 0.0)
            is_better = (score > old_score) if higher_is_better else (score < old_score)
            if is_better:
                records[existing_idx] = new_record
        else:
            records.append(new_record)

        # 排序
        records.sort(key=lambda x: x["score"], reverse=higher_is_better)

        # 赋予排名
        user_rank = 1
        for rank, r in enumerate(records, 1):
            r["rank"] = rank
            if r.get("user_id") == user_id:
                user_rank = rank

        data["records"] = records
        data["updated_at"] = now_str

        # 原子写入
        tmp_path = filepath + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, filepath)
    finally:
        if lf:
            try:
                fcntl.flock(lf, fcntl.LOCK_UN)
                lf.close()
            except Exception:
                pass

    total_participants = len(records)
    beat_pct = round(((total_participants - user_rank) / max(1, total_participants - 1)) * 100, 1)

    return {
        "user_id": user_id,
        "rank": user_rank,
        "total": total_participants,
        "beat_pct": beat_pct,
        "score": score,
        "records": records,
    }


def get_leaderboard(benchmark_name):
    """读取指定赛道的全部排行记录。"""
    filepath = _get_benchmark_file(benchmark_name)
    if not os.path.isfile(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("records", [])
    except Exception:
        return []


def render_leaderboard(
    benchmark_name,
    current_user=None,
    title="IEV 智能网联工程天梯榜",
    metric_labels=None,
    top_n=10,
):
    """渲染具有电竞赛事质感的 HTML 动态天梯排行榜小部件。"""
    records = get_leaderboard(benchmark_name)
    if not records:
        # 若暂无记录，生成基准参考 NPC 排行，营造浓厚打榜竞技氛围
        records = [
            {"rank": 1, "user_id": "benchmark_ref", "nickname": "Cyber-Benchmark (大师标杆)", "score": 96.5, "metrics": {"能耗": 4.12, "计算时延": 3.8}, "timestamp": "2026-10-28 08:00"},
            {"rank": 2, "user_id": "npc_2", "nickname": "Vector-Driver-104", "score": 91.2, "metrics": {"能耗": 4.35, "计算时延": 5.1}, "timestamp": "2026-10-28 07:45"},
            {"rank": 3, "user_id": "npc_3", "nickname": "Apex-Pilot-520", "score": 87.0, "metrics": {"能耗": 4.60, "计算时延": 6.2}, "timestamp": "2026-10-28 07:30"},
        ]

    top_records = records[:top_n]

    # 确定要展示的指标列：遍历 TOP 记录收集所有指标键，防止因记录间键名不一致导致部分列缺失
    metric_keys = []
    for r in top_records:
        for k in r.get("metrics", {}).keys():
            if k not in metric_keys:
                metric_keys.append(k)
    if not metric_labels:
        metric_labels = {k: k for k in metric_keys}

    import uuid
    uid = f"lb_{uuid.uuid4().hex[:8]}"

    def _get_tier(rank, score):
        if rank == 1 or score >= 95:
            return ("#FFD700", "👑 宗师 Grandmaster")
        elif rank <= 3 or score >= 90:
            return ("#58A6FF", "💎 钻石 Diamond")
        elif score >= 80:
            return ("#3FB950", "🏅 铂金 Platinum")
        else:
            return ("#8B949E", "🔰 达标 Qualified")

    rows_html = ""
    for r in top_records:
        rk = r.get("rank", 99)
        u = r.get("user_id", "")
        is_me = (current_user and u == current_user)
        score = r.get("score", 0.0)
        tier_color, tier_text = _get_tier(rk, score)

        medal = str(rk)
        if rk == 1:
            medal = "🥇 1"
        elif rk == 2:
            medal = "🥈 2"
        elif rk == 3:
            medal = "🥉 3"

        row_bg = "rgba(56, 139, 253, 0.12)" if is_me else "transparent"
        border_left = "3px solid #58A6FF" if is_me else "3px solid transparent"

        metric_tds = ""
        for mk in metric_keys:
            val = r.get("metrics", {}).get(mk, "--")
            val_escaped = html_lib.escape(str(val))
            metric_tds += f"<td style='padding: 10px; font-family: monospace; text-align: center; color: #C9D1D9;'>{val_escaped}</td>"

        nick_escaped = html_lib.escape(str(r.get('nickname', '')))
        rows_html += f"""
        <tr style="
            background: {row_bg}; border-bottom: 1px solid #21262D; border-left: {border_left};
            transition: background 0.2s;
        ">
            <td style="padding: 10px 14px; font-weight: 700; color: #F0F6FC; font-size: 13px;">{medal}</td>
            <td style="padding: 10px 14px; font-weight: 600; color: {'#58A6FF' if is_me else '#E6EDF3'};">
                {nick_escaped} {'<span style="font-size: 10px; background: #388BFD; color: #fff; padding: 1px 6px; border-radius: 8px; margin-left: 6px;">YOU</span>' if is_me else ''}
            </td>
            <td style="padding: 10px 14px;">
                <span style="
                    font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600;
                    color: {tier_color}; background: {tier_color}18; border: 1px solid {tier_color}55;
                ">{tier_text}</span>
            </td>
            <td style="padding: 10px 14px; font-family: monospace; font-size: 14px; font-weight: 700; color: #58A6FF; text-align: center;">
                {score:.1f}
            </td>
            {metric_tds}
            <td style="padding: 10px 14px; font-size: 11px; color: #8B949E; text-align: right;">{r.get('timestamp', '')}</td>
        </tr>
        """

    headers_html = "".join([f"<th style='padding: 10px; text-align: center; color: #8B949E; font-weight: 500;'>{metric_labels.get(k, k)}</th>" for k in metric_keys])

    html = f"""
<div id="{uid}" style="
    width: 100%; background: #0D1117; border: 1px solid #30363D; border-radius: 10px;
    overflow: hidden; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #C9D1D9; box-shadow: 0 8px 24px rgba(0,0,0,0.35); margin: 16px 0;
">
    <!-- 顶栏标题 -->
    <div style="
        height: 46px; background: #161B22; border-bottom: 1px solid #30363D;
        display: flex; align-items: center; justify-content: space-between; padding: 0 16px;
    ">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 16px;">🏆</span>
            <span style="font-weight: 700; font-size: 14px; color: #F0F6FC;">{title}</span>
            <span style="font-size: 11px; color: #8B949E;">· TOP {top_n} 实时排位榜</span>
        </div>
        <div style="font-size: 11px; color: #8B949E;">
            赛道标识: <code style="color: #58A6FF; background: #21262D; padding: 2px 6px; border-radius: 4px;">{benchmark_name}</code>
        </div>
    </div>

    <!-- 表格内容 -->
    <div style="overflow-x: auto;">
        <table style="width: 100%; border-collapse: collapse; font-size: 12px; text-align: left;">
            <thead>
                <tr style="background: #161B22; border-bottom: 1px solid #30363D;">
                    <th style="padding: 10px 14px; color: #8B949E; font-weight: 500; width: 60px;">排位</th>
                    <th style="padding: 10px 14px; color: #8B949E; font-weight: 500;">车手 / 算法</th>
                    <th style="padding: 10px 14px; color: #8B949E; font-weight: 500;">工程段位</th>
                    <th style="padding: 10px 14px; color: #8B949E; font-weight: 500; text-align: center;">排位总分</th>
                    {headers_html}
                    <th style="padding: 10px 14px; color: #8B949E; font-weight: 500; text-align: right;">挑战时间</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>
</div>
"""
    try:
        from IPython.display import HTML
        return HTML(html)
    except ImportError:
        return html
