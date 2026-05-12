from functools import wraps
from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel

from .exceptions import DomainError, DomainException

TResult = TypeVar("TResult")  # Type of the success value
TError = TypeVar("TError", bound=DomainException)  # Type of the error (must be an exception)


class Result(BaseModel, Generic[TResult, TError]):
    """
    Class for encapsulating the outcome of an operation,
    which can either succeed (SuccessResult) or fail (ErrorResult).
    """

    _value: TResult | None = None
    _error: TError | None = None

    def __post_init__(self):
        # Ensure that Result has either a value or an error, but not both
        if self._value is not None and self._error is not None:
            raise ValueError("Result cannot have both value and error.")
        if self._value is None and self._error is None:
            raise ValueError("Result must have either value or error.")

    @property
    def is_ok(self) -> bool:
        """Check if the result represents success."""
        return self._error is None

    @property
    def is_failure(self) -> bool:
        """Check if the result represents an error."""
        return self._error is not None

    @property
    def value(self) -> TResult:
        """Get the success value."""
        if self.is_failure:
            raise ValueError("Cannot access value on an error result.")
        return self._value

    @property
    def error(self) -> TError:
        """Get the error."""
        if self.is_ok:
            raise ValueError("Cannot access error on a success result.")
        return self._error

    def match(self, on_success: Callable[[TResult], Any], on_failure: Callable[[TError], Any]) -> Any:
        """
        Execute appropriate function based on result type.

        Args:
            on_success (Callable): Function to handle success.
            on_failure (Callable): Function to handle error.

        Returns:
            Any: The return value of the called function.
        """
        if self.is_ok:
            return on_success(self.value)
        return on_failure(self.error)

    @classmethod
    def ok(cls, value: TResult) -> "Result[TResult, TError]":
        """
        Factory method for creating a success result.

        Args:
            value (TResult): The value representing success.

        Returns:
            Result[TResult, TError]: A successful result.
        """
        instance = cls.model_construct()
        object.__setattr__(instance, "_value", value)
        return instance

    @classmethod
    def fail(cls, error: TError) -> "Result[TResult, TError]":
        """
        Factory method for creating an error result.

        Args:
            error (TError): The error representing failure.

        Returns:
            Result[TResult, TError]: An error result.
        """
        instance = cls.model_construct()
        object.__setattr__(instance, "_error", error)
        return instance

    @staticmethod
    def capture(func: Callable) -> Callable:
        """Wraps a service method to return a Result object."""

        @wraps(func)
        async def wrapper(*args, **kwargs) -> "Result":
            try:
                # Execute the pure service logic
                value = await func(*args, **kwargs)
                return Result.ok(value)
            except DomainError as e:
                # Catch known domain errors
                return Result.fail(e)
            except Exception as e:
                # Catch unexpected infrastructure errors
                return Result.fail(DomainError(message=str(e)))

        return wrapper
