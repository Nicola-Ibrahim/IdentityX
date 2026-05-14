from pydantic import BaseModel


class JWKResponse(BaseModel):
    """Represents a single JSON Web Key."""

    kty: str
    alg: str
    use: str
    kid: str
    n: str
    e: str


class JWKSResponse(BaseModel):
    """Represents a set of JSON Web Keys."""

    keys: list[JWKResponse]
