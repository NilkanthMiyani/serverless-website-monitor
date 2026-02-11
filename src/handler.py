import json
import os
import logging
from http_check import check_http
from ssl_check import check_ssl
from state import get_state, save_state
from alert import send_alert

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DDB_TABLE = os.environ["DDB_TABLE"]

def validate_environment():
    """Validate required environment variables."""
    required_env_vars = ["DDB_TABLE", "SNS_TOPIC_ARN"]
    missing = [var for var in required_env_vars if var not in os.environ]
    if missing:
        error_msg = f"❌ CRITICAL: Missing environment variables: {', '.join(missing)}"
        logger.error(error_msg)
        return error_msg
    return None

def validate_sites(sites):
    """Validate sites.json structure."""
    if not sites:
        return "sites.json is empty"
    
    required_fields = ["site", "url", "domain", "latency_threshold_ms"]
    for i, site in enumerate(sites):
        for field in required_fields:
            if field not in site:
                return f"Site {i}: missing required field '{field}'"
    return None

def lambda_handler(event, context):
    env_error = validate_environment()
    if env_error:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": env_error})
        }
    
    try:
        with open("sites.json") as f:
            sites = json.load(f)
    except FileNotFoundError:
        error_msg = "❌ CRITICAL ERROR: sites.json file not found"
        logger.error(error_msg)
        send_alert("🚨 MONITOR FAILED", "System", error_msg)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }
    except json.JSONDecodeError as e:
        error_msg = f"❌ CRITICAL ERROR: Invalid JSON in sites.json - {str(e)}"
        logger.error(error_msg)
        send_alert("🚨 MONITOR FAILED", "System", error_msg)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }
    
    validation_error = validate_sites(sites)
    if validation_error:
        logger.error(f"❌ sites.json validation failed: {validation_error}")
        send_alert("🚨 MONITOR FAILED", "System", f"Invalid sites.json: {validation_error}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": validation_error})
        }

    results = []
    errors = []

    for site in sites:
        site_name = site["site"]
        
        try:
            http_result = check_http(site)
            ssl_result = check_ssl(site)

            last = get_state(site_name)

            if http_result.get("redirect_warning") and not last.get("redirect_warning"):
                logger.warning(f"⚠️ REDIRECT WARNING: {site_name} - {http_result['message']}")
                send_alert(
                    "⚠️ REDIRECT DETECTED",
                    site_name,
                    f"{http_result['message']}\n\nSite is UP but returning redirect. Check if URL needs updating."
                )

            if last["status"] != http_result["status"]:
                if http_result["status"] == "DOWN":
                    consecutive = last.get("consecutive_failures", 0) + 1
                    if consecutive >= 1:
                        logger.info(f"🚨 ALERT: {site_name} is DOWN - {http_result['message']} (attempt {consecutive})")
                        send_alert(
                            "🚨 WEBSITE DOWN",
                            site_name,
                            f"{http_result['message']}\n\n(Failed {consecutive} times)"
                        )
                else:
                    logger.info(f"✅ ALERT: {site_name} RECOVERED from DOWN")
                    send_alert(
                        "✅ WEBSITE RECOVERED",
                        site_name,
                        "Website is back online"
                    )

            if http_result.get("latency_high") and not last.get("latency_high"):
                logger.info(f"⚠️ ALERT: {site_name} HIGH LATENCY - {http_result['message']}")
                send_alert(
                    "⚠️ HIGH LATENCY DETECTED",
                    site_name,
                    http_result["message"]
                )

            if ssl_result["alert"] and last.get("ssl_last_alert") != ssl_result["stage"]:
                logger.info(f"🔒 ALERT: {site_name} SSL - {ssl_result['subject']} - {ssl_result['message']}")
                send_alert(
                    ssl_result["subject"],
                    site_name,
                    ssl_result["message"]
                )

            save_state(site_name, http_result, ssl_result, last)
            results.append({site_name: http_result["status"]})
            
        except Exception as e:
            error_msg = f"Error checking {site_name}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            send_alert(
                f"⚠️ CHECK FAILED: {site_name}",
                site_name,
                f"Error: {str(e)}\n\nPlease review the logs."
            )

    if errors:
        logger.warning(f"Completed with {len(errors)} error(s)")
        return {
            "statusCode": 200,
            "body": json.dumps({
                "results": results,
                "errors": errors,
                "status": "completed_with_errors"
            })
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "results": results,
            "status": "success"
        })
    }
