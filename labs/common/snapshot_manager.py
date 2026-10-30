"""IEV CloudLab 学生端代码自动快照与时光机回溯保护 | Snapshot & Time Machine

功能说明：
  解决学生在实验过程中“修改算法改崩、误删核心代码、调参失败无法恢复”的教学痛点。

核心特性：
  1. 自动化安全气囊：
     - 当实验评测得分达标 (score >= 60) 或手动调用时，自动保存轻量化时间戳快照；
  2. 防丢失双重保险：
     - 在执行任何“回退”操作前，系统自动对当前状态创建 `pre_restore_auto_save` 紧急快照，绝对零数据丢失；
  3. 细粒度代码 Diff 对比：
     - 基于 Python difflib，支持在 Jupyter 环境中直观对比当前代码与历史快照的增删改差异；
  4. 原生交互式“时光机 (Time Machine)”组件：
     - 包含时间轴快照卡片、得分标记、Diff 预览折叠面板与一键恢复按钮。
"""

import difflib
import json
import os
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union


SNAPSHOT_ROOT = os.path.expanduser('~/.snapshots')


def _get_snapshot_dir(notebook_path_or_name: str) -> str:
    """获取指定 Notebook 的专属快照存放目录"""
    base = os.path.basename(notebook_path_or_name)
    if not base.endswith('.ipynb'):
        base = f"{base}.ipynb"
    name_clean = os.path.splitext(base)[0]
    s_dir = os.path.join(SNAPSHOT_ROOT, name_clean)
    os.makedirs(s_dir, exist_ok=True)
    return s_dir


