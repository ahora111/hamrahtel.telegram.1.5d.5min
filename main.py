import requests
import json

BOT_TOKEN = "8187924543:AAH0jZJvZdpq_34um8R_yCyHQvkorxczXNQ"
CHAT_ID = "-1002284274669"

def send_test_button():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {
        "chat_id": CHAT_ID,
        "text": "🔹 لطفاً یک گزینه را انتخاب کنید:",
        "reply_markup": json.dumps({
            "inline_keyboard": [[{"text": "📱 لیست سامسونگ", "callback_data": "list_samsung"}]]
        })
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(params), headers=headers)
    print(response.json())  # برای بررسی نتیجه

send_test_button()
