import boto3
from fastapi import HTTPException
from botocore.client import Config
from typing import Optional
import os
import json
import tempfile
import string
import random
import uuid

def generate_file_token(length):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

class S3Client:
    def __init__(self):
        self.endpoint = os.getenv("S3_ENDPOINT")
        self.bucket = os.getenv("S3_BUCKET")
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint,
            aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
            config=Config(signature_version='s3v4')
        )
        self._ensure_buckets_exist()

    def _ensure_buckets_exist(self):
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except:
            self.client.create_bucket(
                Bucket=self.bucket,
                ACL='public-read'
            )
        
            public_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": [f"arn:aws:s3:::{self.bucket}/*"]
                    }
                ]
            }
            
            self.client.put_bucket_policy(
                Bucket=self.bucket,
                Policy=json.dumps(public_policy)
            )

    def _generate_unique_filename(self, bucket: str, prefix: str, filename: str) -> str:
        base, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        
        while True:
            try:
                self.client.head_object(Bucket=bucket, Key=f"{prefix}/{new_filename}")
                new_filename = f"{base}_{counter}{ext}"
                counter += 1
            except:
                return new_filename

    async def upload_media_file(self, file, file_type: str, lesson_id: str):
        try:
            original_filename = file.filename.split('/')[-1] 
            unique_filename = self._generate_unique_filename(
                self.bucket,
                f"{file_type}/{lesson_id}",
                original_filename
            )
            
            s3_key = f"{file_type}/{lesson_id}/{unique_filename}"
            self.client.upload_fileobj(
                file.file,
                self.bucket,
                s3_key
            )

            return s3_key
        except Exception as e:
            raise HTTPException(500, f"Error uploading file: {e}")
    
    async def upload_avatar(self, file):
        try:
            type = file.filename.split('.')[-1]
            
            s3_key = f"users/{uuid.uuid4()}.{type}"
            self.client.upload_fileobj(
                file.file,
                self.bucket,
                s3_key
            )

            return s3_key
        except Exception as e:
            raise HTTPException(500, f"Error uploading file: {e}")

    def get_file(self, file_type: str, lesson_id: str, file_name: str):
        s3_key = f"{file_type}/{lesson_id}/{file_name}"
        local_file_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            self.client.download_file(self.bucket, s3_key, local_file_path)
            return local_file_path
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"File not found: {e}")
    
    def get_avatar(self, file_name: str):
        s3_key = f"users/{file_name}"
        local_file_path = os.path.join(tempfile.gettempdir(), file_name)

        try:
            self.client.download_file(self.bucket, s3_key, local_file_path)
            return local_file_path
        except Exception as e:
            raise HTTPException(status_code=404, detail=f"File not found: {e}")
        
    def delete_file(self, s3_key: str):
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=s3_key
            )
        except Exception as e:
            raise HTTPException(500, f'Error deleting file: {e}')