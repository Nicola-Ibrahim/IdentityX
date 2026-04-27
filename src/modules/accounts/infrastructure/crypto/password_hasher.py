import base64
import hashlib
import hmac
import os

from ...application.interfaces import IPasswordHasher


class PBKDF2PasswordHasher(IPasswordHasher):  # type: ignore[misc]
    """Simple PBKDF2 based password hasher.

    The encoded format matches ``algorithm$iterations$salt$hash`` so it can
    be stored as text in the database.
    """

    def __init__(self, iterations: int = 390000, salt_length: int = 16) -> None:
        self._iterations = iterations
        self._salt_length = salt_length

    def encode(self, password: str) -> str:
        salt = os.urandom(self._salt_length)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, self._iterations)
        encoded_salt = base64.urlsafe_b64encode(salt).decode("ascii")
        encoded_hash = base64.urlsafe_b64encode(digest).decode("ascii")
        return f"pbkdf2_sha256${self._iterations}${encoded_salt}${encoded_hash}"

    def verify(self, plain_password: str, hashed_password: str) -> bool:
        try:
            algorithm, iterations_str, encoded_salt, encoded_hash = hashed_password.split("$")
            if algorithm != "pbkdf2_sha256":
                return False
            iterations = int(iterations_str)
            salt = base64.urlsafe_b64decode(encoded_salt.encode("ascii"))
            expected_hash = base64.urlsafe_b64decode(encoded_hash.encode("ascii"))
        except (ValueError, TypeError):
            return False
        digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(digest, expected_hash)
