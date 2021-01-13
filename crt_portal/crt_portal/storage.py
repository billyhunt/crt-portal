from django.core.files.storage import get_storage_class
from storages.backends.s3boto3 import S3ManifestStaticStorage


class CachedS3Boto3Storage(S3ManifestStaticStorage):
    """
    Save compressed files to local storage before uploading to S3.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = get_storage_class("compressor.storage.CompressorFileStorage")()

    def save(self, name, content):
        self.local_storage._save(name, content)
        super().save(name, self.local_storage._open(name))
        return name
