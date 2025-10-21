from django.conf import settings
import boto3

class S3Service:
    @staticmethod
    def get_client():
        session = boto3.session.Session()

        return session.client(
            "s3",
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL)