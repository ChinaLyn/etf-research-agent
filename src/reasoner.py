r"""ReAct 里的 Reason：根据「问题 + 已执行步骤的观察」决定下一步动作。

两种实现产出同一种 Decision：

1. 大模型（OpenAI 兼容接口，JSON 输出）——配了 LLM_API_KEY 时优先使用；
2. 规则回退——没配 Key、超时、返回不合规时使用，保证零凭证也能跑通。

编排器只依赖 Decision，不关心是哪种实现，所以两条路径都能独立测试。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from . import llm

TOOL_DOCS = {
    "search_policy": "政策检索，返回事件卡与原文引用。参数 {query, top_k}",
    "map_event_to_etf": "事件 → 传导机制 → 影响对象 → 候选 ETF。参数 {event_id}",
    "analyze_overlap": "ETF 持仓穿透与两两重叠度。参数 {codes: 1~6 个代码}",
    "run_event_study": "事件研究，t0+5/20 相对基准超额。参数 {event_id, window}",
    "compose_report": "把已取到的证据写成报告。参数 {question, require_evidence}",
}

SYSTEM_PROMPT = """你是 ETF 政策研究 Agent 的编排器。你的职责是决定下一步调用哪个工具，不是自己回答。

可用工具：
%s

规则：
1. 每一步只调用一个工具，args 必须是合法 JSON 对象。
2. 必须参考「已执行步骤」里的观察结果：不要重复调用同一个工具，除非确实需要不同参数。
3. 证据足够时调用 compose_report 收尾；没有更多可做的就输出 action 为 final。
4. 只输出一个 JSON 对象，不要解释文字，不要加代码块标记。

输出格式：
{"thought": "一句话说明为什么走这一步", "action": "工具名或 final", "args": {}, "final": null}"""


@dataclass
class Decision:
    thought: str
    action: str
    args: dict = field(default_factory=dict)
    final: str | None = None
    source: str = "rules"          # llm / rules / fallback

    def to_dict(self) -> dict:
        return {
            "thought": self.thought,
            "action": self.action,
            "args": self.args,
            "final": self.final,
            "source": self.source,
        }


def _extract_json(text: str) -> dict:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("没有找到 JSON 对象")
    payload = json.loads(text[start:end + 1])
    if not isinstance(payload, dict):
        raise ValueError("顶层必须是 JSON 对象")
    return payload


def parse_decision(text: str) -> Decision:
    """把模型输出解析成 Decision；不合规直接抛 ValueError，由上层回退。"""
    payload = _extract_json(text)
    action = str(payload.get("action") or "").strip()
    if action != "final" and action not in TOOL_DOCS:
        raise ValueError("未知工具：%s" % (action or "(空)"))
    args = payload.get("args") or {}
    if not isinstance(args, dict):
        raise ValueError("args 必须是 JSON 对象")
    return Decision(
        thought=str(payload.get("thought") or "").strip(),
        action=action,
        args=args,
        final=payload.get("final"),
        source="llm",
    )


def _has(question: str, words: tuple[str, ...]) -> bool:
    return any(word in question for word in words)


def _first_event_id(history: list[dict]) -> str | None:
    for step in history:
        result = step.get("result") or {}
        for item in result.get("items") or []:
            if isinstance(item, dict) and item.get("event_id"):
                return item["event_id"]
    return None


def decide_rules(question: str, history: list[dict]) -> Decision:
    """规则版 Reason：按「已经拿到什么」推进，不重复调用同一个工具。"""
    done = [step.get("action") for step in history]
    event_id = _first_event_id(history) or "ev_demo_001"

    if "search_policy" not in done:
        return Decision("先拿政策原文，后面的结论才有证据可引", "search_policy",
                        {"query": question, "top_k": 3})
    if "map_event_to_etf" not in done:
        return Decision("政策已有，下一步做传导映射", "map_event_to_etf",
                        {"event_id": event_id})
    if _has(question, ("持仓", "重叠", "暴露", "穿透")) and "analyze_overlap" not in done:
        return Decision("用户问的是持仓，检查重叠与行业暴露", "analyze_overlap",
                        {"codes": ["512480", "159992"]})
    if _has(question, ("回测", "涨跌", "历史表现", "事件后")) and "run_event_study" not in done:
        return Decision("用户关心历史表现，做事件研究", "run_event_study",
                        {"event_id": event_id, "window": 20})
    if "compose_report" not in done:
        return Decision("证据够了，收尾写报告", "compose_report",
                        {"question": question, "require_evidence": True})
    return Decision("链路已走完，没有更多可调用的工具", "final", {})


def _history_text(history: list[dict]) -> str:
    if not history:
        return "（还没有执行任何工具）"
    lines = []
    for step in history:
        brief = json.dumps(step.get("result") or {}, ensure_ascii=False)
        if len(brief) > 600:
            brief = brief[:600] + "…"
        lines.append("%d. %s args=%s -> %s" % (
            step.get("step"), step.get("action"),
            json.dumps(step.get("args") or {}, ensure_ascii=False), brief))
    return "\n".join(lines)


def decide_llm(question: str, history: list[dict]) -> Decision:
    tools_text = "\n".join("- %s：%s" % (k, v) for k, v in TOOL_DOCS.items())
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT % tools_text},
        {"role": "user", "content": "任务：%s\n\n已执行步骤：\n%s\n\n请决定下一步。"
                                    % (question, _history_text(history))},
    ]
    return parse_decision(llm.chat(messages))


def decide(question: str, history: list[dict]) -> Decision:
    if llm.is_configured():
        try:
            return decide_llm(question, history)
        except Exception as exc:  # noqa: BLE001
            fallback = decide_rules(question, history)
            fallback.source = "fallback"
            fallback.thought = "大模型不可用（%s），回退规则：%s" % (
                type(exc).__name__, fallback.thought)
            return fallback
    return decide_rules(question, history)
