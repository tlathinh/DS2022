#!/usr/bin/env python3
"""Delete an S3 bucket (must be empty first — use 08-delete-all-objects.py)."""
import logging
import os

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# we use buckets named class-<USER> to avoid conflicts with other students
bucket_name = f"class-{os.environ.get('USER', 'unknown')}"

try:
    s3 = boto3.client("s3")
    # Bucket must be empty before it can be deleted.
    s3.delete_bucket(Bucket=bucket_name)
    log.info(f"Deleted bucket: {bucket_name}")
except ClientError as e:
    log.error(f"Error deleting bucket {bucket_name}: {e}")
