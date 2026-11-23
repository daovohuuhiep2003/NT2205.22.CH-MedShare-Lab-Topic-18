"""
MinIO S3 Object Storage Data Access Layer for MedShare-Lab.
Operates in Zone Z2 (Untrusted Storage Tier).
Stores only encrypted binary objects (DICOM, CT/MRI, X-ray, Ultrasound, PDF).
MinIO never holds cryptographic keys or plaintext data.
"""

import io
import re
from typing import BinaryIO, Optional
from urllib3.response import HTTPResponse

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    Minio = None
    S3Error = Exception


class MinioStorageError(Exception):
    """Base exception for MinIO storage operations."""
    pass


class ObjectNotFoundError(MinioStorageError):
    """Raised when an object or bucket is not found."""
    pass


class MinioStorage:
    """
    MinIO S3 client wrapper enforcing tenant-isolated bucket boundaries and ciphertext storage.
    """

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "medshare_admin",
        secret_key: str = "minio_secret_dev_pass",
        secure: bool = False,
        bucket_prefix: str = "medshare-",
    ):
        if Minio is None:
            raise MinioStorageError("minio Python package is not installed. Please install 'minio'.")
        
        self.endpoint = endpoint
        self.bucket_prefix = bucket_prefix
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

    def sanitize_bucket_name(self, tenant_id: str) -> str:
        """
        Converts tenant_id into a valid S3 bucket name (lowercase, alphanumeric, hyphens).
        Ensures RFC 1123 compliance.
        """
        clean = tenant_id.lower().strip()
        clean = re.sub(r"[^a-z0-9\-]", "-", clean)
        clean = re.sub(r"-+", "-", clean).strip("-")
        bucket_name = f"{self.bucket_prefix}{clean}"
        # Ensure length 3-63
        if len(bucket_name) < 3:
            bucket_name = f"{bucket_name}bucket"
        return bucket_name[:63]

    def ensure_bucket(self, bucket_name: str) -> None:
        """Creates the bucket if it does not already exist."""
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
        except S3Error as e:
            raise MinioStorageError(f"Failed to ensure bucket '{bucket_name}': {e}") from e

    def put_ciphertext(
        self,
        tenant_id: str,
        object_name: str,
        data_stream: BinaryIO,
        length: int,
        content_type: str = "application/octet-stream",
        metadata: Optional[dict[str, str]] = None,
    ) -> tuple[str, str]:
        """
        Uploads an encrypted file (ciphertext) to the tenant's isolated bucket.
        Returns: (bucket_name, object_name)
        """
        bucket_name = self.sanitize_bucket_name(tenant_id)
        self.ensure_bucket(bucket_name)

        try:
            self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=data_stream,
                length=length,
                content_type=content_type,
                metadata=metadata or {},
            )
            return bucket_name, object_name
        except S3Error as e:
            raise MinioStorageError(
                f"Failed to upload ciphertext to '{bucket_name}/{object_name}': {e}"
            ) from e

    def get_ciphertext(self, tenant_id: str, object_name: str) -> HTTPResponse:
        """
        Retrieves the ciphertext object stream from MinIO.
        Caller is responsible for calling .close() or .release_conn() on the response.
        """
        bucket_name = self.sanitize_bucket_name(tenant_id)
        try:
            response = self.client.get_object(bucket_name=bucket_name, object_name=object_name)
            return response
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket"):
                raise ObjectNotFoundError(f"Ciphertext object '{bucket_name}/{object_name}' not found: {e}") from e
            raise MinioStorageError(
                f"Failed to retrieve ciphertext from '{bucket_name}/{object_name}': {e}"
            ) from e

    def get_ciphertext_bytes(self, tenant_id: str, object_name: str) -> bytes:
        """Convenience method to retrieve ciphertext directly as bytes."""
        response = self.get_ciphertext(tenant_id, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    def delete_ciphertext(self, tenant_id: str, object_name: str) -> None:
        """Deletes an encrypted object from MinIO."""
        bucket_name = self.sanitize_bucket_name(tenant_id)
        try:
            self.client.remove_object(bucket_name=bucket_name, object_name=object_name)
        except S3Error as e:
            raise MinioStorageError(
                f"Failed to delete ciphertext from '{bucket_name}/{object_name}': {e}"
            ) from e

    def stat_ciphertext(self, tenant_id: str, object_name: str) -> dict:
        """Retrieves metadata of the stored ciphertext object."""
        bucket_name = self.sanitize_bucket_name(tenant_id)
        try:
            stat = self.client.stat_object(bucket_name=bucket_name, object_name=object_name)
            return {
                "bucket_name": stat.bucket_name,
                "object_name": stat.object_name,
                "size": stat.size,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "last_modified": stat.last_modified.isoformat() if stat.last_modified else None,
                "metadata": stat.metadata,
            }
        except S3Error as e:
            if e.code in ("NoSuchKey", "NoSuchBucket"):
                raise ObjectNotFoundError(f"Object '{bucket_name}/{object_name}' not found: {e}") from e
            raise MinioStorageError(f"Failed to stat '{bucket_name}/{object_name}': {e}") from e

    def list_ciphertexts(self, tenant_id: str, prefix: str = "") -> list[dict]:
        """Lists ciphertext objects under the given prefix in tenant bucket."""
        bucket_name = self.sanitize_bucket_name(tenant_id)
        try:
            if not self.client.bucket_exists(bucket_name):
                return []
            objects = self.client.list_objects(bucket_name=bucket_name, prefix=prefix, recursive=True)
            return [
                {
                    "object_name": obj.object_name,
                    "size": obj.size,
                    "etag": obj.etag,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                }
                for obj in objects
            ]
        except S3Error as e:
            raise MinioStorageError(f"Failed to list objects in '{bucket_name}': {e}") from e

