import time
import urllib.request
import socket

TIMEOUT = 5
EXPECTED_STATUS = 200

def check_http(site):
    try:
        start = time.time()
        resp = urllib.request.urlopen(site["url"], timeout=TIMEOUT)
        latency = int((time.time() - start) * 1000)

        if resp.status != EXPECTED_STATUS:
            return {
                "status": "DOWN",
                "latency": latency,
                "message": f"HTTP {resp.status}"
            }

        if latency > site["latency_threshold_ms"]:
            return {
                "status": "UP",
                "latency": latency,
                "latency_high": True,
                "message": f"High latency: {latency} ms"
            }

        return {"status": "UP", "latency": latency, "latency_high": False, "message": "OK"}

    except (socket.timeout, Exception) as e:
        return {
            "status": "DOWN",
            "latency": None,
            "latency_high": False,
            "message": str(e)
        }
