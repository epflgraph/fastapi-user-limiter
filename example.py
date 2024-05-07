from fastapi_user_limiter.limiter import rate_limiter
from fastapi import FastAPI, Depends, APIRouter
from starlette.datastructures import Headers

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


# The user callable can return either of these two:
# A. One single string containing the username
# B. A dictionary that maps the key "username" to the username (obligatory), plus two optional keys:
#     i. "max_requests": overriding the endpoint's original max_requests value for this particular user
#     ii. "window": overriding the endpoint's original window value for this particular user
# Provide a None to "max_requests" or "window" in order to disable rate limiting (for the given
# user and endpoint).
# If a dictionary without a "username" key is provided, an AssertionError is raised.
async def get_user(headers, path):
    # This user callable returns a single string and does not override default rate limits.
    username = headers['authorization'].replace('Bearer ', '')
    return username


async def get_user_with_override(headers: Headers, path: str):
    # This user callable returns a dictionary and overrides max_requests for the user "admin"
    # when the endpoint's URL is '/auth'.
    username = headers['authorization'].replace('Bearer ', '')
    result_dict = {"username": username}
    if username == 'admin' and path == '/auth':
        result_dict['max_requests'] = 7
    return result_dict


@app.post("/auth",
          dependencies=[Depends(rate_limiter(3, 20,
                                             user=get_user_with_override))])
async def read_with_auth(data: dict):
    return {'input': data}
