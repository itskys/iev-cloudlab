#!/usr/bin/env python3
"""test_explorers_presets.py
测试 labs/common/lab_explorers.py 中全部 30 个实验的教师一键预设与行业量规锚点
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import labs.common.lab_explorers as le

class TestExplorersPresets(unittest.TestCase):
    def test_helpers_exist(self):
        self.assertTrue(hasattr(le, "_create_benchmark_badge"))
        self.assertTrue(hasattr(le, "_create_preset_bar"))

    def test_all_30_explorers_present(self):
        explorers = [
            le.show_a1_explorer, le.show_a2_explorer, le.show_a3_explorer, le.show_a4_explorer, le.show_a5_explorer,
            le.show_b1_explorer, le.show_b2_explorer, le.show_b3_explorer, le.show_b4_explorer, le.show_b5_explorer,
            le.show_c1_explorer, le.show_c2_explorer, le.show_c3_explorer, le.show_c4_explorer,
            le.show_d1_explorer, le.show_d2_explorer, le.show_d3_explorer, le.show_d4_explorer,
            le.show_e1_explorer, le.show_e2_explorer, le.show_e3_explorer, le.show_e4_explorer,
            le.show_f1_explorer, le.show_f2_explorer, le.show_f3_explorer,
            le.show_g1_explorer, le.show_g2_explorer,
            le.show_h1_explorer, le.show_h2_explorer,
            le.show_capstone_explorer
        ]
        self.assertEqual(len(explorers), 30)

    def test_preset_bar_logic(self):
        if not le._HAS_WIDGETS:
            print("Widgets not installed in test environment, skipping live widget click test.")
            return

        import ipywidgets as widgets
        slider1 = widgets.FloatSlider(value=3.0, min=1.0, max=5.0)
        slider2 = widgets.IntSlider(value=50, min=10, max=100)

        presets = [
            {"title": "P1", "values": {"s1": 1.5, "s2": 80}},
            {"title": "P2", "values": {"s1": 4.5, "s2": 20}},
        ]
        defaults = {"s1": 3.0, "s2": 50}
        setters = {"s1": slider1, "s2": slider2}
        callback_called = [False]

        def dummy_cb():
            callback_called[0] = True

        bar = le._create_preset_bar(presets, defaults, setters, dummy_cb)
        self.assertIsNotNone(bar)
        # children: Label + Button(P1) + Button(P2) + Button(Reset)
        self.assertEqual(len(bar.children), 4)

        # Click P1 button (index 1)
        btn_p1 = bar.children[1]
        btn_p1.click()
        self.assertEqual(slider1.value, 1.5)
        self.assertEqual(slider2.value, 80)
        self.assertTrue(callback_called[0])

        # Click Reset button (index 3)
        callback_called[0] = False
        btn_reset = bar.children[3]
        btn_reset.click()
        self.assertEqual(slider1.value, 3.0)
        self.assertEqual(slider2.value, 50)
        self.assertTrue(callback_called[0])

    def test_benchmark_badge_logic(self):
        if not le._HAS_WIDGETS:
            return
        badge = le._create_benchmark_badge(
            "测试量规",
            [("指标A", "1.0~2.0", "info"), ("指标B", "< 0.5", "danger")],
            "对标 ISO 9999"
        )
        self.assertIsNotNone(badge)
        self.assertIn("测试量规", badge.value)
        self.assertIn("指标A", badge.value)
        self.assertIn("对标 ISO 9999", badge.value)

if __name__ == "__main__":
    unittest.main()
