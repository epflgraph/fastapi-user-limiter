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
from fastapi_user_limiter.limiter import rate_limiter
from fastapi import FastAPI, Depends

app = FastAPI()


# Max 2 requests per 5 seconds
@app.get("/single",
         dependencies=[Depends(rate_limiter(2, 5))])
async def read_single():
    return {"Hello": "World"}


# Max 1 requests per second and max 3 requests per 10 seconds
@app.get("/multi/{some_param}", dependencies=[
    Depends(rate_limiter(1, 1)),
    Depends(rate_limiter(3, 10))
])
async def read_multi(some_param: str):
    return {"Hello": f"There {some_param}"}
```

### Router/API-wide rate limits

You can also add a router-wide (or even API-wide) rate limiter that applies to all endpoints taken together,
rather than per-endpoint:

```python
from fastapi_user_limiter.limiter import rate_limiter
from fastapi import Depends, APIRouter

# The rate limiter in the router applies to the two endpoints together.
# If a request is made to /single, a request to /single2 within the next 
# 3 seconds will result in a "Too many requests" error.

# This rate limiter must have a custom path value, preferably 
# the same as the router's prefix value.
router = APIRouter(
    prefix='/router',
    dependencies=[Depends(rate_limiter(1, 3,
                                       path='/router'))]
)


# Each endpoint also has its own, separate rate limiter
@router.get("/single",
            dependencies=[Depends(rate_limiter(3, 20))])
async def read_single_router():
    return {"Hello": "World"}


@router.get("/single2",
            dependencies=[Depends(rate_limiter(5, 60))])
async def read_single2_router():
    return {"Hello": "There"}
```

### Per-user rate limits

By default, rate limits are applied per host (i.e. per IP address). However, 
you may want to apply the rate limits on a per-user basis, especially if your
API has authentication. To do so, you can pass a custom async callable to the
`user` argument of `rate_limiter`, which extracts the username from the request
headers:

```python
from fastapi_user_limiter.limiter import rate_limiter
from fastapi import Depends, FastAPI

app = FastAPI()


def get_user(headers, path):
    # The username is assumed to be a bearer token,
    # contained in the 'authorization' header.
    username = headers['authorization'].replace('Bearer ', '')
    return username

# 3 requests max per 20 seconds, per user
@app.post("/auth",
          dependencies=[Depends(rate_limiter(3, 20,
                                             user=get_user))])
async def read_with_auth(data: dict):
    return {'input': data}
```

#### User-based rate limit overrides
The async callable introduced above can be used to override `max_requests`
and/or `window` values for specific users by returning a `dict` instead of
a `str`. In the example below, the callable overrides and increases the 
value of `max_requests` for the user `"admin"` and for the endpoint
`/auth`:


```python
from fastapi_user_limiter.limiter import rate_limiter
from fastapi import Depends, FastAPI
from starlette.datastructures import Headers, URL


app = FastAPI()


# The user callable can return either of these two:
# A. One single string containing the username
# B. A dictionary that maps the key "username" to the username (obligatory), plus two optional keys:
#     i. "max_requests": overriding the endpoint's original max_requests value for this particular user
#     ii. "window": overriding the endpoint's original window value for this particular user
# Provide a None to "max_requests" or "window" in order to disable rate limiting (for the given
# user and endpoint).
# If a dictionary without a "username" key is provided, an AssertionError is raised.

async def get_user_with_override(headers: Headers, path: str):
    # This user callable returns a dictionary and overrides max_requests for the user "admin"
    # when the endpoint's URL is '/auth'.
    username = headers['authorization'].replace('Bearer ', '')
    result_dict = {"username": username}
    if username == 'admin' and path == '/auth':
        result_dict['max_requests'] = 7
    return result_dict

# 3 requests max per 20 seconds, per user
@app.post("/auth",
          dependencies=[Depends(rate_limiter(3, 20,
                                             user=get_user_with_override))])
async def read_with_auth(data: dict):
    return {'input': data}
```
