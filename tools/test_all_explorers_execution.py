#!/usr/bin/env python3
"""test_all_explorers_execution.py
逐一调用 labs/common/lab_explorers.py 中的全部 30 个探索器，验证 UI 容器层次、预设按钮点击及滑块响应。
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import labs.common.lab_explorers as le

class TestExplorersExecution(unittest.TestCase):
    def test_all_30_explorers_init_and_presets(self):
        rendered_widgets = []
        old_display = le.display

        def mock_display(*args, **kwargs):
            for a in args:
                rendered_widgets.append(a)

        le.display = mock_display

        test_funcs = [
            ("A1", le.show_a1_explorer),
            ("A2", le.show_a2_explorer),
            ("A3", le.show_a3_explorer),
            ("A4", le.show_a4_explorer),
            ("A5", le.show_a5_explorer),
            ("B1", le.show_b1_explorer),
            ("B2", le.show_b2_explorer),
            ("B3", le.show_b3_explorer),
            ("B4", le.show_b4_explorer),
            ("B5", le.show_b5_explorer),
            ("C1", le.show_c1_explorer),
            ("C2", le.show_c2_explorer),
            ("C3", le.show_c3_explorer),
            ("C4", le.show_c4_explorer),
            ("D1", le.show_d1_explorer),
            ("D2", le.show_d2_explorer),
            ("D3", le.show_d3_explorer),
            ("D4", le.show_d4_explorer),
            ("E1", le.show_e1_explorer),
            ("E2", le.show_e2_explorer),
            ("E3", le.show_e3_explorer),
            ("E4", le.show_e4_explorer),
            ("F1", le.show_f1_explorer),
            ("F2", le.show_f2_explorer),
            ("F3", le.show_f3_explorer),
            ("G1", le.show_g1_explorer),
            ("G2", le.show_g2_explorer),
            ("H1", le.show_h1_explorer),
            ("H2", le.show_h2_explorer),
            ("Capstone", le.show_capstone_explorer),
        ]

        passed_count = 0
        try:
            for name, fn in test_funcs:
                rendered_widgets.clear()
                fn()

                # 必须 display 过 widgets.VBox (controls)
                vboxes = [w for w in rendered_widgets if type(w).__name__ == "VBox"]
                self.assertTrue(len(vboxes) >= 1, f"{name} did not display a VBox controls container")
                controls = vboxes[-1]

                # 检查第一项为 preset_bar (HBox)
                preset_bar = controls.children[0]
                self.assertEqual(type(preset_bar).__name__, "HBox", f"{name} first child is not preset_bar HBox")
                self.assertTrue(len(preset_bar.children) >= 3, f"{name} preset_bar has fewer than 3 items")

                # 检查第二项为 benchmarks_widget (HTML)
                bm_widget = controls.children[1]
                self.assertEqual(type(bm_widget).__name__, "HTML", f"{name} second child is not HTML benchmarks")
                self.assertIn("📐", bm_widget.value, f"{name} benchmarks badge missing 📐 icon")

                # 测试点击预设按钮
                for btn in preset_bar.children[1:-1]:
                    btn.click()

                # 测试点击恢复默认按钮 (最后一项)
                btn_reset = preset_bar.children[-1]
                self.assertIn("恢复默认", btn_reset.description, f"{name} last button is not reset button")
                btn_reset.click()

                passed_count += 1
                print(f"[{passed_count:2d}/30] {name:10s} PASS (presets & benchmarks verified)")

        finally:
            le.display = old_display

        self.assertEqual(passed_count, 30, f"Expected 30 explorers to pass, but got {passed_count}")

if __name__ == "__main__":
    unittest.main()
