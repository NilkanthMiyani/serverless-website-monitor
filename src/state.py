import boto3
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

if not os.environ.get("DDB_TABLE"):
    logger.error("DDB_TABLE environment variable not set")
    
ddb = boto3.resource("dynamodb").Table(os.environ.get("DDB_TABLE", ""))

def get_state(site):
    resp = ddb.get_item(Key={"site": site})
    return resp.get("Item", {
        "status": "UNKNOWN",
        "consecutive_failures": 0
    })

def save_state(site, http, ssl, last_state=None):
    if last_state is None:
        last_state = get_state(site)
    consecutive_failures = last_state.get("consecutive_failures", 0)
    
    if http["status"] == "DOWN":
        consecutive_failures += 1
    else:
        consecutive_failures = 0
    
    ddb.put_item(
        Item={
            "site": site,
            "status": http["status"],
            "latency": http["latency"],
            "latency_high": http.get("latency_high"),
            "redirect_warning": http.get("redirect_warning", False),
            "ssl_stage": ssl.get("stage"),
            "ssl_last_alert": ssl.get("stage") if ssl.get("alert") else None,
            "consecutive_failures": consecutive_failures,
            "last_checked": datetime.utcnow().isoformat()
        }
    )
