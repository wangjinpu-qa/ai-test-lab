"""AI workflows for interface-test generation and failure diagnosis."""

from __future__ import annotations

from typing import Any, Dict

from .client import AiClient

ORDER_RULES = [
    "支付成功后订单状态必须为 PAID",
    "重复支付必须返回 ORDER_ALREADY_PAID",
    "未登录用户不能支付",
    "支付金额必须等于订单应付金额",
]


class ApiAssistant:
    def __init__(self, client: AiClient | None = None):
        self.client = client or AiClient()

    def generate_tests(self, openapi: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.chat_json(
            "generate_api_tests",
            {"openapi": openapi, "business_rules": ORDER_RULES},
        ).as_dict()

    def diagnose_failure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.chat_json("diagnose_failure", context).as_dict()
