#!/usr/bin/env python3
"""Build an S3 client from environment variables (optional alternative to ~/.aws)."""
import logging
import os

import boto3

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

# Prefer the standard AWS names (also used by the AWS CLI / boto3 default chain):
#   export AWS_ACCESS_KEY_ID="YOUR_KEY"
#   export AWS_SECRET_ACCESS_KEY="YOUR_SECRET"
ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MY_ACCESS_KEY")
SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MY_SECRET_ACCESS_KEY")

if not ACCESS_KEY or not SECRET_ACCESS_KEY:
    log.error("Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (or MY_ACCESS_KEY / MY_SECRET_ACCESS_KEY).")
    raise SystemExit(1)

s3 = boto3.client(
    "s3",
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_ACCESS_KEY,
)
log.info("S3 client created using environment credentials.")
