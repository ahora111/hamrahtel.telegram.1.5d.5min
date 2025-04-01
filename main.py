#!/usr/bin/env python3
import os
import time
import requests
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from persiantools.jdatetime import JalaliDate

# تنظیمات تلگرام
BOT_TOKEN = "8187924543:AAH0jZJvZdpq_34um8R_yCyHQvkorxczXNQ"
CHAT_ID = "-1002683452872"

# تنظیمات لاگ‌گیری
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_driver():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        logging.error(f"خطا در ایجاد WebDriver: {e}")
        return None

def scroll_page(driver, scroll_pause_time=2):
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_product_data(driver, valid_brands):
    product_elements = driver.find_elements(By.CLASS_NAME, 'mantine-Text-root')
    brands, models = [], []
    
    for product in product_elements:
        name = product.text.strip().replace("تومانءء", "").replace("تومان", "").replace("نامشخص", "").strip()
        parts = name.split()
        brand = parts[0] if len(parts) >= 2 else name
        model = " ".join(parts[1:]) if len(parts) >= 2 else ""
        
        if brand in valid_brands:
            brands.append(brand)
            models.append(model)
        else:
            models.append(brand + " " + model)
            brands.append("")
    
    return brands[25:], models[25:]

def is_number(model_str):
    try:
        float(model_str.replace(",", ""))
        return True
    except ValueError:
        return False

def process_model(model_str):
    model_str = model_str.replace("٬", "").replace(",", "").strip()
    if is_number(model_str):
        model_value = float(model_str)
        model_value_with_increase = model_value * 1.015
        return f"{model_value_with_increase:,.0f}"
    return model_str

def escape_markdown(text):
    escape_chars = ['\\', '(', ')', '[', ']', '~', '*', '_', '-', '+', '>', '#', '.', '!', '|']
    for char in escape_chars:
        text = text.replace(char, '\\' + char)
    return text

def split_message(message, max_length=4000):
    return [message[i:i+max_length] for i in range(0, len(message), max_length)]

def decorate_line(line):
    if not line or not isinstance(line, str):  
        return ""  # مقدار پیش‌فرض در صورت نامعتبر بودن مقدار line

    if "huawei" in line.lower():
        return f"🟥 {line}"
    elif any(keyword in line.lower() for keyword in ["poco", "redmi"]):
        return f"🟨 {line}"
    elif "lcd" in line.lower():
        return f"🟦 {line}"
    return line


def categorize_messages(lines):
    categories = {"🟥": [], "🟨": [], "🟦": []}
    
    for line in lines:
        if line.startswith("🟥"):
            categories["🟥"].append(line)
        elif line.startswith("🟨"):
            categories["🟨"].append(line)
        elif line.startswith("🟦"):
            categories["🟦"].append(line)
    
    return categories

def get_header_footer(category, update_date):
    headers = {
        "🟥": f"📅 بروزرسانی قیمت در تاریخ {update_date} می باشد\n✅ لیست پخش موبایل اهورا\n⬅️ قطعات هوآوی  ➡️\n",
        "🟨": f"📅 بروزرسانی قیمت در تاریخ {update_date} می باشد\n✅ لیست پخش موبایل اهورا\n⬅️ قطعات شیایومی  ➡️\n",
        "🟦": f"📅 بروزرسانی قیمت در تاریخ {update_date} می باشد\n✅ لیست پخش موبایل اهورا\n⬅️ قطعات سامسونگ  ➡️\n",
    }
    footer = "\n\n☎️ شماره های تماس :\n📞 09371111558\n📞 02833991417"
    return headers[category], footer

def send_telegram_message(message, bot_token, chat_id, reply_markup=None):
    message_parts = split_message(message)
    last_message_id = None
    for part in message_parts:
        part = escape_markdown(part)
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        params = {
            "chat_id": chat_id,
            "text": part,
            "parse_mode": "MarkdownV2"
        }
        if reply_markup:
            params["reply_markup"] = json.dumps(reply_markup)

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=params, headers=headers)  
        response_data = response.json()
        
        if response_data.get('ok'):
            last_message_id = response_data["result"]["message_id"]
        else:
            logging.error(f"❌ خطا در ارسال پیام: {response_data}")
            return None

    logging.info("✅ پیام ارسال شد!")
    return last_message_id

def main():
    try:
        driver = get_driver()
        if not driver:
            logging.error("❌ نمی‌توان WebDriver را ایجاد کرد.")
            return
        
        driver.get('https://hamrahtel.com/quick-checkout?category=mobile-parts')
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'mantine-Text-root')))
        logging.info("✅ داده‌ها آماده‌ی استخراج هستند!")
        scroll_page(driver)

        valid_brands = ["Galaxy", "POCO", "Redmi", "iPhone", "NOKIA", "Honor", "huawei"]
        brands, models = extract_product_data(driver, valid_brands)
        driver.quit()

        processed_data = [f"{process_model(models[i])} {brands[i]}" for i in range(len(brands))]
        update_date = JalaliDate.today().strftime("%Y-%m-%d")
        message_lines = [decorate_line(row) for row in processed_data]

        categories = categorize_messages(message_lines)
        message_ids = {}

        for category, lines in categories.items():
            if lines:
                header, footer = get_header_footer(category, update_date)
                message = header + "\n" + "\n".join(lines) + footer
                message_ids[category] = send_telegram_message(message, BOT_TOKEN, CHAT_ID)

        final_message = "✅ لیست بروز است. جهت ثبت سفارش اطلاعات واریز ارسال شود."
        button_markup = {"inline_keyboard": [
            [{"text": "📱 لیست قطعات هوآوی", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{message_ids.get('🟥', '')}"}],
            [{"text": "📱 لیست قطعات شیایومی", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{message_ids.get('🟨', '')}"}],
            [{"text": "📱 لیست قطعات سامسونگ", "url": f"https://t.me/c/{CHAT_ID.replace('-100', '')}/{message_ids.get('🟦', '')}"}]
        ]}
        
        send_telegram_message(final_message, BOT_TOKEN, CHAT_ID, reply_markup=button_markup)

    except Exception as e:
        logging.error(f"❌ خطا: {e}")

if __name__ == "__main__":
    main()
