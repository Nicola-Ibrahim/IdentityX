from sqlalchemy import select

from src.shared.infrastructure.database.session import SQLAlchemySessionFactory
from src.accounts.application.account.dtos.account import AccountDTO
from src.accounts.application.account.queries.list_accounts_query_service import ListAccountsQueryService
from src.accounts.infrastructure.persistence.tables import AccountTable


class SQLListAccountsQueryService(ListAccountsQueryService):
    """
    SQLAlchemy implementation of ListAccountsQueryService.
    Bypasses domain models and repositories to optimize read-model performance.
    """

    async def list_accounts(self, limit: int = 100, offset: int = 0) -> tuple[AccountDTO, ...]:
        session = SQLAlchemySessionFactory.get_current_session()
        stmt = (
            select(AccountTable)
            .order_by(AccountTable.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await session.execute(stmt)
        records = result.scalars().all()

        return tuple(
            AccountDTO(
                id=str(record.id),
                email=record.email,
                is_verified=record.is_verified,
                is_active=record.is_active,
                roles=tuple(r.strip() for r in record.roles.split(",") if r.strip()),
            )
            for record in records
        )
