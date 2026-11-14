"""编排器：ReAct 循环。

真实部署时，plan/step 由 LLM 完成（用 config 里的 openai-compatible 模型）；
本示例用轻量关键词路由模拟，保证零依赖、零凭证即可跑通整条链路，
便于展示「问题 → 选工具 → 取证据 → 过护栏」的闭环。
"""
from __future__ import annotations

import json

from . import tools
from .guardrails import finalize


def _route(question: str) -> str:
    q = question
    if any(k in q for k in ("重叠", "持仓", "暴露", "穿透")):
        return "analyze_overlap"
    if any(k in q for k in ("回测", "涨跌", "历史表现", "事件后")):
        return "run_event_study"
    if any(k in q for k in ("报告", "写一份")):
        return "compose_report"
    if any(k in q for k in ("影响", "机制", "哪些行业", "哪类资产")):
        return "map_event_to_etf"
    return "search_policy"


def run(question: str, max_steps: int = 4) -> str:
    steps = []
    for _ in range(max_steps):
        tool_id = _route(question)
        args = _guess_args(tool_id, question)
        result = tools.invoke(tool_id, json.dumps(args, ensure_ascii=False))
        steps.append((tool_id, result))
        if tool_id == "compose_report":
            break
        if result.get("error"):
            break
    body = _compose(question, steps)
    ok, out = finalize(body)
    if not ok:
        # 不过关：降级为证据包
        out = f"结论：无法形成合规结论，以下为原始证据包（供人工核验）。\n\n{json.dumps(steps, ensure_ascii=False, indent=2)}\n\n本示例仅作技术演示。"
    return out


def _guess_args(tool_id: str, question: str) -> dict:
    if tool_id == "analyze_overlap":
        return {"codes": ["512480", "159992"]}
    if tool_id == "run_event_study":
        return {"event_id": "ev_demo_001", "window": 20}
    if tool_id == "compose_report":
        return {"question": question, "require_evidence": True}
    if tool_id == "map_event_to_etf":
        return {"event_id": "ev_demo_001"}
    return {"query": question, "top_k": 3}


def _compose(question: str, steps) -> str:
    # mock 合成：只把工具返回拼成结论，不含真实领域逻辑
    hits = [s for s in steps if isinstance(s[1], dict) and "error" not in s[1]]
    return f"结论：针对「{question}」，演示链路调用 {len(steps)} 步，命中 {len(hits)} 个工具；所有结果均带证据标识（evidence_id），依据见各工具返回。"
