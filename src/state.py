import boto3
import os
from datetime import datetime

ddb = boto3.resource("dynamodb").Table(os.environ["DDB_TABLE"])

def get_state(site):
    resp = ddb.get_item(Key={"site": site})
    return resp.get("Item", {"status": "UNKNOWN"})

def save_state(site, http, ssl):
    ddb.put_item(
        Item={
            "site": site,
            "status": http["status"],
            "latency": http["latency"],
            "latency_high": http.get("latency_high"),
            "ssl_stage": ssl.get("stage"),
            "ssl_last_alert": ssl.get("stage") if ssl.get("alert") else None,
            "last_checked": datetime.utcnow().isoformat()
        }
    )
