from enum import Enum

ALLOWED_FILE_TYPES = ['.png', '.jpg']
S3_DELIMITER = "/"

class StorageOrigin(Enum):
    LOCAL = 'local'
    S3 = 's3'