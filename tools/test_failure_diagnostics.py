#!/usr/bin/env python3
"""test_failure_diagnostics.py
全面测试 Step 3 汽车工程失效归因与智能调试助理系统 (Automotive Failure Attribution & Diagnostic Tutor)
覆盖：
1. 29 门实验 + Capstone 全知识库机理故障树
2. 严重等级、物理方程因果、调参处方矩阵、主机厂对标规范
3. evaluator.grade_metrics 自动诊断集成
4. student_cockpit 驾驶舱失效归因看板渲染
5. explain_failure 终端输出
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'labs')))

class TestFailureDiagnostics(unittest.TestCase):
    def test_01_healthy_diagnostics(self):
        """测试健康指标不触发异常误报"""
        from common.copilot import diagnose_experiment

        # A1 正常避险
        res_a1 = diagnose_experiment('A1_cutin_aeb', {'collision': False, 'min_ttc_s': 2.1})
        self.assertTrue(res_a1['is_healthy'])
        self.assertEqual(res_a1['findings_count'], 0)

        # C1 正常电耗
        res_c1 = diagnose_experiment('C1_fastsim_energy', {'energy_kwh_100km': 13.2})
        self.assertTrue(res_c1['is_healthy'])

        # D4 正常快充且大倍率复现析锂
        res_d4 = diagnose_experiment('D4_lithium_plating', {'min_potential_3c_v': -0.45})
        self.assertTrue(res_d4['is_healthy'])
        print("✓ [Healthy Diagnostics] Checked normal metrics pass without false alarms.")

    def test_02_track_a_adas_failures(self):
        """测试 Track A 智驾感知规控失效诊断 (碰撞、TTC紧迫、间距超标)"""
        from common.copilot import diagnose_experiment, render_copilot_card

        # 模拟 A1 碰撞
        res_a1 = diagnose_experiment('A1_cutin_aeb', {'collision': True, 'min_ttc_s': 0.4})
        self.assertFalse(res_a1['is_healthy'])
        f = res_a1['findings'][0]
        self.assertEqual(f['severity'], 'critical')
        self.assertIn("加塞切入", f['physics_root_cause'])
        self.assertIn("Euro NCAP", f['oem_benchmark'])
        self.assertTrue(len(f['tuning_matrix']) >= 2)
        self.assertIn("ttc_threshold", [t['param'] for t in f['tuning_matrix']])

        card_html = render_copilot_card(res_a1)
        self.assertIn("ACTION REQUIRED", card_html)
        self.assertIn("推荐调参处方矩阵", card_html)

        # 模拟 A2 ACC 跟车间距误差超标
        res_a2 = diagnose_experiment('A2_acc_follow', {'max_spacing_error_m': 2.8})
        self.assertFalse(res_a2['is_healthy'])
        self.assertIn("ISO 15622", res_a2['findings'][0]['oem_benchmark'])
        print("✓ [Track A Diagnostics] Checked ADAS collision & spacing error attribution.")

    def test_03_track_b_traffic_and_v2x_failures(self):
        """测试 Track B 交通流与车车通信失效诊断 (CACC弦不稳、激波反向)"""
        from common.copilot import diagnose_experiment

        # 模拟 B3 CACC 编队弦不稳定
        res_b3 = diagnose_experiment('B3_sumo_cacc', {'max_spacing_error': 3.2, 'steps': 350})
        self.assertFalse(res_b3['is_healthy'])
        f_b3 = res_b3['findings'][0]
        self.assertEqual(f_b3['severity'], 'critical')
        self.assertIn("弦不稳定", f_b3['symptom'])
        self.assertIn("前馈", f_b3['physics_root_cause'])

        # 模拟 B4 冲击波速度异常为正
        res_b4 = diagnose_experiment('B4_congestion_wave', {'wave_speed_kmh': 4.5, 'r_squared': 0.7})
        self.assertFalse(res_b4['is_healthy'])
        self.assertIn("LWR", res_b4['findings'][0]['physics_root_cause'])
        print("✓ [Track B Diagnostics] Checked V2X string instability & LWR shockwave attribution.")

    def test_04_track_c_and_d_powertrain_and_battery(self):
        """测试 Track C & D 动力总成电耗与电池电化学失效诊断"""
        from common.copilot import diagnose_experiment

        # 模拟 C1 电耗超标
        res_c1 = diagnose_experiment('C1_fastsim_energy', {'energy_kwh_100km': 25.8})
        self.assertFalse(res_c1['is_healthy'])
        self.assertIn("再生制动", res_c1['findings'][0]['physics_root_cause'])

        # 模拟 D3 OCV-SOC 拟合标定误差超标
        res_d3 = diagnose_experiment('D3_ocv_soc_export', {'calibration_error_pct': 7.2})
        self.assertFalse(res_d3['is_healthy'])
        self.assertIn("固相扩散", res_d3['findings'][0]['physics_root_cause'])
        print("✓ [Track C & D Diagnostics] Checked energy flow & battery electrochemical attribution.")

    def test_05_track_e_mpc_and_capstone(self):
        """测试 Track E MPC 求解器超时与 Capstone 全域大作业冲突"""
        from common.copilot import diagnose_experiment

        # 模拟 E3 MPC 求解耗时超标
        res_e3 = diagnose_experiment('E3_mpc_follow', {'avg_solve_ms': 75.0})
        self.assertFalse(res_e3['is_healthy'])
        self.assertEqual(res_e3['findings'][0]['severity'], 'critical')
        self.assertIn("IPOPT", res_e3['findings'][0]['physics_root_cause'])
        self.assertIn("ISO 26262", res_e3['findings'][0]['oem_benchmark'])

        # 模拟 Capstone 避险失败
        res_cap = diagnose_experiment('Capstone_iev_integrated', {'collision': True, 'min_ttc_s': 0.9, 'window_net_kwh': 0.02})
        self.assertFalse(res_cap['is_healthy'])
        self.assertIn("仲裁", res_cap['findings'][0]['physics_root_cause'])
        print("✓ [Track E & Capstone Diagnostics] Checked MPC real-time watchdog & Capstone arbitration.")

    def test_06_evaluator_integration(self):
        """测试 evaluator.grade_metrics 自动集成机理诊断"""
        from common.evaluator import grade_metrics

        # 评测一个未通过的 A1 指标
        grade_res = grade_metrics('A1_cutin_aeb', {'collision': True, 'min_ttc_s': 0.7})
        self.assertFalse(grade_res['passed'])
        self.assertIn('diagnosis', grade_res)
        self.assertIn('diagnosis_html', grade_res)
        self.assertIn("Actionable Parameter Tuning Matrix", grade_res['diagnosis_html'])

        # 评测一个通过的 A1 指标
        grade_ok = grade_metrics('A1_cutin_aeb', {'collision': False, 'min_ttc_s': 2.3})
        self.assertTrue(grade_ok['passed'])
        self.assertIn('diagnosis', grade_ok)
        self.assertTrue(grade_ok['diagnosis']['is_healthy'])
        print("✓ [Evaluator Integration] Verified grade_metrics automatically attaches diagnostic intelligence.")

    def test_07_student_cockpit_failure_section(self):
        """测试学生驾驶舱自动为未通过实验展示调参处方"""
        from common.student_cockpit import render_student_cockpit_html
        from common.skills_profiler import compute_student_skill_profile

        test_scores = {
            "A1_cutin_aeb": {"passed": False, "score": 40.0, "metrics": {"collision": True, "min_ttc_s": 0.5}},
            "B3_sumo_cacc": {"passed": False, "score": 45.0, "metrics": {"max_spacing_error": 3.0}},
            "C1_fastsim_energy": {"passed": True, "score": 90.0, "metrics": {"energy_kwh_100km": 12.8}},
        }
        mock_progress = {
            'n_done': 3,
            'n_required': 29,
            'completion_rate': 10.3,
            'fair_total_score': 17.5,
            'submitted_avg_score': 58.3,
            'skill_profile': compute_student_skill_profile(test_scores),
            'recommendations': [],
            'scores': test_scores,
        }
        html_out = render_student_cockpit_html(mock_progress, student_name="李四")
        self.assertIn("待攻坚实验智能失效归因与调优处方", html_out)
        self.assertIn("Cut-in 加塞紧急避险", html_out)
        self.assertIn("CACC 编队控制与弦稳定性", html_out)
        self.assertIn("推荐调参处方矩阵", html_out)
        print("✓ [Student Cockpit Integration] Verified cockpit displays actionable failure prescriptions.")

    def test_08_explain_failure_cli(self):
        """测试 CLI 文本输出"""
        from common.copilot import explain_failure

        text_out = explain_failure('A1_cutin_aeb', {'collision': True, 'min_ttc_s': 0.6})
        self.assertIn("智能工程诊断发现", text_out)
        self.assertIn("物理根因", text_out)
        self.assertIn("推荐调参", text_out)
        self.assertIn("ttc_threshold", text_out)
        print("✓ [CLI Explain Failure] Verified terminal text summary generation.")

if __name__ == '__main__':
    unittest.main()
