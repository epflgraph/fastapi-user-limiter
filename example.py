from fastapi_user_limiter.limiter import RateLimiter, rate_limit
from fastapi import FastAPI, Request


app = FastAPI()
rate_limiter = RateLimiter()


@app.get("/")
@rate_limit(rate_limiter, 5, 60)
async def read_root(request: Request):
    return {"Hello": "World"}
