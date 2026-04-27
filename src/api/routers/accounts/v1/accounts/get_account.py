from pydantic import BaseModel


class GetAccountRequest(BaseModel):
    account_id: str
