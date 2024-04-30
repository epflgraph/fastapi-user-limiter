from fastapi_user_limiter.limiter import RateLimiter, rate_limit, multi_rate_limit
from fastapi import FastAPI, Request


app = FastAPI()
rate_limiter = RateLimiter()


@app.get("/single")
@rate_limit(rate_limiter, 2, 5)
async def read_single(request: Request):
    return {"Hello": "World"}


@app.get("/multi")
@multi_rate_limit(1, rate_limiter, 1, 1)
@multi_rate_limit(2, rate_limiter, 3, 10)
async def read_multi(request: Request):
    return {"Hello": "There"}
