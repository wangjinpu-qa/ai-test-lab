package com.example.aitestlab

import android.app.Activity
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

class MainActivity : Activity() {
    private val baseUrl = "http://10.0.2.2:8000"
    private var token: String = ""
    private var orderStatus: TextView? = null
    private var orderId = "ORD-1001"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        showLogin()
    }

    private fun root(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        setPadding(40, 48, 40, 40)
        gravity = Gravity.TOP
    }

    private fun title(text: String): TextView = TextView(this).apply {
        this.text = text
        textSize = 24f
        setPadding(0, 0, 0, 24)
    }

    private fun showLogin() {
        val root = root()
        root.addView(title("订单管理实验室"))
        val username = EditText(this).apply { id = R.id.username; hint = "用户名"; contentDescription = "username"; setText("tester") }
        val password = EditText(this).apply { id = R.id.password; hint = "密码"; contentDescription = "password"; setText("test123") }
        val login = Button(this).apply { id = R.id.login_button; text = "登录"; contentDescription = "login_button" }
        root.addView(username); root.addView(password); root.addView(login)
        login.setOnClickListener { login(username.text.toString(), password.text.toString()) }
        setContentView(root)
    }

    private fun login(username: String, password: String) {
        request("POST", "/api/auth/login", JSONObject().put("username", username).put("password", password), "") { code, body ->
            if (code == 200) { token = JSONObject(body).getJSONObject("data").getString("token"); runOnUiThread { showOrders() } }
            else runOnUiThread { Toast.makeText(this, "登录失败", Toast.LENGTH_SHORT).show() }
        }
    }

    private fun showOrders() {
        val root = root()
        root.addView(title("我的订单"))
        val row = Button(this).apply { id = R.id.order_row_ORD_1001; text = "ORD-1001  Keyboard  ¥98.00  待支付"; contentDescription = "order_row_ORD-1001" }
        root.addView(row)
        row.setOnClickListener { showDetail() }
        setContentView(root)
    }

    private fun showDetail() {
        val root = root()
        root.addView(title("订单详情"))
        root.addView(TextView(this).apply { text = "订单号：$orderId" })
        root.addView(TextView(this).apply { text = "商品：Keyboard" })
        orderStatus = TextView(this).apply { id = R.id.order_status; text = "状态：待支付"; contentDescription = "order_status" }
        root.addView(orderStatus)
        val pay = Button(this).apply { id = R.id.pay_order; text = "支付"; contentDescription = "pay_order" }
        root.addView(pay)
        pay.setOnClickListener { pay(pay) }
        setContentView(root)
    }

    private fun pay(button: Button) {
        button.isEnabled = false
        request("POST", "/api/orders/$orderId/pay", JSONObject().put("amount", 98.0), token) { code, body ->
            runOnUiThread {
                if (code == 200) { orderStatus?.text = "状态：已支付"; Toast.makeText(this, "支付成功", Toast.LENGTH_SHORT).show() }
                else { button.isEnabled = true; Toast.makeText(this, "支付失败", Toast.LENGTH_SHORT).show() }
            }
        }
    }

    private fun request(method: String, path: String, payload: JSONObject, auth: String, callback: (Int, String) -> Unit) {
        thread {
            try {
                val connection = URL(baseUrl + path).openConnection() as HttpURLConnection
                connection.requestMethod = method
                connection.setRequestProperty("Content-Type", "application/json")
                if (auth.isNotBlank()) connection.setRequestProperty("Authorization", "Bearer $auth")
                connection.doOutput = true
                connection.outputStream.use { it.write(payload.toString().toByteArray()) }
                val body = (if (connection.responseCode < 400) connection.inputStream else connection.errorStream).bufferedReader().readText()
                callback(connection.responseCode, body)
                connection.disconnect()
            } catch (error: Exception) { callback(599, error.message ?: "network error") }
        }
    }
}
