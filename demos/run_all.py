#!/usr/bin/env python3
"""一键离线验证 12 章 demo：零 API 费用、不需要任何 key，适合 CI / 提交前自检。

    python demos/run_all.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

DEMOS = Path(__file__).resolve().parent
ROOT = DEMOS.parent
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}


def main() -> int:
    files = sorted(DEMOS.glob("demo_*.py"))
    if not files:
        print("未找到 demo 文件")
        return 1
    passed = []
    for file in files:
        try:
            proc = subprocess.run(
                [sys.executable, str(file), "--offline"],
                cwd=str(ROOT), env=ENV, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120)
        except subprocess.TimeoutExpired:
            print(f"[FAIL] {file.name} 超时（120s）")
            continue
        if proc.returncode == 0:
            print(f"[PASS] {file.name}")
            passed.append(file.name)
        else:
            print(f"[FAIL] {file.name}")
            print((proc.stdout + proc.stderr)[-1500:])
    print(f"\n{len(passed)}/{len(files)} 个 demo 通过（全部离线，零 API 费用）")
    return 0 if len(passed) == len(files) else 1


if __name__ == "__main__":
    sys.exit(main())
