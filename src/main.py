r"""CLI 演示入口：零凭证跑通「问题 → 工具 → 证据 → 护栏」。

    python -m src.main "农机补贴对持仓的影响"
    python -m src.main --trace "农机补贴对持仓的影响"    # 打印每一步的决策与观察
"""
from __future__ import annotations

import json
import sys

from . import orchestrator


def _brief(result) -> str:
    text = json.dumps(result, ensure_ascii=False)
    return text if len(text) <= 180 else text[:180] + "…"


def main() -> int:
    argv = sys.argv[1:]
    show_trace = "--trace" in argv
    argv = [item for item in argv if item != "--trace"]
    question = argv[0] if argv else "农机补贴对持仓的影响"

    history = orchestrator.run_steps(question)

    if show_trace:
        for step in history:
            print("[%d] %s" % (step["step"], step["thought"]))
            print("    action : %s %s" % (
                step["action"], json.dumps(step["args"], ensure_ascii=False)))
            print("    observe: %s" % _brief(step["result"]))
            print("    source : %s" % step["source"])
        if not history:
            print("（没有执行任何工具）")
        print()

    print(orchestrator.render(question, history))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
