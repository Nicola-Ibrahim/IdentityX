import pytest
from unittest.mock import AsyncMock, MagicMock
from src.modules.accounts.application.account.service import AccountService
from src.modules.accounts.domain.account.account import Account
from src.modules.accounts.application.account.dto import AccountDTO

@pytest.mark.asyncio
async def test_register_account_async_flow():
    # Arrange
    mock_uow = AsyncMock()
    # Mock context manager
    mock_uow.__aenter__.return_value = mock_uow
    mock_uow.__aexit__.return_value = None
    
    # Mock account repository
    mock_uow.accounts.exists_by_email.return_value = False
    mock_uow.accounts.add = AsyncMock()
    mock_uow.commit = AsyncMock()
    
    mock_hasher = MagicMock()
    mock_hasher.encode.return_value = "hashed_password"
    
    mock_notifications = AsyncMock()
    mock_notifications.send_welcome_email = AsyncMock()
    
    service = AccountService(
        uow=mock_uow,
        password_hasher=mock_hasher,
        notification_service=mock_notifications
    )
    
    # Act
    account, dto = await service.register("test@example.com", "password123")
    
    # Assert
    assert isinstance(account, Account)
    assert isinstance(dto, AccountDTO)
    assert dto.email == "test@example.com"
    
    mock_uow.accounts.exists_by_email.assert_called_once_with("test@example.com")
    mock_uow.accounts.add.assert_called_once()
    mock_uow.commit.assert_called_once()
    mock_notifications.send_welcome_email.assert_called_once_with("test@example.com")
