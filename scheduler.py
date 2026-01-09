import time
import json
import requests
from checker import check_domain

CONFIG_FILE = "domains.json"
STATUS_FILE = "status.json"

# ---------------------------
# Telegram send_message function
# ---------------------------
def send_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

# ---------------------------
# Load config and status
# ---------------------------
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_status():
    try:
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f, indent=4)

# ---------------------------
# Run automatic check (scheduler)
# Only send ERROR domains to Telegram
# ---------------------------
def run_scheduler_check(config):
    timeout = config.get("timeout", 10)
    domains = config["domains"]
    telegram_cfg = config["telegram"]

    status = load_status()
    error_domains = []

    for domain in domains:
        url = domain["url"]
        expected = domain["expected_status"]
        result = check_domain(domain, timeout)
        line = f"{url} | Expected: {expected} | Got: {result['status']} | {result['reason']}"

        # Track errors only
        if not result["ok"]:
            error_domains.append(line)
            # Send Telegram alert if enabled
            if telegram_cfg["enabled"]:
                send_message(telegram_cfg["bot_token"], telegram_cfg["chat_id"], line)

        # Update status for future checks
        status[url] = result

    save_status(status)
    return error_domains

# ---------------------------
# Main loop
# ---------------------------
if __name__ == "__main__":
    config = load_config()
    interval = config.get("check_interval_minutes", 10) * 60
    print(f"Automatic monitoring started. Interval: {interval//60} minutes.")

    while True:
        errors = run_scheduler_check(config)
        if errors:
            print(f"Errors sent to Telegram:\n" + "\n".join(errors))
        time.sleep(interval)
