# FastAPI rate limiter

This package adds a rate limiter to FastAPI using Redis.

## Installation

First install Redis, then install the package using:
```
pip install fastapi-user-limiter
```

## Usage

All the examples below can be found in `example.py` (use ` uvicorn example:app --reload` to run).

### Single and multiple rate limiters

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

### Router/API-wide rate limits

You can also add a router-wide (or even API-wide) rate limiter that applies to all endpoints taken together,
rather than per-endpoint:

```python
from fastapi_user_limiter.limiter import RateLimiterConnection, rate_limiter
from fastapi import Depends, APIRouter

# The rate limiter in the router applies to the two endpoints together.
# If a request is made to /single, a request to /single2 within the next 
# 3 seconds will result in a "Too many requests" error.

# This rate limiter must have a custom path value, preferably 
# the same as the router's prefix value.
router = APIRouter(
    prefix='/router',
    dependencies=[Depends(rate_limiter(RateLimiterConnection(), 1, 3,
                                       path='/router'))]
)


# Each endpoint also has its own, separate rate limiter
@router.get("/single",
            dependencies=[Depends(rate_limiter(RateLimiterConnection(), 3, 20))])
async def read_single_router():
    return {"Hello": "World"}


@router.get("/single2",
            dependencies=[Depends(rate_limiter(RateLimiterConnection(), 5, 60))])
async def read_single2_router():
    return {"Hello": "There"}
```

### Per-user rate limits

By default, rate limits are applied per host (i.e. per IP address). However, 
you may want to apply the rate limits on a per-user basis, especially if your
API has authentication. To do so, you can pass a custom callable to the
`user` argument of `rate_limiter`, which extracts the username from the request
headers:

```python
from fastapi_user_limiter.limiter import RateLimiterConnection, rate_limiter
from fastapi import Depends, FastAPI

app = FastAPI()


def get_user(headers):
    # The username is assumed to be a bearer token,
    # contained in the 'authorization' header.
    username = headers['authorization'].strip('Bearer ')
    return username

# 3 requests max per 20 seconds, per user
@app.post("/auth",
          dependencies=[Depends(rate_limiter(RateLimiterConnection(), 3, 20,
                                             user=get_user))])
async def read_with_auth(data: dict):
    return {'input': data}
```

## Future features

The package will soon have the additional feature of allowing each user account to have a different window size and max 
request count for each endpoint.
