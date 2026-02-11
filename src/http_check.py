import time
import urllib.request
import urllib.error
import socket
import random

TIMEOUT = 5
MIN_SUCCESS_STATUS = 200
MAX_SUCCESS_STATUS = 299
MIN_REDIRECT_STATUS = 300
MAX_REDIRECT_STATUS = 399
MAX_RETRIES = 2
RETRY_DELAY = 5
RETRY_JITTER = 2
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Website-Monitor/1.0"

def check_http(site):
    """
    Check HTTP status with retry logic.
    2xx = success, 3xx = warning, 4xx/5xx = error (retried).
    """
    for attempt in range(MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                site["url"],
                headers={"User-Agent": USER_AGENT}
            )
            
            start = time.time()
            resp = urllib.request.urlopen(req, timeout=TIMEOUT)
            latency = int((time.time() - start) * 1000)
            status_code = resp.status

            if MIN_REDIRECT_STATUS <= status_code <= MAX_REDIRECT_STATUS:
                if latency > site["latency_threshold_ms"]:
                    return {
                        "status": "UP",
                        "latency": latency,
                        "latency_high": True,
                        "redirect_warning": True,
                        "message": f"Redirect HTTP {status_code} - High latency: {latency} ms"
                    }
                return {
                    "status": "UP",
                    "latency": latency,
                    "latency_high": False,
                    "redirect_warning": True,
                    "message": f"Redirect HTTP {status_code} - Check configuration"
                }

            if MIN_SUCCESS_STATUS <= status_code <= MAX_SUCCESS_STATUS:
                if latency > site["latency_threshold_ms"]:
                    return {
                        "status": "UP",
                        "latency": latency,
                        "latency_high": True,
                        "redirect_warning": False,
                        "message": f"High latency: {latency} ms"
                    }
                return {
                    "status": "UP",
                    "latency": latency,
                    "latency_high": False,
                    "redirect_warning": False,
                    "message": "OK"
                }

            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY + random.uniform(0, RETRY_JITTER)
                time.sleep(delay)
                continue

            return {
                "status": "DOWN",
                "latency": latency,
                "redirect_warning": False,
                "message": f"HTTP {status_code} (after {MAX_RETRIES + 1} attempts)"
            }

        except urllib.error.HTTPError as e:
            latency = int((time.time() - start) * 1000) if 'start' in locals() else None
            error_msg = f"HTTP {e.code}"
            
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY + random.uniform(0, RETRY_JITTER)
                time.sleep(delay)
                continue
            
            return {
                "status": "DOWN",
                "latency": latency,
                "redirect_warning": False,
                "message": f"{error_msg} (after {MAX_RETRIES + 1} attempts)"
            }

        except (socket.timeout, urllib.error.URLError, Exception) as e:
            if attempt < MAX_RETRIES:
                delay = RETRY_DELAY + random.uniform(0, RETRY_JITTER)
                time.sleep(delay)
                continue
            
            return {
                "status": "DOWN",
                "latency": None,
                "latency_high": False,
                "redirect_warning": False,
                "message": f"{type(e).__name__}: {str(e)} (after {MAX_RETRIES + 1} attempts)"
            }
