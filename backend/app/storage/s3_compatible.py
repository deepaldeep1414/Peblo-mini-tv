"""
S3-compatible backend (works against Cloudflare R2 or MinIO -- both speak
the S3 API). This is what moving "from local disk to Cloudflare R2" looks
like: everything else in the app is unchanged; only STORAGE_BACKEND=s3 and
the STORAGE_S3_* env vars change. See README Part E for the discussion of
what does and doesn't change (mainly: multipart upload thresholds and
the fact that R2 has zero egress fees, so we stop worrying about read
costs to the viewer UI).
"""
import boto3
from botocore.client import Config

from app.storage.base import StorageBackend


class S3CompatibleStorage(StorageBackend):
    def __init__(self, endpoint: str, bucket: str, access_key: str, secret_key: str, region: str = "auto"):
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )

    def write_bytes(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def read_bytes(self, key: str) -> bytes:
        obj = self.client.get_object(Bucket=self.bucket, Key=key)
        return obj["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    def atomic_write_bytes(self, key: str, data: bytes, content_type: str = "application/json") -> None:
        # S3 PUT of a single object is already atomic from a reader's
        # perspective (readers see either the previous full object or the
        # new full object, never a partial one) -- there is no in-place
        # partial write API. We still stage-then-copy to a stable key so
        # the "current" catalogue key never 404s mid-publish for a caller
        # who read the key a moment before the PUT completed.
        staging_key = f"{key}.staging"
        self.client.put_object(Bucket=self.bucket, Key=staging_key, Body=data, ContentType=content_type)
        self.client.copy_object(Bucket=self.bucket, CopySource={"Bucket": self.bucket, "Key": staging_key}, Key=key)
        self.client.delete_object(Bucket=self.bucket, Key=staging_key)

    def url_for(self, key: str) -> str:
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=3600
        )
