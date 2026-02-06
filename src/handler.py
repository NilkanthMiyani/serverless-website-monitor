import json
import os
from http_check import check_http
from ssl_check import check_ssl
from state import get_state, save_state
from alert import send_alert

DDB_TABLE = os.environ["DDB_TABLE"]

def lambda_handler(event, context):
    with open("sites.json") as f:
        sites = json.load(f)

    results = []

    for site in sites:
        site_name = site["site"]

        http_result = check_http(site)
        ssl_result = check_ssl(site)

        last = get_state(site_name)

        # ----- Status transition -----
        if last["status"] != http_result["status"]:
            if http_result["status"] == "DOWN":
                send_alert(
                    "🚨 WEBSITE DOWN",
                    site_name,
                    http_result["message"]
                )
            else:
                send_alert(
                    "✅ WEBSITE RECOVERED",
                    site_name,
                    "Website is back online"
                )

        # ----- Latency alert (only on first detection) -----
        if http_result.get("latency_high") and not last.get("latency_high"):
            send_alert(
                "⚠️ HIGH LATENCY DETECTED",
                site_name,
                http_result["message"]
            )

        # ----- SSL alerts (only if stage changed) -----
        if ssl_result["alert"] and last.get("ssl_last_alert") != ssl_result["stage"]:
            send_alert(
                ssl_result["subject"],
                site_name,
                ssl_result["message"]
            )

        save_state(site_name, http_result, ssl_result)
        results.append({site_name: http_result["status"]})

    return {"results": results}
