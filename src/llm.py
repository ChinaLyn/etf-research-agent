r"""最小 OpenAI 兼容客户端：只用标准库，不引第三方依赖。

只在真正要做推理时才联网。没配 LLM_API_KEY 时 is_configured() 为 False，
上层据此回退到规则，保证零凭证也能跑通整条链路。
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"


class LLMError(RuntimeError):
    """调用大模型失败：没配 Key、网络错误、返回格式不对。"""


def base_url() -> str:
    return (os.environ.get("LLM_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def api_key() -> str:
    return (os.environ.get("LLM_API_KEY") or "").strip()


def model() -> str:
    return (os.environ.get("LLM_MODEL") or DEFAULT_MODEL).strip()


def timeout() -> float:
    try:
        return float(os.environ.get("LLM_TIMEOUT", "30"))
    except ValueError:
        return 30.0


def is_configured() -> bool:
    return bool(api_key())


def chat(messages: list[dict], temperature: float = 0.0) -> str:
    if not is_configured():
        raise LLMError("没有配置 LLM_API_KEY")

    payload = json.dumps(
        {
            "model": model(),
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        },
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        base_url() + "/chat/completions",
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + api_key(),
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout()) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        raise LLMError("HTTP %s: %s" % (exc.code, detail)) from exc
    except Exception as exc:  # noqa: BLE001
        raise LLMError("%s: %s" % (type(exc).__name__, exc)) from exc

    try:
        return json.loads(body)["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as exc:
        raise LLMError("返回格式不是预期的 chat/completions") from exc
