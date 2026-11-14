# search_policy —— 政策检索

## 功能
按关键词检索政策事件，返回带原文引用的事件卡。

## 参数
| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| query | string | 是 | 关键词，短词优先（如「农机补贴」「降准」「半导体设备」） |
| top_k | int | 否 | 返回条数，默认 5，范围 1~20 |
| deep_rerank | bool | 否 | 深度重排（会多一次模型调用），默认 false |

## 返回
```
{ "items": [ { "event_id", "title", "quote", "published_at", "relevance",
               "evidence_id" } ] }
```

## 口径
- 命中「最新」关键词时优先实时来源。
- 每条必须带原文引用（quote）与 evidence_id。
- 检索不到时如实返回空，不编造。

## 调用示例
```bash
python scripts/tools.py search_policy '{"query":"农机补贴","top_k":3}'
```
