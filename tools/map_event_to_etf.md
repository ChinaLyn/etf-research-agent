# map_event_to_etf —— 事件到影响对象映射

## 功能
把一条政策事件映射为传导机制、影响对象与真实 ETF。

## 参数
| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| event_id | string | 是 | 事件标识 |

## 返回
```
{ "mechanism", "variables": [...], "affected_objects": [...],
  "proxies": ["512480","159992"], "confidence", "evidence_id" }
```

## 口径
- 影响对象必须落在已知清单内或原文出现过。
- 抽不出链条时记「直接作用」，不补造机制。
- proxies 只给真实 ETF 代码，不产虚构代码。

## 调用示例
```bash
python scripts/tools.py map_event_to_etf '{"event_id":"ev_20261114_001"}'
```
