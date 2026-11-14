"""CLI 演示入口：零凭证跑通「问题 → 工具 → 证据 → 护栏」。"""
from __future__ import annotations

import sys

from .orchestrator import run


def main() -> int:
    question = sys.argv[1] if len(sys.argv) > 1 else "农机补贴对持仓的影响"
    print(run(question))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
