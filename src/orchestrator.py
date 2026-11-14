"""编排器：ReAct 循环。

每一步都是 Reason → Act → Observe：
  Reason   reasoner.decide(question, history)  看问题，也看前面几步的观察结果
  Act      tools.invoke(action, args)          调一个工具
  Observe  结果追加进 history                  下一轮 Reason 能看到它

配了 LLM_API_KEY 时 Reason 走大模型，否则回退规则；两条路径都能跑通，
区别只在于「下一步」是不是真的看过上一轮的结果再做决定。
"""
from __future__ import annotations

import json

from . import reasoner, tools
from .guardrails import finalize


def run_steps(question: str, max_steps: int = 6, decide=None) -> list[dict]:
    """跑完整个循环，返回每一步的 thought / action / args / result。"""
    decide = decide or reasoner.decide
    history: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for _ in range(max_steps):
        decision = decide(question, history)
        if decision.action == "final":
            break

        signature = (decision.action, json.dumps(decision.args, sort_keys=True, ensure_ascii=False))
        if signature in seen:          # 同一个工具、同一组参数：模型在原地打转
            break
        seen.add(signature)

        result = tools.invoke(decision.action, json.dumps(decision.args, ensure_ascii=False))
        history.append({
            "step": len(history) + 1,
            "thought": decision.thought,
            "action": decision.action,
            "args": decision.args,
            "result": result,
            "source": decision.source,
        })

        if decision.action == "compose_report":
            break
        if isinstance(result, dict) and result.get("error"):
            break

    return history


def _compose(question: str, history: list[dict]) -> str:
    if not history:
        return "结论：没有调用到任何工具，无法回答「%s」；请检查输入后重试。" % question

    chain = " → ".join(step["action"] for step in history)
    evidence = []
    for step in history:
        result = step.get("result") or {}
        if isinstance(result, dict) and result.get("evidence_id"):
            evidence.append(str(result["evidence_id"]))
    evidence_text = "、".join(evidence) if evidence else "（无）"

    return ("结论：针对「%s」，按 %s 依次取证共 %d 步，证据标识 %s；"
            "各步返回值见证据包，具体机制与阈值以原文为准。"
            % (question, chain, len(history), evidence_text))


def render(question: str, history: list[dict]) -> str:
    """合稿 + 过护栏；不合规就降级为证据包，不强行成文。"""
    ok, out = finalize(_compose(question, history))
    if ok:
        return out
    return ("结论：无法形成合规结论，以下为原始证据包（供人工核验）。\n\n"
            + json.dumps(history, ensure_ascii=False, indent=2)
            + "\n\n本示例仅作技术演示。")


def run(question: str, max_steps: int = 6, decide=None) -> str:
    return render(question, run_steps(question, max_steps, decide))
