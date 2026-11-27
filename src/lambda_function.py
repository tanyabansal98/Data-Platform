import logging
import os
from urllib.parse import unquote_plus
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.client("s3")


def move(bucket, src, dst):
    logger.info("Move requested: s3://%s/%s -> %s", bucket, src, dst)
    s3.copy_object(Bucket=bucket, Key=dst,
                   CopySource={"Bucket": bucket, "Key": src})
    logger.info("Copy successful")
    s3.delete_object(Bucket=bucket, Key=src)
    logger.info("Source deleted, move complete")


def lambda_handler(event, context):
    try:
        # Triggered by S3: the event contains a list of "Records"
        if "Records" in event:
            moved = []
            for record in event["Records"]:
                bucket = record["s3"]["bucket"]["name"]
                src = unquote_plus(record["s3"]["object"]["key"])
                if src.endswith("/") or not src.startswith("incoming/"):
                    logger.info("Skipping %s", src)
                    continue
                dst = "processed/" + src[len("incoming/"):]
                move(bucket, src, dst)
                moved.append({"from": src, "to": dst})
            return {"status": "moved", "files": moved}

        # Manual test event
        bucket = os.environ["BUCKET_NAME"]
        src, dst = event["source_key"], event["dest_key"]
        move(bucket, src, dst)
        return {"status": "moved", "from": src, "to": dst}
    except Exception:
        logger.error("Move failed", exc_info=True)
        raise