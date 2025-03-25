import boto3
from fastapi import HTTPException
from botocore.client import Config
from typing import Optional
import os
import json
import tempfile
import string
import random

def generate_file_token(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

class S3Client:
    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT")
        self.public_bucket = os.getenv("S3_PUBLIC_BUCKET")
        self.private_bucket = os.getenv("S3_PRIVATE_BUCKET")
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            config=Config(signature_version='s3v4')
        )
        self._ensure_buckets_exist()

    def _ensure_buckets_exist(self):
        for bucket in [self.private_bucket]:
            try:
                self.client.head_bucket(Bucket=bucket)
            except:
                self.client.create_bucket(Bucket=bucket)
        try:
            self.client.head_bucket(Bucket=self.public_bucket)
        except:
            self.client.create_bucket(
                Bucket=self.public_bucket,
                ACL='public-read'
            )
        
            public_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.public_bucket}/*"]
                    }
                ]
            }
            
            
            
            self.client.put_bucket_policy(
                Bucket=self.public_bucket,
                Policy=json.dumps(public_policy)
            )

    async def upload_media_file(self, file, file_type: str, lesson_id: str):
        try:
            filename = generate_file_token(32) + '.' + file.filename.split('.')[-1]
            s3_key = f"{file_type}/{lesson_id}/{filename}"
            self.client.upload_fileobj(
                file.file,
                self.public_bucket,
                s3_key
            )

            return s3_key
        except Exception as e:
            raise HTTPException(500, f"Error uploading file: {e}")

    def get_file(self, file_type: str, lesson_id: str, file_name: str):
        s3_key = f"{file_type}/{lesson_id}/{file_name}"
        local_file_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            self.client.download_file(self.public_bucket, s3_key, local_file_path)
            return local_file_path
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"File not found: {e}")
        
    def delete_file(self, s3_key: str, isPublic: bool = True):
        try:
            self.client.delete_object(
                Bucket=self.public_bucket if isPublic else self.private_bucket,
                Key=s3_key
            )
        except Exception as e:
            raise HTTPException(500, f'Error deleting file: {e}')
        
    def upload_file_from_path(self, file_path: str, user_id: str):
        try:
            file_name = os.path.basename(file_path)
            s3_key = f"{user_id}/{file_name}"
            
            self.client.upload_file(
                file_path,
                self.private_bucket,
                s3_key
            )
            return s3_key
        except Exception as e:
            raise HTTPException(500, f"Error uploading file from path: {e}")
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                raise HTTPException(500, f"Warning: failed to delete local file {file_path}: {e}")

    def get_temporary_file(self, user_id: str, file_name: str):
        s3_key = f"{user_id}/{file_name}"
        local_file_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            self.client.download_file(self.private_bucket, s3_key, local_file_path)
            return local_file_path
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"Private file not found: {e}")