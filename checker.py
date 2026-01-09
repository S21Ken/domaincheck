import json
import requests
from datetime import datetime
from pathlib import Path
from telegram import send_message

STATUS_FILE = "status.json"


def load_json(file):
    if not Path(file).exists():
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def check_domain(domain, timeout):
    try:
        r = requests.get(domain["url"], timeout=timeout)
        return {
            "status": r.status_code,
            "ok": r.status_code == domain["expected_status"],
            "reason": r.reason
        }
    except requests.exceptions.Timeout:
        return {"status": "TIMEOUT", "ok": False, "reason": "Timeout"}
    except requests.exceptions.ConnectionError:
        return {"status": "NO CONNECTION", "ok": False, "reason": "Unreachable"}


def format_alert(url, domain, result, recovered=False):
    icon = "✅ RECOVERED" if recovered else "🚨 ALERT"

    return (
        f"{icon}\n\n"
        f"<b>{url}</b>\n"
        f"Expected: {domain['expected_status']}\n"
        f"Got: {result['status']}\n"
        f"Reason: {result['reason']}\n\n"
        f"Time: {datetime.now()}"
    )


def run_check(config, send_alerts=True, show_all=False, send_all_status=False):
    """
    send_alerts      -> True/False : enable/disable Telegram alerts
    show_all         -> True/False : print all domains to console
    send_all_status  -> True/False : send all domains to Telegram (manual mode)
    """
    status_db = load_json(STATUS_FILE)
    telegram_cfg = config["telegram"]

    for domain in config["domains"]:
        url = domain["url"]
        result = check_domain(domain, config["timeout"])
        prev = status_db.get(url)

        # Console output
        if show_all or not result["ok"]:
            state = "OK" if result["ok"] else "ERROR"
            print(f"{state} | {url} | {result['status']}")

        # Telegram alerts
        if telegram_cfg["enabled"]:
            if send_all_status:
                # Manual mode: send all statuses
                send_message(
                    telegram_cfg["bot_token"],
                    telegram_cfg["chat_id"],
                    format_alert(url, domain, result)
                )
            elif send_alerts:
                # Automatic mode: only errors or status change
                if prev is None and not result["ok"]:
                    send_message(
                        telegram_cfg["bot_token"],
                        telegram_cfg["chat_id"],
                        format_alert(url, domain, result)
                    )
                elif prev and prev["ok"] and not result["ok"]:
                    send_message(
                        telegram_cfg["bot_token"],
                        telegram_cfg["chat_id"],
                        format_alert(url, domain, result)
                    )
                elif prev and not prev["ok"] and result["ok"]:
                    send_message(
                        telegram_cfg["bot_token"],
                        telegram_cfg["chat_id"],
                        format_alert(url, domain, result, recovered=True)
                    )

        # Save state
        status_db[url] = result

    save_json(STATUS_FILE, status_db)
