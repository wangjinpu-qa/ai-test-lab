# AI Test Lab：AI 辅助自动化测试实践

这是一个持续完善的个人实践项目，围绕订单登录、查询和支付业务，学习 Python 接口自动化、Playwright Web 自动化，以及 AI 在测试草稿生成、失败分析和定位器维护中的应用。

## 当前实现与验证范围

| 模块 | 当前状态 |
| --- | --- |
| 本地订单应用 | FastAPI + SQLite + Web 页面，提供登录、订单查询、详情、支付和数据重置接口 |
| 接口自动化 | pytest + FastAPI TestClient，覆盖登录、支付、重复支付、金额异常、未登录访问和用户数据隔离等场景 |
| Web 自动化 | Python Playwright 完成登录、打开订单详情、支付和页面状态检查 |
| AI 测试生成与失败分析 | 已实现统一模型调用、生成与诊断脚本、JSON 解析和结果保存，已验证 Mock 流程 |
| 真实模型效果 | 已实现兼容 API 的调用封装，实际模型效果待验证 |
| AI Web 定位辅助 | 已有建议入口和 Mock 示例，自动采集、候选验证及回归流程待完成 |
| Android / Appium | Kotlin 客户端骨架和 Appium 测试模板，构建与设备运行待验证 |
| Playwright MCP / Appium MCP | 提供配置示例，客户端连接与操作流程待验证 |

Mock 返回预先准备的示例，用于学习工程流程，不代表真实模型已成功识别页面或生成可直接执行的测试。当前生成草稿仍需审核登录鉴权、测试数据和业务断言。

2026-11-11 本地验证：**13 passed，1 skipped**；Android 用例因环境未配置跳过。Ruff 检查通过。验证使用临时数据库和单独启动的服务。

Web 后续主流程见 [WEB_AI_TODO.md](WEB_AI_TODO.md)。Android 环境和构建方式见 [app/mobile/README.md](app/mobile/README.md)。

## 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m playwright install chromium
```

启动服务：

```bash
uvicorn app.main:app --reload
```

浏览器访问 <http://127.0.0.1:8000>，登录账号是 `tester` / `test123`。

## 2. 运行确定性自动化

另开终端并激活虚拟环境：

```bash
pytest -m api
pytest -m ai
```

接口测试通过 TestClient 在进程内执行，不依赖 Uvicorn。默认会重置本地演示数据库；如需保留浏览器中的数据，可为该次运行指定独立数据库：

```bash
DB_PATH=/tmp/ai-test-lab-api.db pytest -m api
```

Web 测试访问真实运行的 FastAPI 服务；先启动服务，再在每次 Web 测试前重置订单，保证订单待支付：

```bash
python scripts/reset_demo_data.py
pytest -m web
```

当前 Web 用例尚未自动准备数据。重置会清空演示订单状态和服务中的登录 Token。保留失败截图、Trace 或生成 Allure 原始结果可使用：

```bash
python scripts/reset_demo_data.py
pytest -m web --tracing=retain-on-failure --alluredir=allure-results
```

截图可按需增加 `--screenshot=only-on-failure`。查看 Allure 网页报告需要另外安装 Allure CLI。

## 3. 验证接口 AI 用例生成

默认使用 `AI_MODE=mock`，不需要 API Key：

```bash
python scripts/generate_api_tests.py \
  --spec http://127.0.0.1:8000/openapi.json \
  --output artifacts/generated_api_tests.py
