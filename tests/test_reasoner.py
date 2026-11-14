"""编排与推理：规则推进、模型输出解析、失败回退。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import orchestrator, reasoner, tools  # noqa: E402
from src.reasoner import Decision  # noqa: E402


def test_tool_docs_match_registry():
    assert set(reasoner.TOOL_DOCS) == set(tools.available())


def test_rules_progress_without_repeats():
    steps = orchestrator.run_steps("农机补贴对持仓的影响")
    actions = [step["action"] for step in steps]
    assert actions == ["search_policy", "map_event_to_etf", "analyze_overlap", "compose_report"]
    assert len(set(actions)) == len(actions), "同一个工具不该被重复调用"


def test_event_id_flows_from_search_to_mapping():
    steps = orchestrator.run_steps("农机补贴对持仓的影响")
    event_id = steps[0]["result"]["items"][0]["event_id"]
    assert steps[1]["args"]["event_id"] == event_id


def test_injected_decide_drives_the_loop():
    def fake(question, history):
        if not history:
            return Decision("先查政策", "search_policy", {"query": question}, source="llm")
        return Decision("够了", "final", {}, source="llm")

    steps = orchestrator.run_steps("任何问题", decide=fake)
    assert [step["action"] for step in steps] == ["search_policy"]


def test_repeated_identical_call_is_cut_off():
    def stuck(question, history):
        return Decision("再来一次", "search_policy", {"query": "x"}, source="llm")

    steps = orchestrator.run_steps("x", max_steps=6, decide=stuck)
    assert len(steps) == 1, "同工具同参数应被熔断"


def test_parse_decision_handles_fenced_json():
    text = '```json\n{"thought": "先查", "action": "search_policy", "args": {"query": "农机补贴"}}\n```'
    decision = reasoner.parse_decision(text)
    assert decision.action == "search_policy"
    assert decision.args == {"query": "农机补贴"}
    assert decision.source == "llm"


def test_parse_decision_rejects_unknown_tool():
    with pytest.raises(ValueError):
        reasoner.parse_decision('{"action": "delete_everything", "args": {}}')


def test_parse_decision_rejects_non_object_args():
    with pytest.raises(ValueError):
        reasoner.parse_decision('{"action": "search_policy", "args": "query=x"}')


def test_llm_failure_falls_back_to_rules(monkeypatch):
    monkeypatch.setattr(reasoner.llm, "is_configured", lambda: True)

    def boom(_messages):
        raise RuntimeError("network down")

    monkeypatch.setattr(reasoner.llm, "chat", boom)

    decision = reasoner.decide("农机补贴", [])
    assert decision.action == "search_policy"
    assert decision.source == "fallback"
    assert "回退规则" in decision.thought


def test_llm_path_used_when_available(monkeypatch):
    monkeypatch.setattr(reasoner.llm, "is_configured", lambda: True)
    monkeypatch.setattr(
        reasoner.llm, "chat",
        lambda messages: '{"thought": "模型决定", "action": "search_policy", "args": {"query": "x"}}',
    )
    decision = reasoner.decide("农机补贴", [])
    assert decision.source == "llm"
    assert decision.thought == "模型决定"


def test_final_answer_passes_guardrail():
    out = orchestrator.run("农机补贴对持仓的影响")
    assert out.startswith("结论：")
    assert "证据" in out
    assert "依次取证" in out