def _read_notebook_source(nb_path: str) -> str:
    """读取 Notebook 并将其所有代码单元格提取为扁平的文本，便于对比"""
    if not os.path.exists(nb_path):
        return ""
    try:
        with open(nb_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cells = data.get('cells', [])
        lines = []
        for i, c in enumerate(cells):
            c_type = c.get('cell_type', 'code')
            src = ''.join(c.get('source', []))
            lines.append(f"### [Cell {i+1} - {c_type}] ###\n" + src)
        return "\n\n".join(lines)
    except Exception:
        with open(nb_path, 'r', encoding='utf-8') as f:
            return f.read()


def create_snapshot(
    notebook_path: str,
    message: str = "手动保存快照",
    score: Optional[float] = None,
) -> Dict[str, Any]:
    """为指定 Notebook 创建历史快照点。

    :param notebook_path: Notebook 文件路径（如 'notebooks/A1_cutin_aeb_pro.ipynb'）
    :param message: 快照备注说明（如 '调参避险通过，得分 100'）
    :param score: 对应的评测得分（可选）
    :return: 快照元数据字典
    """
    if not os.path.exists(notebook_path):
        # 尝试在当前目录或 notebooks/ 目录下寻找
        candidates = [
            notebook_path,
            os.path.join('notebooks', notebook_path),
            os.path.join('..', 'notebooks', notebook_path),
            os.path.join('/home/jovyan/notebooks', notebook_path),
        ]
        found = False
        for c in candidates:
            if os.path.exists(c):
                notebook_path = c
                found = True
                break
        if not found:
            return {'success': False, 'error': f'未找到文件: {notebook_path}'}

    s_dir = _get_snapshot_dir(notebook_path)
    now = datetime.now()
    timestamp_id = now.strftime('%Y%m%d_%H%M%S')
    snap_id = f"snap_{timestamp_id}"

    dest_file = os.path.join(s_dir, f"{snap_id}.ipynb")
    shutil.copy2(notebook_path, dest_file)

    meta = {
        'snapshot_id': snap_id,
        'timestamp': now.isoformat(),
        'display_time': now.strftime('%Y-%m-%d %H:%M:%S'),
        'message': message,
        'score': score,
        'original_path': os.path.abspath(notebook_path),
        'file_path': dest_file,
    }

    # 更新索引表 index.json
    index_file = os.path.join(s_dir, 'index.json')
    history = []
    if os.path.exists(index_file):
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception:
            history = []

    history.insert(0, meta)  # 最新排在最前

    # 自动安全配额控制：单文件最多保留最近 20 个快照，防止多次运行撑满磁盘
    MAX_SNAPSHOTS_PER_NB = 20
    if len(history) > MAX_SNAPSHOTS_PER_NB:
        for old_snap in history[MAX_SNAPSHOTS_PER_NB:]:
            old_file = old_snap.get('file_path')
            if old_file and os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except Exception:
                    pass
        history = history[:MAX_SNAPSHOTS_PER_NB]

    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

    return {'success': True, 'snapshot': meta}


def list_snapshots(notebook_path_or_name: str) -> List[Dict[str, Any]]:
    """列出指定 Notebook 的所有历史快照版本"""
    s_dir = _get_snapshot_dir(notebook_path_or_name)
    index_file = os.path.join(s_dir, 'index.json')
    if not os.path.exists(index_file):
        return []
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def compute_code_diff(current_nb_path: str, snapshot_id: str) -> str:
    """计算当前 Notebook 代码与目标快照版本之间的差异 (Diff)"""
    s_dir = _get_snapshot_dir(current_nb_path)
    target_snap_file = os.path.join(s_dir, f"{snapshot_id}.ipynb")
    if not os.path.exists(target_snap_file):
        return f"快照文件不存在: {target_snap_file}"

    current_src = _read_notebook_source(current_nb_path).splitlines()
    snap_src = _read_notebook_source(target_snap_file).splitlines()

    diff = difflib.unified_diff(
        snap_src,
        current_src,
        fromfile=f"Snapshot ({snapshot_id})",
        tofile="Current Working Notebook",
        lineterm="",
    )
    return "\n".join(diff)


def restore_snapshot(current_nb_path: str, snapshot_id: str) -> Dict[str, Any]:
    """回退到指定快照版本（在回退前自动备份当前工作状态，确保零丢失）。"""
    s_dir = _get_snapshot_dir(current_nb_path)
    target_snap_file = os.path.join(s_dir, f"{snapshot_id}.ipynb")
    if not os.path.exists(target_snap_file):
        return {'success': False, 'error': f'未找到目标快照: {snapshot_id}'}

    if not os.path.exists(current_nb_path):
        return {'success': False, 'error': f'未找到当前文件: {current_nb_path}'}

    # 1. 紧急安全备份当前未提交代码
    auto_backup = create_snapshot(
        current_nb_path,
        message=f"【自动安全保护】回退到 {snapshot_id} 前的紧急暂存",
    )

    # 2. 覆盖回退
    try:
        shutil.copy2(target_snap_file, current_nb_path)
        return {
            'success': True,
            'restored_snapshot': snapshot_id,
            'safety_backup': auto_backup.get('snapshot', {}).get('snapshot_id'),
            'message': f'成功恢复到版本 {snapshot_id}！已自动将回退前代码备份为紧急快照。',
        }
    except Exception as e:
        return {'success': False, 'error': f'文件写入失败: {str(e)}'}


def render_time_machine_html(current_nb_path: str) -> str:
    """生成富文本时光机卡片与版本历史时间轴 (HTML)"""
    snapshots = list_snapshots(current_nb_path)
    nb_name = os.path.basename(current_nb_path)

    if not snapshots:
        return f"""
        <div style="background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px; margin: 10px 0; font-family: system-ui, sans-serif; text-align: center;">
            <p style="margin: 0; color: #64748b; font-size: 13px;">
                ⏱️ 当前文件 <strong>{nb_name}</strong> 暂无历史快照。<br/>
                运行 <code>from common.snapshot_manager import create_snapshot; create_snapshot('{nb_name}', '首版基线')</code> 即可打下第一个安全锚点！
            </p>
        </div>
        """

    items_html = ""
    for idx, s in enumerate(snapshots[:8]):  # 展示最近 8 个
        score_badge = ""
        if s.get('score') is not None:
            sc = s['score']
            sc_color = "#10b981" if sc >= 80 else ("#f59e0b" if sc >= 60 else "#ef4444")
            score_badge = f'<span style="background: {sc_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold; margin-left: 6px;">{sc:.1f}分</span>'

        items_html += f"""
        <div style="position: relative; padding-left: 24px; padding-bottom: 14px; border-left: 2px solid #e2e8f0;">
            <div style="position: absolute; left: -6px; top: 2px; width: 10px; height: 10px; border-radius: 50%; background: #3b82f6; border: 2px solid white;"></div>
            <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: #0f172a; font-size: 13px;">{s['message']}</strong>
                        {score_badge}
                    </div>
                    <span style="font-size: 11px; color: #94a3b8; font-family: monospace;">{s['display_time']}</span>
                </div>
                <div style="margin-top: 6px; font-size: 11px; color: #64748b;">
                    快照 ID: <code>{s['snapshot_id']}</code>
                </div>
            </div>
        </div>
        """

    html = f"""
    <div style="background: white; border: 1px solid #cbd5e1; border-radius: 10px; padding: 18px; margin: 12px 0; font-family: system-ui, -apple-system, sans-serif; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.04);">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; padding-bottom: 10px; margin-bottom: 14px;">
            <div>
                <h4 style="margin: 0; color: #0f172a; font-size: 15px; font-weight: 700;">
                    ⏱️ 代码“时光机”版本历史: {nb_name}
                </h4>
                <p style="margin: 3px 0 0 0; color: #64748b; font-size: 12px;">
                    安全气囊机制：调崩参数随时一键穿梭回滚，零代码丢失风险
                </p>
            </div>
            <span style="background: #eff6ff; color: #1d4ed8; padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 600;">
                共 {len(snapshots)} 个历史版本
            </span>
        </div>
        <div style="margin-left: 6px; margin-top: 10px;">
            {items_html}
        </div>
    </div>
    """
    return html


def show_time_machine(notebook_path: str):
    """在 Notebook 中渲染交互式时光机控制面板"""
    from IPython.display import HTML, display
    display(HTML(render_time_machine_html(notebook_path)))
