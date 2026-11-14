---
name: etf-research-agent
description: 面向 ETF 政策研究的垂直 AI Agent。把「多数据源 + 五个研究工具 + 证据链约束 + 输出护栏」组织成一套可被 LLM 编排调用的工具集：search_policy（政策检索）、map_event_to_etf（事件到影响对象映射）、analyze_overlap（持仓穿透与重叠度）、run_event_study（事件研究）、compose_report（证据优先报告）。当用户要查政策催化、持仓暴露、ETF 重叠度、事件回测或生成研究报告时使用。凭证红线：任何取数前若数据源凭证未配置或鉴权失败，必须提示用户配置 config，不得猜测或硬编码凭证。
---

# ETF 研究 Agent

把「找政策 → 映射到 ETF → 看持仓 → 回测 → 出报告」这条研究闭环拆成五个工具，
由编排器（ReAct）按问题选择调用，每个工具的结果都带 `evidence_id`，最终回答过护栏校验。

## 五个工具

| tool_id | 作用 |
| --- | --- |
| search_policy | 按关键词检索政策事件，返回带原文引用的事件卡 |
| map_event_to_etf | 事件 → 传导机制 → 影响对象 → 真实 ETF |
| analyze_overlap | 多标的组合暴露与两两重叠度 |
| run_event_study | 事件发生后相对基准的超额（t0+5/20） |
| compose_report | 生成证据优先的研究报告（异步） |

## 执行顺序（强制）

1. 理解意图 —— 判断用户要的是哪类事实/结论。
2. 读 `catalog.md` 选工具 —— 语义匹配，多命中按「区别」消歧。
3. 读命中的 `tools/<tool_id>.md` —— 没读文档不得构造调用。
4. 校验参数 —— 缺信息就问，不猜。
5. 调用 `scripts/tools.py <tool_id> '<json参数>'`。
6. 组织结论并过护栏 —— 用 `scripts/guardrails.py` 校验后输出。

## 硬约束

- 每个工具的返回必须带 `evidence_id`，无证据不得进入结论。
- 样本不足（如事件研究少于 3 条同类样本）时如实报告「样本不足」，不得据此下结论。
- 抽不出传导链时记「直接作用」，不得补造机制。
- 凭证未配置时提示用户配置，不猜测、不硬编码。