python -m py_compile artifacts/generated_api_tests.py
```

脚本保存 `.py` 草稿和 `.json` 结果，不自动执行测试或修改正式测试目录。`py_compile` 是手动语法检查，不会运行接口请求。当前 Mock 支付示例未携带登录 Token，需人工补齐鉴权，并在测试环境执行确认后再纳入正式测试集。

使用 OpenAI 兼容接口时：

```bash
export AI_MODE=api
export OPENAI_BASE_URL=https://your-compatible-endpoint/v1
export OPENAI_API_KEY=your-key
export OPENAI_MODEL=your-model
```

## 4. 验证接口失败诊断

创建一个模拟失败上下文：

```bash
cat > artifacts/payment-failure.json <<'JSON'
{
  "request": {"method": "POST", "path": "/api/orders/ORD-1001/pay"},
  "response": {"status_code": 200, "code": "0000", "data": {"status": "CREATED"}},
  "assertion": "expected status PAID, actual CREATED",
  "logs": ["payment accepted", "order status update missing"]
}
JSON
python scripts/diagnose_failure.py --input artifacts/payment-failure.json
```

也可以对当前进程内的接口测试注入真实故障，观察支付状态断言失败：

```bash
DEMO_FAULT=payment_status DB_PATH=/tmp/ai-test-lab-fault.db \
  pytest tests/api/test_orders.py::test_pay_order_success -q
```

该命令预期失败：支付返回成功，但状态保留为 `CREATED`。当前需要手动整理失败上下文并交给诊断脚本，pytest 失败后自动采集与诊断尚未接入。对 Web 演示同类故障时，可使用 `DEMO_FAULT=payment_status uvicorn app.main:app --reload` 启动服务。

## 5. 验证 Playwright AI 方式

`ai/web_assistant.py` 提供 `suggest_locator(dom, failed_locator, page_url)`，复用统一的模型调用。当前 Web 用例没有调用这个助手，Mock 返回固定候选，API 模式的专用任务提示与实际页面验证待补齐。

下一步以支付按钮的 `data-testid` 变化为例，完成“失败采集 → AI 建议 → Playwright 实际验证 → 人工更新定位器 → 回归”，详见 [主流程待办](WEB_AI_TODO.md)。

安装 Node.js 后，可在支持 MCP 的 AI 客户端中加载 [mcp.playwright.json](mcp.playwright.json)，验证自然语言操作浏览器。该配置示例尚未完成运行验证，pytest 不会自动加载它。

## 6. 验证 Appium AI 方式

先按 [app/mobile/README.md](app/mobile/README.md) 安装 Android Studio、SDK、模拟器和 Appium。App 使用 `10.0.2.2` 访问宿主机服务。

Appium MCP 配置示例见 [mcp.appium.json](mcp.appium.json)。目前移动端仍是待补齐的骨架，不应将其视为已验证的完整业务流程。

`ai/mobile_assistant.py` 目前把页面层级和截图路径作为文字传入；尚未上传图片内容，因此没有实现真实视觉识别。后续先通过稳定 `accessibility id` 跑通支付，再接入 AI 辅助识别和状态验证。

## AI 边界

- 固定状态码、错误码、金额、字段类型和权限结果由代码断言。
- AI 只生成草稿、提出定位器候选、辅助失败分类和解释证据。
- 外层 `OK` / `ERROR` 表示模型调用状态；部分任务结果中的 `verdict` 表示分析建议，不能替代 pytest 或 Playwright 的断言结果。
- 当前主要完成 JSON 解析，完整字段和证据校验待补充。使用者仍需审核生成结果。
- 生成的代码不自动执行、不自动提交；先做语法检查、测试运行和人工审核。
- AI 服务不可用时，确定性接口和 Web 测试仍可执行。

## 面试演示建议

当前可演示：

1. 运行接口自动化并说明登录 Token、数据准备和业务断言。
2. 在 Mock 模式下，从 OpenAPI 获取输入并保存接口测试草稿，执行手动语法检查。
3. 注入支付状态故障观察确定性测试失败，再使用保存的上下文演示 Mock 诊断流程。
4. 重置数据，运行 Playwright 登录和支付主链路。

真实模型结果、Web 候选定位验证和 Android 自动化完成后，再补充相应演示材料。项目重点是学习 AI 辅助测试资产生产和维护，最终结果由实际执行与业务断言验证。
