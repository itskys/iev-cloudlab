#!/usr/bin/env python3
"""test_step2_deep_engineering.py
全面验证 Step 2 (深度工程与可视化增强) 的四大核心组件:
1. C1 / C2 动力流与能量损耗瀑布图 (Powertrain Energy Waterfall)
2. A1 智驾感知视场 HUD、激光测距标尺与急刹滑移胎痕 (BEV FoV, Spacing Ruler & Skid Marks)
3. D4 电芯微观剖面电位梯度与枝晶析锂动态机理 (1D Newman Potential Gradient & Dendrite Plating)
4. 跨域工程数据血缘交互式拓扑图 (Cross-Domain Engineering Data Lineage DAG in Student Cockpit)
"""

import sys
import os
import unittest
import numpy as np

# Ensure labs can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'labs')))

class TestStep2DeepEngineering(unittest.TestCase):
    def test_01_student_cockpit_dag_integration(self):
        """测试驾驶舱中血缘拓扑 DAG 的生成与嵌入"""
        from common.student_cockpit import render_data_lineage_dag_svg, render_student_cockpit_html
        from common.skills_profiler import compute_student_skill_profile

        # 模拟不同学生实验得分
        test_scores = {
            "D3_ocv_soc": {"passed": True, "score": 95},
            "C1_fastsim": {"passed": True, "score": 88},
            "C4_ecms": {"passed": False, "score": 45},
            "A1_cutin_aeb": {"passed": True, "score": 90},
            "A2_acc_track": {"passed": True, "score": 82},
            "B1_idm_fitting": {"passed": True, "score": 85},
            "Capstone_iev_integrated": {"passed": False, "score": 0}
        }
        svg_out = render_data_lineage_dag_svg(test_scores)
        self.assertIn("<svg", svg_out)
        self.assertIn("</svg>", svg_out)
        self.assertIn("D3", svg_out)
        self.assertIn("Capstone", svg_out)
        self.assertIn("ocv_soc.csv", svg_out)
        self.assertIn("stroke=\"#10b981\"", svg_out) # 已达标连线

        # 验证完整 cockpit html 渲染
        skill_profile = compute_student_skill_profile(test_scores)
        mock_progress = {
            'n_done': 6,
            'n_required': 29,
            'completion_rate': 20.7,
            'fair_total_score': 18.5,
            'submitted_avg_score': 81.0,
            'skill_profile': skill_profile,
            'recommendations': [],
            'scores': test_scores
        }
        html_out = render_student_cockpit_html(mock_progress, student_name="张三")
        self.assertIn("跨域工程数据血缘与全域链路拓扑图", html_out)
        self.assertIn("三链汇流贯通", html_out)
        self.assertIn("<svg", html_out)
        print("✓ [DAG & Student Cockpit] Passed integration check.")

    def test_02_a1_lite_driver_and_visualizer3d(self):
        """测试 A1 lite 驱动返回指标与 BEV 激光测距、胎痕渲染"""
        from common.lite_drivers import run_a1_lite, a1_replay

        # 运行一次 A1 lite 仿真
        res = run_a1_lite(ttc_threshold=2.5)
        self.assertIn("ttcs", res)
        self.assertIn("aeb_actives", res)
        self.assertIn("gaps", res)
        self.assertEqual(len(res["ttcs"]), len(res["times"]))
        self.assertEqual(len(res["aeb_actives"]), len(res["times"]))

        # 验证 a1_replay 构建
        replay_obj = a1_replay(res)
        html_repr = getattr(replay_obj, 'data', str(replay_obj))
        # 验证 visualizer3d 包含激光测距标尺和胎痕绘制逻辑
        self.assertIn("激光测距", html_repr)
        self.assertIn("skid marks", html_repr.lower())
        self.assertIn("ttc", html_repr.lower())
        print("✓ [A1 BEV Radar & Skid Marks] Passed simulation and visualizer check.")

    def test_03_c1_energy_waterfall(self):
        """测试 C1 能量瀑布图逻辑与探索器构建"""
        from common.lab_explorers import show_c1_explorer
        # 确保无异常抛出
        try:
            show_c1_explorer()
        except Exception as e:
            self.fail(f"show_c1_explorer failed with error: {e}")
        print("✓ [C1 Energy Waterfall] Passed explorer instantiate check.")

    def test_04_d4_1d_newman_dendrite_profile(self):
        """测试 D4 1D 微观剖面与枝晶析锂机理图探索器构建"""
        from common.lab_explorers import show_d4_explorer
        # 确保无异常抛出
        try:
            show_d4_explorer()
        except Exception as e:
            self.fail(f"show_d4_explorer failed with error: {e}")
        print("✓ [D4 1D Newman & Dendrite Profile] Passed explorer instantiate check.")

if __name__ == '__main__':
    unittest.main()
