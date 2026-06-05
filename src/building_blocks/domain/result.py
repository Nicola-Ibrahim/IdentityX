from __future__ import annotations

from typing import Any, Callable, Self, cast

from pydantic import BaseModel


class Result[TResult, TError: Exception](BaseModel):
    """
    Class for encapsulating the outcome of an operation,
    which can either succeed (SuccessResult) or fail (ErrorResult).
    """

    _value: TResult | None = None
    _error: TError | None = None

    @property
    def is_success(self) -> bool:
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
        return cast(TResult, self._value)

    @property
    def error(self) -> TError:
        """Get the error."""
        if self.is_success:
            raise ValueError("Cannot access error on a success result.")
        return cast(TError, self._error)

    def match(self, on_success: Callable[[TResult], Any], on_failure: Callable[[TError], Any]) -> Any:
        """
        Execute appropriate function based on result type.

        Args:
            on_success (Callable): Function to handle success.
            on_failure (Callable): Function to handle error.

        Returns:
            Any: The return value of the called function.
        """
        if self.is_success:
            return on_success(self.value)
        return on_failure(self.error)

    @classmethod
    def success(cls, value: TResult) -> Self:
        """
        Factory method for creating a success result.

        Args:
            value (TResult): The value representing success.

        Returns:
            Self: A successful result.
        """
        instance = cls.model_construct()
        object.__setattr__(instance, "_value", value)
        return instance

    @classmethod
    def fail(cls, error: TError) -> Self:
        """
        Factory method for creating an error result.

        Args:
            error (TError): The error representing failure.

        Returns:
            Self: An error result.
        """
        instance = cls.model_construct()
        object.__setattr__(instance, "_error", error)
        return instance
