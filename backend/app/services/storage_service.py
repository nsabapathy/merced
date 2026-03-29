"""File storage service with factory pattern.

Supports local storage and Azure Blob Storage.
Files are always stored locally first, then optionally uploaded to cloud.
"""
import os
import shutil
import logging
from abc import ABC, abstractmethod
from typing import Tuple
import aiofiles
from azure.storage.blob.aio import BlobServiceClient
from app.config import settings

log = logging.getLogger(__name__)

# Local upload directory
UPLOAD_DIR = "/tmp/uploads"


class StorageProvider(ABC):
    """Abstract base class for storage providers."""

    @abstractmethod
    async def upload_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """Upload a file. Returns (local_path, blob_path)."""
        pass

    @abstractmethod
    async def download_file(self, blob_path: str, file_path: str) -> None:
        """Download a file from storage."""
        pass

    @abstractmethod
    async def delete_file(self, blob_path: str) -> None:
        """Delete a file from storage."""
        pass

    @abstractmethod
    async def get_download_url(self, blob_path: str) -> str:
        """Get a download URL for a file."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider."""

    async def upload_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """Save file locally."""
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        local_path = f"{UPLOAD_DIR}/{filename}"

        async with aiofiles.open(local_path, 'wb') as f:
            await f.write(file_content)

        return local_path, local_path

    async def download_file(self, blob_path: str, file_path: str) -> None:
        """Copy file locally (blob_path is already a local path)."""
        async with aiofiles.open(blob_path, 'rb') as src:
            data = await src.read()

        async with aiofiles.open(file_path, 'wb') as dst:
            await dst.write(data)

    async def delete_file(self, blob_path: str) -> None:
        """Delete local file."""
        try:
            if os.path.isfile(blob_path):
                os.remove(blob_path)
            else:
                log.warning(f"File {blob_path} not found in local storage")
        except Exception as e:
            log.error(f"Error deleting file {blob_path}: {e}")

    async def get_download_url(self, blob_path: str) -> str:
        """Return local file path as "URL"."""
        return blob_path


class AzureStorageProvider(StorageProvider):
    """Azure Blob Storage provider with local caching."""

    def __init__(self):
        self.connection_string = settings.azure_storage_connection_string
        self.container_name = settings.azure_storage_container
        self.local_provider = LocalStorageProvider()

    async def upload_file(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """Save locally, then upload to Azure. Returns (local_path, azure_url)."""
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not configured")

        # Save locally first
        local_path, _ = await self.local_provider.upload_file(file_content, filename)

        # Upload to Azure
        try:
            async with BlobServiceClient.from_connection_string(
                self.connection_string
            ) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=filename
                )
                await blob_client.upload_blob(file_content, overwrite=True)

            # Return both paths: local for processing, Azure URL for record
            return local_path, f"{blob_client.account_name}/{self.container_name}/{filename}"
        except Exception as e:
            log.error(f"Error uploading file to Azure: {e}")
            raise RuntimeError(f"Error uploading file to Azure: {e}")

    async def download_file(self, blob_path: str, file_path: str) -> None:
        """Download file from Azure to local path."""
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not configured")

        try:
            filename = blob_path.split("/")[-1]
            async with BlobServiceClient.from_connection_string(
                self.connection_string
            ) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=filename
                )
                download_stream = await blob_client.download_blob()
                data = await download_stream.readall()

            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(data)
        except Exception as e:
            raise RuntimeError(f"Error downloading file from Azure: {e}")

    async def delete_file(self, blob_path: str) -> None:
        """Delete file from Azure and local storage."""
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not configured")

        try:
            filename = blob_path.split("/")[-1]
            async with BlobServiceClient.from_connection_string(
                self.connection_string
            ) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=filename
                )
                await blob_client.delete_blob()
        except Exception as e:
            log.error(f"Error deleting file from Azure: {e}")

        # Always delete local copy
        await self.local_provider.delete_file(blob_path)

    async def get_download_url(self, blob_path: str) -> str:
        """Get Azure blob URL."""
        if not self.connection_string:
            raise ValueError("Azure Storage connection string not configured")

        try:
            filename = blob_path.split("/")[-1]
            async with BlobServiceClient.from_connection_string(
                self.connection_string
            ) as blob_service_client:
                blob_client = blob_service_client.get_blob_client(
                    container=self.container_name,
                    blob=filename
                )
                return blob_client.url
        except Exception as e:
            raise RuntimeError(f"Error getting download URL: {e}")


def get_storage_provider() -> StorageProvider:
    """Factory function to get the appropriate storage provider."""
    if settings.azure_storage_connection_string:
        return AzureStorageProvider()
    else:
        return LocalStorageProvider()


storage_service = get_storage_provider()
