# Android Appium 练习

这个目录包含一个不依赖 AndroidX 的最小 Kotlin Android 客户端。它只实现订单实验室的登录、订单列表、详情和支付流程，便于在本地验证 Appium 与 AI 辅助定位。

## 构建和安装

在安装 Android Studio、SDK 35 和 Java 17 后：

```bash
cd app/mobile/android
# Either open this directory in Android Studio and run the app,
# or use a locally installed Gradle:
gradle assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

模拟器访问宿主机 FastAPI 服务使用 `10.0.2.2:8000`。启动服务：

```bash
uvicorn app.main:app --reload
```

## 启动 Appium

```bash
appium driver install uiautomator2
appium --base-path /
```

然后设置：

```bash
export RUN_MOBILE_TESTS=1
export APPIUM_SERVER=http://127.0.0.1:4723
pytest -m mobile
```

测试优先使用 `accessibility id`：`username`、`password`、`login_button`、`order_row_ORD-1001`、`pay_order`、`order_status`。

## AI 辅助定位

先使用稳定定位器。只有在控件没有稳定标识或需要视觉特征识别时，才使用 Appium MCP 的 `appium_ai` 工具，例如“找到页面底部蓝色的支付按钮”。AI 返回的元素必须通过真实点击和订单状态变化验证，不能直接替代正式 Screen Object。
