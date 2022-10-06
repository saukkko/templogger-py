from pydantic import BaseModel, BaseConfig
from typing import Dict


class AuthResponse(BaseModel):
    code: int = 200
    msg: str = "OK"
    token_type: str | None
    token: str | None

    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "code": 200,
                "msg": "OK",
                "token_type": "Bearer",
                "token": "<token>"
            }
        }


class DataResponseBase(BaseModel):
    q: str
    reads: int | None = 2
    format: str
    delay: int | None = 2
    data: Dict[str, float] | str | None


class JSONDataResponse(DataResponseBase):
    format: str = "json"
    data: Dict[str, float]

    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "q": "all",
                "reads": 2,
                "format": "json",
                "delay": 2,
                "data": {
                    "humi": 39.2,
                    "temp": 24.1
                }
            }
        }


class HexDataResponse(DataResponseBase):
    format: str = "hex"
    data: str

    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "q": "all",
                "reads": 2,
                "format": "hex",
                "delay": 2,
                "data": "0304 018d 00f2 e1ba"
            }
        }


class Base64DataResponse(DataResponseBase):
    format: str = "base64"
    data: str

    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "q": "all",
                "reads": 2,
                "format": "base64",
                "delay": 2,
                "data": "AwQBiwDyAbs="
            }
        }


class HumanDataResponse(DataResponseBase):
    format: str = "human"
    data: str

    class Config(BaseConfig):
        schema_extra = {
            "example": {
                "q": "all",
                "reads": 2,
                "format": "human",
                "delay": 2,
                "data": "RH %: 39.3, °C: 24.2"
            }
        }
