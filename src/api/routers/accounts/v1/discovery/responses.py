from pydantic import BaseModel


class JWKResponse(BaseModel):
    kty: str
    alg: str
    use: str
    kid: str
    n: str
    e: str


class JWKSResponse(BaseModel):
    keys: list[JWKResponse]
