from __future__ import annotations

import os

import pytest

pytest.importorskip("playwright", reason="install Playwright for web tests")
from playwright.sync_api import Page, expect

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")


@pytest.mark.web
def test_pay_order(page: Page):
    page.goto(f"{BASE_URL}/login")
    page.get_by_label("用户名").fill("tester")
    page.get_by_label("密码").fill("test123")
    page.get_by_role("button", name="登录").click()
    expect(page.get_by_role("heading", name="我的订单")).to_be_visible()

    page.get_by_test_id("order-row").first.click()
    expect(page.get_by_role("heading", name="订单详情")).to_be_visible()
    page.get_by_test_id("pay-order").click()
    expect(page.get_by_test_id("order-status")).to_have_text("已支付")
