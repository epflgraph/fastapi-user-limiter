from fastapi_user_limiter.limiter import RateLimiter, rate_limit
from fastapi import FastAPI, Depends


app = FastAPI()


@app.get("/single",
         dependencies=[Depends(rate_limit(RateLimiter(), 2, 5))])
async def read_single():
    return {"Hello": "World"}


@app.get("/multi/{some_param}", dependencies=[
    Depends(rate_limit(RateLimiter(), 1, 1)),
    Depends(rate_limit(RateLimiter(), 3, 10))
])
async def read_multi(some_param: str):
    return {"Hello": f"There {some_param}"}


@app.post("/single_post",
          dependencies=[Depends(rate_limit(RateLimiter(), 4, 10))])
async def read_single(data: dict):
    return {'input': data}
