import redis.asyncio as redis
from fastapi import Request, HTTPException, status
import time
from functools import wraps
import random
from typing import Annotated


DEFAULT_REDIS_URL = 'redis://localhost:6379/1'


class RateLimiter:
    def __init__(self, redis_url: str = None):
        if redis_url is None:
            redis_url = DEFAULT_REDIS_URL
        self.redis_url = redis_url
        self.redis = None

    async def init_redis(self):
        """
        Initializes the Redis connection
        :return: None
        """
        if self.redis is None or not await self.redis.ping():
            self.redis = await redis.from_url(self.redis_url)

    async def is_rate_limited(self, key: str, max_requests: int, window: int) -> bool:
        """
        Given a key (client host + endpoint url), determines whether the rate limit has been reached
        :param key: Key consisting of client host plus endpoint URL
        :param max_requests: Maximum allowed # of requests in the given window
        :param window: Time window for rate limit
        :return: True if rate limited
        """
        # Negative max_requests values disable rate-limiting
        if max_requests < 0:
            return False
        current_time = time.time()
        current_time_key = (('%.06f' % current_time).replace('.', '')
                            + '%08d' % random.randint(0, int(1e7)))
        window_start = current_time - window
        await self.init_redis()
        async with self.redis.pipeline(transaction=True) as pipe:
            try:
                # Remove all name-score pairs with score < window_start for this key
                pipe.zremrangebyscore(key, 0, window_start)
                # Get number of elements for this key after elimination of invalid ones
                pipe.zcard(key)
                # Add new element to this key with current time as its name and score
                pipe.zadd(key, {current_time_key: current_time})
                # Set expiry for this key
                pipe.expire(key, window)
                results = await pipe.execute()
            except redis.RedisError as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Redis error: {str(e)}"
                ) from e
        # results[1] is the output of pipe.zcard(key), which gives you the # of requests made before
        # the current one.
        return results[1] >= max_requests


def get_rate_limited_message(max_requests, window):
    return (f"Too many requests, no more than {max_requests} requests "
            f"are allowed every {window} seconds.")


def rate_limit(rl: RateLimiter, max_requests: int, window: int):
    async def _rate_limiter(request: Annotated[Request, Request]):
        key = f"rate_limit:{request.url.path}:{window}:{max_requests}:{request.client.host}"
        if await rl.is_rate_limited(key, max_requests, window):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=get_rate_limited_message(max_requests, window)
            )
    return _rate_limiter
