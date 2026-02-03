import ssl
import socket
from datetime import datetime

WARN_30 = 30
WARN_3 = 3

def check_ssl(site):
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((site["domain"], 443), timeout=5) as sock:
            with ctx.wrap_socket(sock, server_hostname=site["domain"]) as ssock:
                cert = ssock.getpeercert()

        expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
        days_left = (expiry - datetime.utcnow()).days

        if days_left <= WARN_3:
            return {
                "alert": True,
                "subject": "🚨 SSL EXPIRY CRITICAL",
                "message": f"Expires in {days_left} days ({expiry.date()})",
                "stage": "3D"
            }

        if days_left <= WARN_30:
            return {
                "alert": True,
                "subject": "⚠️ SSL EXPIRY WARNING",
                "message": f"Expires in {days_left} days ({expiry.date()})",
                "stage": "30D"
            }

        return {"alert": False, "stage": "OK"}

    except Exception:
        return {"alert": False, "stage": "UNKNOWN"}
