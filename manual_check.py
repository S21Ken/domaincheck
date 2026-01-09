import json
from checker import run_check

CONFIG_FILE = "domains.json"

if __name__ == "__main__":
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    print("Manual check (all domains sent to Telegram)")
    run_check(config, send_alerts=False, show_all=True, send_all_status=True)
