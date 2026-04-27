from pydantic import BaseModel


class DeleteAccountRequest(BaseModel):
    """Command/DTO for deleting an account."""

    account_id: str
