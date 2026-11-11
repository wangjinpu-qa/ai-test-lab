from __future__ import annotations

import pytest

from ai.api_assistant import ApiAssistant
from ai.client import AiClient
from ai.mobile_assistant import MobileAssistant
from ai.web_assistant import WebAssistant


@pytest.mark.ai
def test_mock_api_test_generation_is_structured():
    result = ApiAssistant(AiClient(mode="mock")).generate_tests({"openapi": "3.0.0"})
    assert result["status"] == "OK"
    assert result["result"]["scenarios"]
    assert "def test_pay_order_success" in result["result"]["code"]


@pytest.mark.ai
def test_mock_failure_diagnosis_uses_supplied_evidence():
    result = ApiAssistant(AiClient(mode="mock")).diagnose_failure(
        {"response": {"code": "0000", "data": {"status": "CREATED"}}}
    )
    assert result["result"]["verdict"] == "FAIL"
    assert "CREATED" in " ".join(result["result"]["evidence"])


@pytest.mark.ai
def test_web_and_mobile_assistants_return_candidates():
    web = WebAssistant(AiClient(mode="mock")).suggest_locator("<button>确认支付</button>", "#pay")
    mobile = MobileAssistant(AiClient(mode="mock")).find_element("页面底部支付按钮", "pay_order")
    assert web["result"]["verdict"] == "PASS"
    assert mobile["result"]["selector"] == "pay_order"
