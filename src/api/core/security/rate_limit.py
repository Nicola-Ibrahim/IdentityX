from fastapi import Request

async def get_email_key(request: Request) -> str:
    """
    Custom key function for rate limiting by email address in the request body.
    Allows us to block attacks targeting a specific user account.
    """
    # For now, we use the remote IP, but we can expand this to parse the request body
    # and return the email/username as the key.
    return request.client.host
