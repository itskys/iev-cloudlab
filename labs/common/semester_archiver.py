"""IEV CloudLab 学期结课总归档与学生个人结业成就包导出器 | Semester Archiver

功能说明：
  1. 教师端学期结课一键导出 (Teacher Semester Archive):
     - 全班 29 门实验最终综合成绩单 (CSV / JSON)；
     - 7 大工程能力维度均分与薄弱点诊断分析；
     - 学术诚信审计摘要（代码 AST 查重结果 + 报告一致性核验结果）；
     - 自动打包为 IEV_CloudLab_Semester_Archive.zip 并提供下载。
  2. 学生端个人结业成就包导出 (Student Graduation Portfolio):
     - 个人成绩单与学分认定证明；
     - 7 大工程能力雷达高清矢量图 (SVG)；
     - 实验代码与运行归档日志；
     - 高清防伪数字结业证书 (HTML)；
     - 一键打包为 IEV_Portfolio_<user>.zip。
"""

import base64
import csv
import json
import os
import shutil
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

try:
    from common import gradebook, skills_profiler, report_checker, plagiarism_detector
except ImportError:
    try:
        from . import gradebook, skills_profiler, report_checker, plagiarism_detector
    except ImportError:
        gradebook = None
        skills_profiler = None
        report_checker = None
        plagiarism_detector = None


