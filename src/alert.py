import boto3
import os

sns = boto3.client("sns")
TOPIC = os.environ["SNS_TOPIC_ARN"]

def send_alert(subject, site, message):
    sns.publish(
        TopicArn=TOPIC,
        Subject=subject,
        Message=f"{site}\n{message}"
    )
