from base64 import b64decode
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.middleware import cors, gzip, trustedhost, Middleware
from starlette.middleware.base import BaseHTTPMiddleware, Request, Response, RequestResponseEndpoint
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR
from typing import Union
from crypto import JSONToken, validate_credentials
from jwcrypto.jws import InvalidJWSSignature, InvalidJWSObject, JWKeyNotFound, JWException  # type: ignore
from AM2320 import AM2320
from models import HexDataResponse, HumanDataResponse, JSONDataResponse, Base64DataResponse, AuthResponse
from utils import fmt_response


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# TODO: publish
#   - push to github
#   - double check .gitignore
#   - document all functions and methods
#
# TODO: token renewal logic
#   - cookies?
#   - issue separate renewal token?
#   - set max_age for such token?
#
# TODO: keep track of issued tokens for the past n hours
#   - allow only one live token per user
#   - find out easiest way to invalidate any excess tokens
#
# TODO: publish /docs and/or /redoc to public
#   - fix documentation
#
# TODO: OAuth2?
#   - Too heavy for 1 GHz / 512 MB Raspberry Zero W?
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


dev = AM2320(loglevel="INFO")
jwt = JSONToken(private_key_path=f"keys/private_key.pem",
                public_key_path=f"keys/pubkey.pem")


class MyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, req: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        err_res = JSONResponse(status_code=HTTP_401_UNAUTHORIZED, content={
            "code": HTTP_401_UNAUTHORIZED, "message": "Unauthorized"})
        if req.headers.get("x-real-ip") != req.headers.get("x-forwarded-for"):
            return err_res
        if not req.headers.get("x-nginx-proxy") or req.headers.get("x-nginx-proxy") != "true":
            return err_res

        print(f"<<< Incoming request...")
        for header in req.headers.raw:
            key, value = header
            print(f"< '{key.decode()}: {value.decode()}'")
        print()

        print(f">>> Outgoing response...")
        res = await call_next(req)
        for k, v in [
            ("strict-transport-security",
             "max-age=63072000; includeSubDomains; preload"),
            ("X-Frame-Options", "DENY"),
            ("X-Content-Type-Options", "nosniff"),
            ("X-XSS-Protection", "1; mode=block")
        ]:
            res.headers.append(k, v)

        for header in res.headers.raw:
            key, value = header
            print(f"> '{key.decode()}: {value.decode()}'")
        print()

        return res


middlewares = [
    Middleware(cors.CORSMiddleware,
               allow_origins=["https://logger.sokru.fi"],
               allow_methods=["GET", "POST", "HEAD"]),
    Middleware(gzip.GZipMiddleware, compresslevel=6),
    Middleware(trustedhost.TrustedHostMiddleware,
               allowed_hosts=["logger.sokru.fi"]),
    Middleware(MyMiddleware)
]

app = FastAPI(middleware=middlewares)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.post("/api/authorize", response_model=AuthResponse)
async def authorize(authorization: str | None = Header(default=None)):
    if not authorization or len(authorization) < 1:
        raise HTTPException(HTTP_401_UNAUTHORIZED)
    r = AuthResponse()
    try:
        username, password = b64decode(
            authorization.lstrip("Basic")).decode("utf8").split(":")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    if validate_credentials(username, password):
        token = jwt.sign(payload={"app": "templogger"})
        r.token_type = "Bearer"
        r.token = token.serialize(compact=True)
        return r
    else:
        r.code = HTTP_401_UNAUTHORIZED
        r.msg = "Invalid credentials"
        raise HTTPException(status_code=r.code, detail=r.msg)


@app.get("/api/getData", response_model=Union[
    JSONDataResponse, HexDataResponse,
    Base64DataResponse, HumanDataResponse
])
async def get_data(q: str = Query(default="all", max_length=4),
                   reads: int | None = Query(default=2, max_length=1),
                   fmt: str | None = Query(
                       default="json", max_length=10, alias="format"),
                   delay: int | None = Query(default=2, max_length=1),
                   authorization: str | None = Header(default=None)):
    if not authorization or len(authorization) < 1:
        raise HTTPException(HTTP_401_UNAUTHORIZED)
    try:
        token_type, token = authorization.split(" ")
        if token_type != "Bearer":
            raise HTTPException(HTTP_400_BAD_REQUEST)
        jwt.verify(token, jwt.public_key)

    except InvalidJWSSignature as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))
    except JWKeyNotFound:
        raise HTTPException(status_code=HTTP_500_INTERNAL_SERVER_ERROR)
    except JWException or InvalidJWSObject as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        if not reads or not delay:
            raise ValueError("Required parameters missing")
        read_count = reads
        delay = delay
        if read_count < 2 or read_count > 4:
            raise ValueError("Read count should be between 2 and 4")
        if delay < 2 or delay > 5:
            raise ValueError("Delay should be between 2 and 5 seconds")
        dev.read_count = read_count
        dev.delay = delay
    except ValueError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=str(e))
    data = bytes(0)
    if q == "all":
        data = dev.get_all()
        pass
    elif q == "temp":
        data = dev.get_temperature()
        pass
    elif q == "humi":
        data = dev.get_humidity()
        pass

    results = {
        "q": q,
        "reads": read_count,
        "format": fmt,
        "delay": delay,
        "data": fmt_response(q, data, fmt)
    }
    return results