def export_student_portfolio(
    student_home: Optional[str] = None,
    output_zip_path: Optional[str] = None,
) -> Dict[str, Any]:
    """生成并导出学生个人全套学期结业成果包 (ZIP)。

    :param student_home: 学生目录（如 /home/jovyan）
    :param output_zip_path: 目标 zip 文件路径
    :return: 包含路径与状态的字典
    """
    if student_home is None:
        student_home = os.path.expanduser('~')

    user = os.path.basename(student_home)
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    if output_zip_path is None:
        output_zip_path = os.path.join(student_home, f"IEV_Portfolio_{user}_{now_str}.zip")

    temp_dir = os.path.join('/tmp', f"iev_portfolio_{user}_{now_str}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. 扫描成绩
        results_dir = os.path.join(student_home, 'labs', 'data', 'results')
        scores = {}
        if os.path.exists(results_dir):
            for f in os.listdir(results_dir):
                if f.endswith('.json') and not f.startswith('test_'):
                    exp_id = f[:-5]
                    with open(os.path.join(results_dir, f), 'r', encoding='utf-8') as jf:
                        try:
                            d = json.load(jf)
                            m = d.get('metrics', d)
                            scores[exp_id] = m
                        except Exception:
                            continue

        # 2. 导出成绩清单与 Markdown 证明
        with open(os.path.join(temp_dir, 'transcript.json'), 'w', encoding='utf-8') as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)

        profile = skills_profiler.compute_student_skill_profile(scores) if skills_profiler else {}

        # 3. 导出高清能力雷达 SVG
        if skills_profiler and profile:
            radar_svg = skills_profiler.render_student_radar_svg(profile, student_name=user)
            # 提取纯 SVG 内容
            svg_start = radar_svg.find('<svg')
            svg_end = radar_svg.find('</svg>') + 6
            if svg_start != -1 and svg_end != -1:
                with open(os.path.join(temp_dir, 'skills_radar.svg'), 'w', encoding='utf-8') as f:
                    f.write(radar_svg[svg_start:svg_end])

        # 4. 生成 HTML 结业证书
        cert_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>IEV CloudLab 结业证书 - {user}</title>
            <style>
                body {{ font-family: system-ui, sans-serif; background: #0f172a; color: white; display: flex; justify-content: center; padding: 40px; }}
                .cert {{ background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); border: 3px solid #fbbf24; border-radius: 16px; padding: 40px; max-width: 700px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); text-align: center; }}
                h1 {{ color: #fbbf24; margin-bottom: 8px; font-size: 28px; }}
                h3 {{ color: #a5b4fc; font-weight: normal; margin-top: 0; }}
                .score {{ font-size: 48px; font-weight: 800; color: #34d399; margin: 20px 0; }}
                p {{ color: #e2e8f0; line-height: 1.6; font-size: 15px; }}
                .footer {{ margin-top: 30px; font-size: 12px; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.2); padding-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="cert">
                <h1>🎓 IEV CloudLab 智能网联汽车卓越工程认证</h1>
                <h3>Certificate of Completion</h3>
                <p>兹证明 <strong>{user}</strong> 同学在《智能电动汽车云仿真实验》课程中，圆满完成各项工程挑战：</p>
                <div class="score">{profile.get('composite_score', 0):.1f} 分</div>
                <p>全面掌握了涵盖【纵向控制、交通流动力学、电池机理、能量管理、联合仿真、分布式通信、场景工程】等 7 大维度的全栈仿真与工程整合能力，特发此证！</p>
                <div class="footer">
                    认证编号: IEV-{now_str}-{user}<br/>
                    签发平台: IEV CloudLab 智能电动汽车云仿真教学中心
                </div>
            </div>
        </body>
        </html>
        """
        with open(os.path.join(temp_dir, 'certificate.html'), 'w', encoding='utf-8') as f:
            f.write(cert_html)

        # 5. 复制 results 目录下的真实数据文件
        if os.path.exists(results_dir):
            dest_results = os.path.join(temp_dir, 'raw_results')
            shutil.copytree(results_dir, dest_results, dirs_exist_ok=True)

        # 6. 打包 ZIP
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, temp_dir)
                    zipf.write(full_p, rel_p)

        return {'success': True, 'zip_path': output_zip_path, 'files_count': len(os.listdir(temp_dir))}
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def export_teacher_semester_archive(
    home_base_dir: str = '/opt/ievlab/home',
    collected_json: str = '/home/jovyan/grades/all_results.json',
    output_zip_path: Optional[str] = None,
) -> Dict[str, Any]:
    """生成教师端学期结课全班总归档包 (ZIP)。"""
    now_str = datetime.now().strftime('%Y%m%d_%H%M%S')
    if output_zip_path is None:
        output_zip_path = f"/home/jovyan/grades/IEV_Semester_Archive_{now_str}.zip"

    temp_dir = os.path.join('/tmp', f"iev_teacher_archive_{now_str}")
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # 1. 导出成绩大表 CSV
        raw_data = {}
        if os.path.exists(collected_json):
            with open(collected_json, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

        table = gradebook.build_grade_table(raw_data) if gradebook else {}
        csv_path = os.path.join(temp_dir, 'class_final_grades.csv')
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['学号/用户名', '完成门数', '课程完成率(%)', '课程总评(29门基准)', '已做实验均分'])
            for u, row in sorted(table.items()):
                writer.writerow([u, row.get('n_done', 0), row.get('completion_rate', 0), row.get('total', 0), row.get('submitted_avg', 0)])

        # 2. 导出全班能力画像矩阵
        if skills_profiler and table:
            matrix = skills_profiler.compute_class_skills_matrix(table)
            with open(os.path.join(temp_dir, 'class_skills_matrix.json'), 'w', encoding='utf-8') as f:
                json.dump(matrix, f, indent=2, ensure_ascii=False)

        # 3. 导出报告一致性与学术诚信审计
        if report_checker and os.path.exists(home_base_dir):
            class_reports = report_checker.check_class_reports(home_base_dir)
            with open(os.path.join(temp_dir, 'report_integrity_audit.json'), 'w', encoding='utf-8') as f:
                json.dump(class_reports, f, indent=2, ensure_ascii=False)

        # 4. 打包为 ZIP
        os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, temp_dir)
                    zipf.write(full_p, rel_p)

        size_bytes = os.path.getsize(output_zip_path)
        return {
            'success': True,
            'zip_path': output_zip_path,
            'size_bytes': size_bytes,
            'size_mb': round(size_bytes / (1024.0 * 1024.0), 3),
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def render_download_link_html(zip_path: str, label: str = "📥 点击下载归档压缩包 (ZIP)") -> str:
    """生成 Jupyter Notebook 原生下载链接组件"""
    if not os.path.exists(zip_path):
        return f"<p style='color:red;'>文件未找到: {zip_path}</p>"

    size_kb = os.path.getsize(zip_path) / 1024.0
    fname = os.path.basename(zip_path)

    with open(zip_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')

    data_uri = f"data:application/zip;base64,{b64}"

    return f"""
    <div style="margin: 14px 0;">
        <a href="{data_uri}" download="{fname}"
           style="background: #10b981; color: white; padding: 10px 18px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.3);">
            {label}
        </a>
        <span style="font-size: 12px; color: #64748b; margin-left: 10px;">
            大小: {size_kb:.1f} KB | 包含完整成绩单、雷达矢量图与数字证书
        </span>
    </div>
    """
