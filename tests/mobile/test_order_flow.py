"""Appium smoke-test template.

Run only when an Android emulator/device and Appium server are available:

    pytest -m mobile --appium-server http://127.0.0.1:4723

The test is intentionally skipped by default so API/Web learning works on a
machine without Android SDK. The concrete Screen Object shows the stable
locator policy used by the project.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("appium", reason="install Appium-Python-Client for mobile tests")


@pytest.mark.mobile
@pytest.mark.skipif(
    os.getenv("RUN_MOBILE_TESTS") != "1",
    reason="set RUN_MOBILE_TESTS=1 after starting an Android emulator and Appium",
)
def test_pay_order_on_android():
    from appium import webdriver
    from appium.options.android import UiAutomator2Options
    from appium.webdriver.common.appiumby import AppiumBy

    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.device_name = os.getenv("ANDROID_DEVICE", "Pixel_6_API_35")
    options.app_package = "com.example.aitestlab"
    options.app_activity = ".MainActivity"
    options.no_reset = True

    driver = webdriver.Remote(os.getenv("APPIUM_SERVER", "http://127.0.0.1:4723"), options=options)
    try:
        driver.find_element(AppiumBy.ACCESSIBILITY_ID, "username").send_keys("tester")
        driver.find_element(AppiumBy.ACCESSIBILITY_ID, "password").send_keys("test123")
        driver.find_element(AppiumBy.ACCESSIBILITY_ID, "login_button").click()
        driver.find_element(AppiumBy.ACCESSIBILITY_ID, "order_row_ORD-1001").click()
        driver.find_element(AppiumBy.ACCESSIBILITY_ID, "pay_order").click()
        assert driver.find_element(AppiumBy.ACCESSIBILITY_ID, "order_status").text == "已支付"
    finally:
        driver.quit()
