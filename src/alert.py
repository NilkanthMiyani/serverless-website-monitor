import boto3
import os
import logging

logger = logging.getLogger(__name__)
sns = boto3.client("sns")

if not os.environ.get("SNS_TOPIC_ARN"):
    logger.error("SNS_TOPIC_ARN environment variable not set")

TOPIC = os.environ.get("SNS_TOPIC_ARN", "")

def send_alert(subject, site, message):
    if not TOPIC:
        logger.error("SNS_TOPIC_ARN not configured, cannot send alert")
        raise ValueError("SNS_TOPIC_ARN environment variable not set")
    
    try:
        sns.publish(
            TopicArn=TOPIC,
            Subject=subject,
            Message=f"{site}\n{message}"
        )
    except Exception as e:
        logger.error(f"Failed to send alert to {site}: {e}")
        raise
