import redis.asyncio as redis
from fastapi import Request, HTTPException, status
import time
from functools import wraps


DEFAULT_REDIS_URL = 'redis://localhost:6379/1'


class RateLimiter:
    def __init__(self, redis_url: str = None):
        if redis_url is None:
            redis_url = DEFAULT_REDIS_URL
        self.redis_url = redis_url
        self.redis = None

    async def init_redis(self):
        if self.redis is None or not await self.redis.ping():
            self.redis = await redis.from_url(self.redis_url)

    async def is_rate_limited(self, key: str, max_requests: int, window: int) -> bool:
        current = int(time.time())
        window_start = current - window
        await self.init_redis()
        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {current: current})
                pipe.expire(key, window)
                results = await pipe.execute()
            except redis.RedisError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Redis error: {str(e)}"
                ) from e
        return results[1] > max_requests


def rate_limit(rate_limiter: RateLimiter, max_requests: int, window: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            key = f"rate_limit:{request.client.host}:{request.url.path}"
            if await rate_limiter.is_rate_limited(key, max_requests, window):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests"
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
