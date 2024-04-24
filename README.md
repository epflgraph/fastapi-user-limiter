# FastAPI rate limiter

This package adds a rate limiter to FastAPI using Redis.

## Installation

First install Redis, then install the package using:
```
pip install fastapi-user-limiter
```

## Usage

An example of how to use the rate limiter can be found in `example.py`:

```
from fastapi_user_limiter.limiter import RateLimiter, rate_limit
from fastapi import FastAPI, Request


app = FastAPI()
rate_limiter = RateLimiter()


@app.get("/")
@rate_limit(rate_limiter, 5, 60)
async def read_root(request: Request):
    return {"Hello": "World"}
```

Every endpoint handler with the rate limiter decorator needs to have `request` (of type `fastapi.Request`) as its first argument.

## Future features

The package will soon have the additional feature of allowing each user account to have a different rate limit for each endpoint.
