import os
import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import from your internal database bucket
from src.buckets.database.config import SQLAlchemySettings
from src.buckets.database.session import SQLAlchemySessionFactory, _current_session
from src.buckets.database.table import BaseSQLTable

# Import models to register them with Metadata
import src.accounts.infrastructure.persistence.orm.models  # noqa: F401
from src.api.main import APIFactory

# Derive TEST_DATABASE_URL from DATABASE_URL if not explicitly defined
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    dev_db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/identityx")
    # Parse and suffix the database name with '_test'
    if dev_db_url:
        if not dev_db_url.endswith("_test"):
            base, db_name = (
                dev_db_url.split("://")[0] + "://" + dev_db_url.split("://")[1].rsplit("/", 1)[0],
                dev_db_url.rsplit("/", 1)[1],
            )
            if "?" in db_name:
                db_name, query = db_name.split("?", 1)
                TEST_DATABASE_URL = f"{base}/{db_name}_test?{query}"
            else:
                TEST_DATABASE_URL = f"{base}/{db_name}_test"
        else:
            TEST_DATABASE_URL = dev_db_url
    else:
        TEST_DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/identityx_test"


@pytest.fixture(scope="session")
async def session_factory():
    """
    Creates a real SQLAlchemySessionFactory using your internal logic.
    Initializes the schema once per test session.
    """
    # 1. Setup test settings
    settings = SQLAlchemySettings(url=TEST_DATABASE_URL, echo=False)

    # 2. Use your existing factory
    factory = SQLAlchemySessionFactory(config=settings)

    # 3. Initialize Schema
    async with factory._engine.begin() as conn:
        await conn.run_sync(BaseSQLTable.metadata.create_all)

    yield factory

    # 4. Cleanup
    await factory.dispose()


@pytest.fixture(scope="session")
def app():
    """Real FastAPI app instance."""
    # Override the environment so APIFactory uses the test DB
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    factory = APIFactory()
    return factory.create_app()


@pytest.fixture(scope="function")
async def db_session(session_factory):
    """
    Provides a real database session that rolls back after every test.
    Injects the session into your internal _current_session context.
    """
    # Start a connection and transaction
    connection = await session_factory._engine.connect()
    transaction = await connection.begin()

    # Create a session bound to this connection
    # (Using the underlying session_factory logic but pinned to the connection)
    session = session_factory._session_factory(bind=connection)

    # Inject into the context variable so Repository.get_current_session() works
    token = _current_session.set(session)

    yield session

    # Cleanup: Rollback ensures test isolation
    await session.close()
    await transaction.rollback()
    await connection.close()
    _current_session.reset(token)


@pytest.fixture(scope="function")
def client(app, db_session):
    """HTTP Client for testing."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def authenticated_client(client):
    """Helper for pre-authenticated client."""

    def _authenticate(email="test@example.com", password="Password123!"):
        client.post("/v1/accounts/register", json={"email": email, "password": password})
        res = client.post("/v1/accounts/login", data={"username": email, "password": password})
        token = res.json()["data"]["tokens"]["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})
        return client

    return _authenticate


@pytest.fixture(scope="function")
def assert_standard_response():
    """Helper to verify standard envelope."""

    def _assert(response, status_code=200, success=True):
        assert response.status_code == status_code
        data = response.json()
        assert "api_version" in data
        assert "timestamp" in data
        assert data["success"] is success
        return data

    return _assert
