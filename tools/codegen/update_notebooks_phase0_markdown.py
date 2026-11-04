#!/usr/bin/env python3
"""update_notebooks_phase0_markdown.py
将 30 个 Pro 实验 Notebook 的阶段零 (Phase 0) Markdown 引导文案升级：
加入教师一键快照对标、行业车规量规锚点与一键恢复默认的直观使用提示。
"""

import os
import glob
import json

OLD_PATTERNS = [
    "> 💡 **给初学者的直观模式 (Novice Mode)**：\n> - **零代码调参**：",
    "> 💡 **给初学者的直观模式 (Novice Mode)**：\n> - **零代码调参**",
]

NEW_REPLACEMENT = """> 💡 **给初学者与教师演示的直观模式 (Novice & Teacher Demo Mode)**：
> - **🎯 教师一键案例快照对标**：点击下方【典型工况快照】按钮，自动加载典型车规对比工况并即时推演；
> - **📐 行业车规量规物理锚点**：实时对照行业车规与真实车型工程规范对标标签；
> - **↺ 一键恢复出厂默认**：随时点击【↺ 恢复默认】重置回出厂基准状态；
> - **零代码手动调参**："""

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    nb_files = sorted(glob.glob(os.path.join(repo_root, "notebooks", "*_pro.ipynb")))

    updated_count = 0
    for path in nb_files:
        with open(path, "r", encoding="utf-8") as f:
            nb = json.load(f)

        modified = False
        for cell in nb.get("cells", []):
            if cell.get("cell_type") != "markdown":
                continue
            src = "".join(cell.get("source", []))
            if "阶段零" in src or "Phase 0" in src:
                for old in OLD_PATTERNS:
                    if old in src:
                        new_src = src.replace(old, NEW_REPLACEMENT)
                        # convert back to lines for notebook
                        cell["source"] = [line + "\n" for line in new_src.split("\n")[:-1]] + [new_src.split("\n")[-1]]
                        modified = True
                        break

        if modified:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(nb, f, ensure_ascii=False, indent=1)
            updated_count += 1
            print(f"✅ Updated Phase 0 markdown in: {os.path.basename(path)}")

    print(f"\n🎉 Total notebooks updated: {updated_count}/{len(nb_files)}")

if __name__ == "__main__":
    main()
