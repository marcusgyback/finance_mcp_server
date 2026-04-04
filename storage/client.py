"""
StorageClient — boto3-based abstraction for Filestash and S3-compatible storage.

Configuration is read from environment variables:
    S3_ENDPOINT_URL   — Filestash endpoint, e.g. https://filestash.example.com/api/s3
    S3_ACCESS_KEY     — access key ID
    S3_SECRET_KEY     — secret access key
    S3_BUCKET_NAME    — default bucket
    S3_REGION         — region (default: us-east-1; Filestash typically ignores this)
"""

import os
from typing import List, Dict, Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class StorageClient:
    """Thin wrapper around boto3 S3 client configured for Filestash.

    Uses path-style addressing (required by Filestash and most S3-compatible
    services) rather than the default virtual-hosted style used by AWS S3.
    """

    def __init__(self) -> None:
        endpoint_url = os.getenv("S3_ENDPOINT_URL")
        access_key = os.getenv("S3_ACCESS_KEY")
        secret_key = os.getenv("S3_SECRET_KEY")
        region = os.getenv("S3_REGION", "us-east-1")

        self.bucket_name = os.getenv("S3_BUCKET_NAME", "")

        kwargs: Dict[str, Any] = {
            "region_name": region,
        }
        # Path-style addressing is required by Filestash and most S3-compatible
        # services. For native AWS S3 (no custom endpoint), use the default
        # virtual-hosted style to avoid redirect issues.
        if endpoint_url:
            kwargs["config"] = Config(s3={"addressing_style": "path"})
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if access_key and secret_key:
            kwargs["aws_access_key_id"] = access_key
            kwargs["aws_secret_access_key"] = secret_key

        self._client = boto3.client("s3", **kwargs)

    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """Return a list of object metadata dicts under the given prefix.

        Each dict contains:
            key           — full object key
            size          — size in bytes
            last_modified — datetime of last modification
        """
        results: List[Dict[str, Any]] = []
        paginator = self._client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=prefix)

        for page in pages:
            for obj in page.get("Contents", []):
                results.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                    }
                )
        return results

    def get_object(self, key: str) -> bytes:
        """Fetch the raw bytes of the object at *key*."""
        response = self._client.get_object(Bucket=self.bucket_name, Key=key)
        return response["Body"].read()

    def put_object(self, key: str, data: bytes) -> None:
        """Upload *data* to storage under *key*."""
        self._client.put_object(Bucket=self.bucket_name, Key=key, Body=data)

    def object_exists(self, key: str) -> bool:
        """Return True if an object with *key* exists in the bucket."""
        try:
            self._client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] in ("404", "NoSuchKey"):
                return False
            raise
