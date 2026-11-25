import logging
import os
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket = os.environ["BUCKET_NAME"]
    src, dst = event["source_key"], event["dest_key"]
    logger.info("Move requested: s3://%s/%s -> %s", bucket, src, dst)
    try:
        s3.copy_object(Bucket=bucket, Key=dst,
                       CopySource={"Bucket": bucket, "Key": src})
        logger.info("Copy successful")
        s3.delete_object(Bucket=bucket, Key=src)
        logger.info("Source deleted, move complete")
        return {"status": "moved", "from": src, "to": dst}
    except Exception:
        logger.error("Move failed", exc_info=True)
        raise