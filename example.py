from fastapi_user_limiter.limiter import rate_limiter
from fastapi import FastAPI, Depends, APIRouter

router = APIRouter(
    prefix='/router',
    dependencies=[Depends(rate_limiter(1, 3,
                                       path='/router'))]
)


@router.get("/single",
            dependencies=[Depends(rate_limiter(3, 20))])
async def read_single_router():
    return {"Hello": "World"}


@router.get("/single2",
            dependencies=[Depends(rate_limiter(5, 60))])
async def read_single2_router():
    return {"Hello": "There"}


app = FastAPI()
app.include_router(router)


@app.get("/single",
         dependencies=[Depends(rate_limiter(2, 5))])
async def read_single():
    return {"Hello": "World"}


@app.get("/multi/{some_param}", dependencies=[
    Depends(rate_limiter(1, 1)),
    Depends(rate_limiter(3, 10))
])
async def read_multi(some_param: str):
    return {"Hello": f"There {some_param}"}


@app.post("/single_post",
          dependencies=[Depends(rate_limiter(4, 10))])
async def read_single(data: dict):
    return {'input': data}


async def get_user(headers):
    username = headers['authorization'].strip('Bearer ')
    return username


@app.post("/auth",
          dependencies=[Depends(rate_limiter(3, 20,
                                             user=get_user))])
async def read_with_auth(data: dict):
    return {'input': data}
