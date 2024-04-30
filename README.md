# FastAPI rate limiter

This package adds a rate limiter to FastAPI using Redis.

## Installation

First install Redis, then install the package using:
```
pip install fastapi-user-limiter
```

## Usage

You can use the `rate_limit` function as a FastAPI Dependency to add one or several rate limiters to an endpoint:

```python
from fastapi_user_limiter.limiter import RateLimiterConnection, rate_limiter
from fastapi import FastAPI, Depends

app = FastAPI()


# Max 2 requests per 5 seconds
@app.get("/single",
         dependencies=[Depends(rate_limiter(RateLimiterConnection(), 2, 5))])
async def read_single():
    return {"Hello": "World"}


# Max 1 requests per second and max 3 requests per 10 seconds
@app.get("/multi/{some_param}", dependencies=[
    Depends(rate_limiter(RateLimiterConnection(), 1, 1)),
    Depends(rate_limiter(RateLimiterConnection(), 3, 10))
])
async def read_multi(some_param: str):
    return {"Hello": f"There {some_param}"}
```

The aforementioned examples and more can be found in `example.py` (use ` uvicorn example:app --reload` to run).

## Future features

The package will soon have the additional feature of allowing each user account to have a different rate limit for each endpoint.
