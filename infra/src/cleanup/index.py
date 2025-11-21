import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Periodic cleanup task.
    """
    logger.info("Starting cleanup task")
    # Add cleanup logic here (e.g., removing old temporary files from S3)
    logger.info("Cleanup task completed")
    return {"statusCode": 200, "body": "Cleanup completed"}
