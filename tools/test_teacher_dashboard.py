#!/usr/bin/env python3
"""test_teacher_dashboard.py
全面测试 Step 4 教师演示大屏与学情全景洞察看板 (Instructor Live Presentation Dashboard)
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'labs')))

class TestTeacherDashboard(unittest.TestCase):
    def test_01_class_failure_analytics(self):
        """测试全班高频失效统计聚合并输出 Top 5"""
        from common.teacher_dashboard import compute_class_failure_analytics

        analytics = compute_class_failure_analytics()
        self.assertIn('total_students', analytics)
        self.assertIn('total_submissions', analytics)
        self.assertIn('top_failures', analytics)
        self.assertTrue(len(analytics['top_failures']) > 0)
        self.assertTrue(len(analytics['top_failures']) <= 5)

        first_failure = analytics['top_failures'][0]
        self.assertIn('symptom', first_failure)
        self.assertIn('physics_root_cause', first_failure)
        self.assertIn('severity', first_failure)
        self.assertIn('occurrences', first_failure)
        self.assertTrue(first_failure['occurrences'] > 0)
        print("✓ [Failure Analytics] Verified class failure aggregation and Top 5 ranking.")

    def test_02_side_by_side_comparison(self):
        """测试优秀方案 vs 典型受阻方案同屏对标视窗渲染"""
        from common.teacher_dashboard import render_side_by_side_comparison_html, SIDE_BY_SIDE_CASES

        # 测试 A1, B3, C1, D4, E3 对标
        for exp_id in ['A1_cutin_aeb', 'B3_sumo_cacc', 'C1_fastsim_energy', 'D4_lithium_plating', 'E3_mpc_follow']:
            self.assertIn(exp_id, SIDE_BY_SIDE_CASES)
            html_out = render_side_by_side_comparison_html(exp_id)
            self.assertIn("优秀满分工程方案", html_out)
            self.assertIn("典型受阻方案", html_out)
            self.assertIn("核心控制参数标定", html_out)
            self.assertIn("教学示意动态曲线对比", html_out)
        print("✓ [Side-by-Side Comparison] Verified dual-column golden vs failed comparisons.")

    def test_03_teacher_live_dashboard_html(self):
        """测试教师多媒体演示中心大屏渲染"""
        from common.teacher_dashboard import render_teacher_live_dashboard_html

        html_out = render_teacher_live_dashboard_html()
        self.assertIn("教师多媒体演示中心与学情全景洞察看板", html_out)
        self.assertIn("全班 8 大工程能力达成度分布", html_out)
        self.assertIn("全班高频机理失效模式排行榜", html_out)
        self.assertIn("课堂同屏对标演示器", html_out)
        self.assertIn("Capstone 通关", html_out)
        print("✓ [Teacher Live Dashboard] Verified dashboard HTML layout and sections.")

    def test_04_debrief_markdown_export(self):
        """测试课堂讲评教案与学期分析简报 Markdown 导出"""
        from common.teacher_dashboard import export_teacher_debrief_markdown

        md_out = export_teacher_debrief_markdown()
        self.assertIn("# 🎓", md_out)
        self.assertIn("全班总体学情关键指标", md_out)
        self.assertIn("全班高频机理失效排行榜与讲评要点", md_out)
        self.assertIn("物理第一性原理因果", md_out)
        print("✓ [Debrief Markdown Export] Verified lesson plan markdown generation.")

if __name__ == '__main__':
    unittest.main()
