from typing import Any, Callable, Generic, TypeVar

from pydantic import BaseModel

from .exceptions import BusinessRuleValidationException

TResult = TypeVar("TResult")  # Type of the success value
TError = TypeVar("TError", bound=BusinessRuleValidationException)  # Type of the error (must be an exception)


class Result(Generic[TResult, TError], BaseModel):
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

    def map(self, fn: Callable[[TResult], TResult]) -> "Result[TResult, TError]":
        """
        Transforms the value of a successful result.

        Args:
            fn (Callable): Function to apply on the success value.

        Returns:
            Result[TResult, TError]: A new result with the transformed value.
        """
        if self.is_ok:
            return Result.ok(fn(self.value))
        return self

    def flat_map(self, fn: Callable[[TResult], "Result[Any, TError]"]) -> "Result[Any, TError]":
        """
        Applies a function that returns a `Result` and flattens the result.

        Args:
            fn (Callable): Function that returns a `Result`.

        Returns:
            Result[Any, TError]: A flattened result.
        """
        if self.is_ok:
            return fn(self.value)
        return self

    def unwrap(self) -> TResult:
        """
        Returns the success value or raises an error if the result is a failure.

        Returns:
            TResult: The success value.

        Raises:
            ValueError: If the result is a failure.
        """
        if self.is_failure:
            raise ValueError(f"Unwrap failed with error: {self.error}")
        return self.value

    def __repr__(self) -> str:
        """
        Custom repr for better debugging.
        """
        if self.is_ok:
            return f"Result.ok({repr(self._value)})"
        return f"Result.fail({repr(self._error)})"

    @classmethod
    def ok(cls, value: TResult) -> "Result[TResult, TError]":
        """
        Factory method for creating a success result.

        Args:
            value (TResult): The value representing success.

        Returns:
            Result[TResult, TError]: A successful result.
        """
        return cls(_value=value)

    @classmethod
    def fail(cls, error: TError) -> "Result[TResult, TError]":
        """
        Factory method for creating an error result.

        Args:
            error (TError): The error representing failure.

        Returns:
            Result[TResult, TError]: An error result.
        """
        return cls(_error=error)


def resultify(fn: Callable[..., TResult]) -> Callable[..., Result[TResult, TError]]:
    """
    Decorator to convert a function that returns a value into a function that returns a Result.

    Args:
        fn (Callable): The function to decorate.

    Returns:
        Callable: The decorated function.
    """

    def inner(*args, **kwargs) -> Result[TResult, TError]:
        try:
            return Result.ok(fn(*args, **kwargs))
        except BusinessRuleValidationException as e:
            return Result.fail(e)

    return inner
