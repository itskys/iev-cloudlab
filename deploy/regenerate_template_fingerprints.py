#!/usr/bin/env python3
"""Regenerate labs/common/template_fingerprints.json from current Pro masters.

Why this exists (2026-10-31, P1 plagiarism fix):
  The checker (plagiarism_detector.scan_class_code_plagiarism) excludes a
  student's cell from the plagiarism pool only when the cell's AST sequence
  exactly matches a fingerprint in template_fingerprints.json. The old JSON
  was built by a different extractor that recorded ALL node types
  (Module, Import, alias, Name, Store, ...), while the current
  get_ast_sequence() records only 12 structural types
  (Assign, BinOp, UnaryOp, Compare, If, For, While, Call, FunctionDef,
  Return, Attribute, Subscript). Nothing matched, so untouched-template
  students were flagged at 100% similarity.
  This generator uses the SAME get_ast_sequence() the scanner uses, so
  fingerprints match by construction. Re-run it whenever a Pro master
  notebook's code cells change.

Usage (on the VPS):
  python3 deploy/regenerate_template_fingerprints.py \
      --src /opt/ievlab/scenarios \
      --out /opt/ievlab/scenarios/labs/common/template_fingerprints.json
"""

import argparse
import importlib.util
import json
import os


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", default="/opt/ievlab/scenarios",
                    help="Directory containing notebooks/ (VPS layout)")
    ap.add_argument("--out", default="",
                    help="Output JSON path (default: <src>/labs/common/template_fingerprints.json)")
    args = ap.parse_args()

    detector_path = os.path.join(args.src, "labs", "common", "plagiarism_detector.py")
    pd = load_module("plagiarism_detector", detector_path)
    out_path = args.out or os.path.join(args.src, "labs", "common", "template_fingerprints.json")
    nb_dir = os.path.join(args.src, "notebooks")

    fingerprints = {}
    for fname in sorted(os.listdir(nb_dir)):
        if not fname.endswith("_pro.ipynb"):
            continue
        key = fname[:-len(".ipynb")].replace("_pro", "")
        with open(os.path.join(nb_dir, fname), "r", encoding="utf-8") as f:
            data = json.load(f)
        seqs = set()
        for cell in data.get("cells", []):
            if cell.get("cell_type") != "code":
                continue
            src = "".join(cell.get("source", [])).strip()
            clean_lines = [l for l in src.splitlines() if not l.startswith(("%", "!"))]
            code = "\n".join(clean_lines).strip()
            if not code:
                continue
            seq = pd.get_ast_sequence(code)
            if seq:
                seqs.add(tuple(seq))
        fingerprints[key] = sorted(list(seqs))

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(fingerprints, f, ensure_ascii=False, indent=1)
    total = sum(len(v) for v in fingerprints.values())
    print(f"Wrote {out_path}: {len(fingerprints)} experiments, {total} fingerprints")
    for key in sorted(fingerprints):
        print(f"  {key}: {len(fingerprints[key])}")


if __name__ == "__main__":
    main()
