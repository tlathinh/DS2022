#!/usr/bin/env python3
"""Download cloud.jpg from the shared ds2022-fall26 bucket."""
import logging

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

bucket_name = "ds2022-fall26"
key = "cloud.jpg"
local_file = "cloud.jpg"

try:
    s3 = boto3.client("s3")
    obj = s3.get_object(Bucket=bucket_name, Key=key)
    with open(local_file, "wb") as f:
        f.write(obj["Body"].read())
    log.info(f"Downloaded s3://{bucket_name}/{key} -> {local_file}")
except ClientError as e:
    log.error(f"Error downloading object: {e}")
