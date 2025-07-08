import redis
import secrets
from datetime import timedelta
from fastapi import HTTPException

class RedisClient:
    def __init__(self):
        self.host = 'redis'
        self.port = 6379
        self.db=2
        self.decode_responses=True
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=self.db,
            decode_responses=self.decode_responses
        )

    def create_token(self, lesson_id):
        existing_tokens = self.client.keys('special_token:*')

        for token_key in existing_tokens:
            stored_lesson_id = self.client.get(token_key)
            if stored_lesson_id == str(lesson_id):
                token = token_key.split(":")[1]
                ttl = self.client.ttl(token_key)
                return {
                    "token": token,
                    "expires_in": f"{ttl // 3600}h {(ttl % 3600) // 60}m",
                    "already_exists": True
                }


        token = secrets.token_urlsafe(32)

        self.client.setex(
            name=f"special_token:{token}",
            time=timedelta(hours=24),
            value=lesson_id
        )

        return {"token": token, 'expires_in': "24h"}
    
    def verify_token(self, token) -> int:
        redis_key = f'special_token:{token}'
        index = self.client.get(redis_key)

        if not index:
            raise HTTPException(400, 'Invalid token')
        
        return int(index)
