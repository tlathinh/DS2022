#!/usr/bin/env python3
"""Delete one object from S3."""
import logging
import os

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# we use buckets named class-<USER> to avoid conflicts with other students
bucket_name = "class-" + os.environ.get("USER", "unknown")
key = "folder/in/bucket/file.txt"  # must exist in the bucket

try:
    s3 = boto3.client("s3")
    s3.delete_object(Bucket=bucket_name, Key=key)
    log.info(f"Deleted s3://{bucket_name}/{key}")
except ClientError as e:
    log.error(f"Error deleting object: {e}")
