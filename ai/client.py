"""Small OpenAI-compatible client with a deterministic Mock mode.

The mock mode is intentionally useful: all automation can be learned and
tested without spending model credits. Set AI_MODE=api to use a compatible
``/chat/completions`` endpoint.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AiResponse:
    status: str
    result: Dict[str, Any]
    model: str
    prompt_version: str
    raw: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "result": self.result,
            "model": self.model,
            "prompt_version": self.prompt_version,
        }


def _extract_json(text: str) -> Dict[str, Any]:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise ValueError("AI response did not contain a JSON object")
        return json.loads(match.group(0))


class AiClient:
    def __init__(self, mode: str | None = None):
        self.mode = mode or os.getenv("AI_MODE", "mock")
        self.base_url = os.getenv("OPENAI_BASE_URL", "").rstrip("/")
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "local-mock")
        self.prompt_version = "v1"

    def chat_json(self, task: str, context: Dict[str, Any]) -> AiResponse:
        if self.mode == "mock":
            return AiResponse("OK", self._mock(task, context), self.model, self.prompt_version)
        if not self.base_url or not self.api_key or not self.model:
            return AiResponse(
                "ERROR",
                {"error": "OPENAI_BASE_URL, OPENAI_API_KEY and OPENAI_MODEL are required in API mode"},
                self.model,
                self.prompt_version,
            )
        prompt = (
            "You are an assistant for a local software testing lab. Return only valid JSON. "
            "Never invent evidence or fields. If the supplied context is insufficient, use "
            "INCONCLUSIVE. Task: "
            + task
            + "\nContext:\n"
            + json.dumps(context, ensure_ascii=False, indent=2)
        )
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "Return structured JSON only."},
                {"role": "user", "content": prompt},
            ],
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
            content = body["choices"][0]["message"]["content"]
            return AiResponse("OK", _extract_json(content), self.model, self.prompt_version, content)
        except (urllib.error.URLError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            return AiResponse("ERROR", {"error": str(exc)}, self.model, self.prompt_version)

    @staticmethod
    def _mock(task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if task == "generate_api_tests":
            return {
                "status": "OK",
                "scenarios": [
                    "支付成功后订单状态为 PAID",
                    "重复支付返回 ORDER_ALREADY_PAID",
                    "未登录用户不能支付",
                    "支付金额不等于订单金额时返回 AMOUNT_MISMATCH",
                ],
                "source_refs": ["OpenAPI document", "ORDER_RULES"],
                "code": (
                    "def test_pay_order_success(client):\n"
                    "    response = client.post('/api/orders/ORD-1001/pay', json={'amount': 98.0})\n"
                    "    assert response.status_code == 200\n"
                    "    assert response.json()['code'] == '0000'\n"
                    "    assert response.json()['data']['status'] == 'PAID'\n"
                ),
            }
        if task == "diagnose_failure":
            text = json.dumps(context, ensure_ascii=False)
            if "CREATED" in text and "0000" in text:
                return {
                    "category": "business_assertion",
                    "summary": "支付接口返回成功，但订单状态未更新",
                    "evidence": ["支付接口 code=0000", "订单查询 status=CREATED"],
                    "suggested_actions": [
                        "检查支付成功后的订单状态更新逻辑",
                        "确认支付接口和查询接口使用同一个 order_id",
                    ],
                    "verdict": "FAIL",
                }
            return {
                "category": "unknown",
                "summary": "上下文不足，无法可靠定位失败原因",
                "evidence": [],
                "suggested_actions": ["补充请求、响应和服务端日志"],
                "verdict": "INCONCLUSIVE",
            }
        if task == "suggest_locator":
            return {
                "locator": "get_by_role('button', name='确认支付')",
                "reason": "按钮文本发生变化，当前页面仍存在唯一支付操作",
                "scope": "订单详情区域",
                "evidence": ["button text=确认支付"],
                "verdict": "PASS",
            }
        if task == "find_mobile_element":
            return {
                "strategy": "accessibility id",
                "selector": "pay_order",
                "reason": "当前页面存在带有 pay_order content description 的支付按钮",
                "evidence": ["page_source contains content-desc=pay_order"],
                "verdict": "PASS",
            }
        return {"verdict": "INCONCLUSIVE", "evidence": [], "reason": "unsupported mock task"}
