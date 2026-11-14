"""五个研究工具。当前为 mock 实现（无真实数据源），替换 data_sources 后即可接入真实数据。

每个工具的返回都必须带 evidence_id：这是证据链约束的硬要求，
缺 evidence_id 的结果会被 guardrails 拒绝进入结论。
"""
from __future__ import annotations

import json
import sys

_MOCK = "mock"


def search_policy(args: dict) -> dict:
    query = args.get("query", "")
    top_k = int(args.get("top_k", 5))
    if not query:
        return {"error": "query 必填"}
    # mock：返回占位事件卡，evidence_id 指向 mock 数据源
    return {
        "items": [
            {
                "event_id": f"ev_{query}_001",
                "title": f"关于「{query}」的示例事件（mock）",
                "quote": "（mock 原文引用）",
                "published_at": "2026-11-14",
                "relevance": 0.9,
                "evidence_id": f"mock-{query}-001",
            }
        ][:top_k],
        "source": _MOCK,
    }


def map_event_to_etf(args: dict) -> dict:
    event_id = args.get("event_id", "")
    if not event_id:
        return {"error": "event_id 必填"}
    return {
        "mechanism": "直接作用（mock，未接入真实闭集）",
        "variables": [],
        "affected_objects": [],
        "proxies": [],
        "confidence": None,
        "evidence_id": f"mock-{event_id}",
        "source": _MOCK,
    }


def analyze_overlap(args: dict) -> dict:
    codes = args.get("codes", [])
    if not codes or not isinstance(codes, list):
        return {"error": "codes 必填（1~6 个代码的数组）"}
    return {
        "industry_exposure": [],
        "pair_overlap": [],
        "penetration_rate": None,
        "evidence_id": f"mock-overlap-{'-'.join(codes)}",
        "source": _MOCK,
    }


def run_event_study(args: dict) -> dict:
    event_id = args.get("event_id", "")
    if not event_id:
        return {"error": "event_id 必填"}
    return {
        "t0": "2026-11-14",
        "sample_size": 0,
        "excess_5d": None,
        "excess_20d": None,
        "caveats": ["样本不足：mock 数据源无同类事件，不下结论"],
        "evidence_id": f"mock-{event_id}",
        "source": _MOCK,
    }


def compose_report(args: dict) -> dict:
    question = args.get("question", "")
    if not question:
        return {"error": "question 必填"}
    return {
        "task_id": f"task-mock-{abs(hash(question)) % 100000}",
        "status": "queued",
        "source": _MOCK,
    }


_REGISTRY = {
    "search_policy": search_policy,
    "map_event_to_etf": map_event_to_etf,
    "analyze_overlap": analyze_overlap,
    "run_event_study": run_event_study,
    "compose_report": compose_report,
}


def invoke(tool_id: str, args_json: str) -> dict:
    if tool_id not in _REGISTRY:
        return {"error": f"未知工具 {tool_id}，可用: {sorted(_REGISTRY)}"}
    try:
        args = json.loads(args_json)
    except json.JSONDecodeError as e:
        return {"error": f"参数不是合法 JSON: {e}"}
    return _REGISTRY[tool_id](args)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(json.dumps({"error": "用法: tools.py <tool_id> '<json参数>'"}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(invoke(sys.argv[1], sys.argv[2]), ensure_ascii=False, indent=2))
