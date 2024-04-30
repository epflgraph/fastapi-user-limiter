# FastAPI rate limiter

This package adds a rate limiter to FastAPI using Redis.

## Installation

First install Redis, then install the package using:
```
pip install fastapi-user-limiter
```

## Usage

You can use the `rate_limit` decorator to put a single rate limit on an endpoint:

```python
app = FastAPI()
rate_limiter = RateLimiter()

# 2 requests max per 5 seconds
@app.get("/single")
@rate_limit(rate_limiter, 2, 5)
async def read_single(request: Request):
    return {"Hello": "World"}

```

To put multiple rate limits on the same endpoint (with different window size and maximum request counts), use the
`multi_rate_limit` decorator. Each `multi_rate_limit` decorator on a particular endpoint requires an ID as its first arg.
This ID must be unique among the `multi_rate_limit` decorators on that endpoint:

```python
app = FastAPI()
rate_limiter = RateLimiter()


# 1 request max per second, 3 requests max per 10 seconds
@app.get("/multi")
@multi_rate_limit(1, rate_limiter, 1, 1)
@multi_rate_limit(2, rate_limiter, 3, 10)
async def read_multi(request: Request):
    return {"Hello": "There"}
```

The aforementioned examples can be found in `example.py` (use ` uvicorn example:app --reload` to run).


**NOTE**: Every endpoint handler with the rate limiter decorator needs to have `request` (of type `fastapi.Request`) as its first argument.

## Future features

The package will soon have the additional feature of allowing each user account to have a different rate limit for each endpoint.
