# compose_report —— 证据优先报告

## 功能
生成证据优先的研究报告（异步）。

## 参数
| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| question | string | 是 | 研究问题 |
| require_evidence | bool | 否 | 是否要求每条结论带证据，默认 true |

## 返回
```
{ "task_id", "status" }   // status: queued → running → done
```

## 口径
- 先检索事实、再生成论证、最后过闸门与独立审稿。
- 不过闸门降级为证据包，不强行成文。
- 报告每条断言带引用。

## 调用示例
```bash
python scripts/tools.py compose_report '{"question":"农机补贴对持仓的影响","require_evidence":true}'
```
