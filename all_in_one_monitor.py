import time
import json
import requests
import threading
from datetime import datetime
from checker import check_domain

CONFIG_FILE = "domains.json"
STATUS_FILE = "status.json"

# -------------------------------------------------
# Telegram
# -------------------------------------------------
def send_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram error:", e)

# -------------------------------------------------
# Load / Save
# -------------------------------------------------
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_status():
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_status(status):
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, indent=4)

# -------------------------------------------------
# Format Message
# -------------------------------------------------
def format_block(title, lines):
    return f"<b>{title}</b>\n" + "\n".join(lines)

# -------------------------------------------------
# AUTOMATIC CHECK (Errors only)
# -------------------------------------------------
def run_scheduler_check():
    config = load_config()   # 🔥 reload every run
    timeout = config.get("timeout", 10)
    domains = config["domains"]
    tg = config["telegram"]

    status = load_status()
    errors = []

    for domain in domains:
        url = domain["url"]
        expected = domain["expected_status"]

        try:
            result = check_domain(domain, timeout)
        except Exception as e:
            result = {"ok": False, "status": "ERROR", "reason": str(e)}

        if not result["ok"]:
            line = f"{url}\nExpected: {expected}\nGot: {result['status']}\nReason: {result['reason']}"
            errors.append(line)

            if tg["enabled"]:
                send_message(tg["bot_token"], tg["chat_id"], f"🚨 <b>ERROR</b>\n{line}")

        status[url] = result

    save_status(status)
    return errors

# -------------------------------------------------
# MANUAL CHECK (/check)
# -------------------------------------------------
def run_manual_check(chat_id):
    config = load_config()   # 🔥 reload every run
    timeout = config.get("timeout", 10)
    domains = config["domains"]
    tg = config["telegram"]

    ok_list = []
    err_list = []
    status = load_status()

    for domain in domains:
        url = domain["url"]
        expected = domain["expected_status"]

        try:
            result = check_domain(domain, timeout)
        except Exception as e:
            result = {"ok": False, "status": "ERROR", "reason": str(e)}

        line = f"{url}\nExpected: {expected}\nGot: {result['status']}\nReason: {result['reason']}"

        if result["ok"]:
            ok_list.append(line)
        else:
            err_list.append(line)

        status[url] = result

    save_status(status)

    if tg["enabled"]:
        if err_list:
            send_message(tg["bot_token"], chat_id, format_block("🚨 ERROR DOMAINS", err_list))
        if ok_list:
            send_message(tg["bot_token"], chat_id, format_block("✅ OK DOMAINS", ok_list))

# -------------------------------------------------
# TELEGRAM BOT LISTENER
# -------------------------------------------------
def bot_listener():
    print("Telegram bot listener started...")
    last_update_id = None

    while True:
        config = load_config()
        BOT_TOKEN = config["telegram"]["bot_token"]

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?timeout=60"
        if last_update_id:
            url += f"&offset={last_update_id}"

        try:
            data = requests.get(url, timeout=10).json()
        except:
            time.sleep(5)
            continue

        for update in data.get("result", []):
            last_update_id = update["update_id"] + 1
            msg = update.get("message")
            if not msg:
                continue

            text = msg.get("text", "").lower().strip()
            chat_id = msg["chat"]["id"]

            if text == "/check":
                send_message(BOT_TOKEN, chat_id, "🔍 Running manual check...")
                run_manual_check(chat_id)
                send_message(BOT_TOKEN, chat_id, "✅ Manual check completed")

        time.sleep(1)

# -------------------------------------------------
# MAIN
# -------------------------------------------------
def main():
    config = load_config()
    interval = config.get("check_interval_minutes", 10) * 60

    print(f"Monitoring started — interval: {interval // 60} minutes")

    # Start Telegram listener
    threading.Thread(target=bot_listener, daemon=True).start()

    # Scheduler loop
    while True:
        run_scheduler_check()
        time.sleep(interval)

if __name__ == "__main__":
    main()
