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
CHAT_ID = "-1002284274669"

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

def process_model(model_str):
    model_str = model_str.replace("٬", "").replace(",", "").strip()
    try:
        model_value = float(model_str)
        model_value_with_increase = model_value * 1.015
        return f"{model_value_with_increase:,.0f}"
    except ValueError:
        return model_str

def decorate_line(line):
    if line.startswith(('🔵', '🟡', '🍏', '🟣')):
        return line
    if "Galaxy" in line:
        return f"🔵 {line}"
    elif "POCO" in line or "Redmi" in line:
        return f"🟡 {line}"
    elif "iPhone" in line:
        return f"🍏 {line}"
    else:
        return f"🟣 {line}"

def categorize_messages(lines):
    categories = {"🔵": [], "🟡": [], "🍏": [], "🟣": []}
    for line in lines:
        category = line[:2]
        if category in categories:
            categories[category].append(line)
    return categories

def get_header_footer(category, update_date):
    headers = {
        "🔵": f"📅 بروزرسانی {update_date}\n⬅️ موجودی سامسونگ ➡️\n",
        "🟡": f"📅 بروزرسانی {update_date}\n⬅️ موجودی شیایومی ➡️\n",
        "🍏": f"📅 بروزرسانی {update_date}\n⬅️ موجودی آیفون ➡️\n",
        "🟣": f"📅 بروزرسانی {update_date}\n⬅️ موجودی متفرقه ➡️\n",
    }
    footer = "\n\n☎️ شماره تماس:\n📞 09371111558\n📞 02833991417"
    return headers[category], footer

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    params = {"chat_id": CHAT_ID, "text": message, "parse_mode": "MarkdownV2"}
    requests.get(url, params=params)

def send_payment_message():
    message = (
        "✅ لیست گوشی‌ها بروز است. تحویل: 11:30 صبح روز بعد\n\n"
        "✅ شماره کارت:\n"
        "🔷 شبا: IR970560611828006154229701\n"
        "🔷 کارت: 6219861812467917\n"
        "🔷 بلو بانک: حسین گرئی\n\n"
        "⭕️ رسید واریز به @lhossein1 ارسال شود."
    )
    send_telegram_message(message)

def main():
    driver = get_driver()
    if not driver:
        return
    driver.get('https://hamrahtel.com/quick-checkout')
    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'mantine-Text-root')))
    scroll_page(driver)
    valid_brands = ["Galaxy", "POCO", "Redmi", "iPhone"]
    brands, models = extract_product_data(driver, valid_brands)
    driver.quit()
    if brands:
        processed_data = [f"{process_model(models[i])} {brands[i]}" for i in range(len(brands))]
        update_date = JalaliDate.today().strftime("%Y-%m-%d")
        message_lines = [decorate_line(row) for row in processed_data]
        categories = categorize_messages(message_lines)
        for category, lines in categories.items():
            if lines:
                header, footer = get_header_footer(category, update_date)
                send_telegram_message(header + "\n" + "\n".join(lines) + footer)
    send_payment_message()

if __name__ == "__main__":
    main()
