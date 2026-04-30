import functools
from typing import Any, Callable


def transactional(func: Callable) -> Callable:
    """
    Automatically wraps a service method in a Unit of Work transaction
    and commits upon successful completion.
    """

    @functools.wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        # We assume the service class has 'self.uow' injected
        async with self.uow:
            # Execute the actual business logic
            result = await func(self, *args, **kwargs)

            # If no exception was raised, commit automatically!
            await self.uow.commit()

            return result

    return wrapper
