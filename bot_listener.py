import requests
import time
import json
from checker import check_domain, load_json, save_json

CONFIG_FILE = "domains.json"
STATUS_FILE = "status.json"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_updates(bot_token, offset=None):
    url = f"https://api.telegram.org/bot{bot_token}/getUpdates?timeout=100"
    if offset:
        url += f"&offset={offset}"
    response = requests.get(url)
    return response.json()

def send_message(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def run_manual_check(config):
    timeout = config["timeout"]
    domains = config["domains"]

    ok_domains = []
    error_domains = []

    for domain in domains:
        url = domain["url"]
        result = check_domain(domain, timeout)
        line = f"{url} | Expected: {domain['expected_status']} | Got: {result['status']} | {result['reason']}"
        if result["ok"]:
            ok_domains.append(line)
        else:
            error_domains.append(line)

    messages = []
    if error_domains:
        messages.append("🚨 <b>Error Domains</b>:\n" + "\n".join(error_domains))
    if ok_domains:
        messages.append("✅ <b>OK Domains</b>:\n" + "\n".join(ok_domains))

    return messages

if __name__ == "__main__":
    config = load_config()
    BOT_TOKEN = config["telegram"]["bot_token"]
    print("Bot listener started...")

    # 🟢 FIX: initialize update_id to latest so old messages are skipped
    updates = get_updates(BOT_TOKEN)
    if updates.get("result"):
        update_id = updates["result"][-1]["update_id"] + 1
    else:
        update_id = None

    while True:
        updates = get_updates(BOT_TOKEN, update_id)
        if "result" in updates:
            for item in updates["result"]:
                update_id = item["update_id"] + 1
                message = item.get("message")
                if not message:
                    continue

                text = message.get("text", "")
                chat_id = message["chat"]["id"]

                if text.strip().lower() == "/check":
                    send_message(BOT_TOKEN, chat_id, "🖐️ Running manual check...")
                    msgs = run_manual_check(config)
                    for m in msgs:
                        send_message(BOT_TOKEN, chat_id, m)
                    send_message(BOT_TOKEN, chat_id, "✅ Manual check completed!")
