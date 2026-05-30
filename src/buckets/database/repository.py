from sqlalchemy.ext.asyncio import AsyncSession

from .session import SQLAlchemySessionFactory


class SQLBaseRepository[ModelType]:
    """Provides standard CRUD and automatic background session resolution."""

    def __init__(self, model: type[ModelType]):
        self.model = model

    @property
    def session(self) -> AsyncSession:
        """Dynamically fetches the session from the current context."""
        return SQLAlchemySessionFactory.get_current_session()
