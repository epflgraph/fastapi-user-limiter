import redis.asyncio as redis
from fastapi import Request, HTTPException, status
from starlette.datastructures import Headers
import time
import random
from typing import Union, Callable


DEFAULT_REDIS_URL = 'redis://localhost:6379/1'


class RateLimiterConnection:
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
        if self.redis is None:
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


def rate_limiter(max_requests: Union[int, None] = 10, window: Union[int, None] = 1,
                 path: Union[str, None] = None,
                 user: Union[Callable[[Headers, str], Union[str, dict]], None] = None,
                 redis_url: Union[str, None] = None):
    """
    Rate limiter dependency for FastAPI
    :param max_requests: Max # of requests in given time window
    :param window: Time window in seconds
    :param path: Custom path.
                 Can be used for a router-wide (or even API-wide) rate limit that applies to all
                 endpoints together, rather than each endpoint separately. For such a use case,
                 the dependency should be placed in the router or app constructor call, preferably
                 with the path parameter being equal to the router's prefix (for readability).
                 If None, the path of the request URL is used, creating a per-endpoint limit.
    :param user: Custom user callable.
                 Can be used with a custom callable that extracts the username from request header
                 in order to have a per-user rate-limit, rather than per-IP.
                 If None, the host of the client is used as the username.
    :param redis_url: URL for Redis server
    :return: Rate limiting async callable to be used as FastAPI dependency
    """
    async def _rate_limit(request: Request):
        # Providing a None value for either window or max_requests disables rate limiting
        if max_requests is None or window is None:
            return
        n_max_requests = max_requests
        window_size = window
        rlc = RateLimiterConnection(redis_url)

        # Checking to see if a custom path has been provided
        if path is None:
            path_name = request.url.path
        else:
            path_name = path

        # Checking to see if a custom callable has been provided for the username
        if user is None:
            user_name = request.client.host
        else:
            # The path value is passed to the user callable, regardless of whether
            # it's the default value or a custom path
            user_output = await user(request.headers, path_name)
            if isinstance(user_output, str):
                user_name = user_output
            else:
                assert 'username' in user_output.keys()
                user_name = user_output['username']
                n_max_requests = user_output.get('max_requests', n_max_requests)
                window_size = user_output.get('window', window_size)
                # Here we check again because the values may have been overridden
                if n_max_requests is None or window_size is None:
                    return

        # Generating the redis key
        key = f"rate_limit:{path_name}:{window_size}:{n_max_requests}:{user_name}"
        if await rlc.is_rate_limited(key, n_max_requests, window_size):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=get_rate_limited_message(n_max_requests, window_size)
            )
    return _rate_limit


def dummy_rate_limiter():
    """
    Dummy rate limiter for pytest dependency override
    :return: dummy rate limiter async callable
    """
    async def _dummy_limiter():
        return
    return _dummy_limiter
