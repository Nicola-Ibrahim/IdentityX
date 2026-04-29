# 🛡️ IdentityX

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Domain-Driven Design](https://img.shields.io/badge/Architecture-DDD-blue?style=for-the-badge)](https://en.wikipedia.org/wiki/Domain-driven_design)

**IdentityX** is a high-performance, production-ready Identity and Access Management (IAM) service. Built with a strict adherence to **Domain-Driven Design (DDD)** and **Clean Architecture**, it provides a robust foundation for secure user authentication, session management, and role-based access control.

---

## ✨ Key Features

- 🔐 **Secure Authentication**: Multi-layered security with modern password hashing and verification.
- 🔄 **JWT Token Rotation**: Secure Access/Refresh token pairs with single-use refresh rotation to prevent replay attacks.
- 📂 **Stateful Sessions**: Database-backed session tracking for granular revocation and auditability.
- 🏗️ **Domain-Driven Design**: Clear separation of concerns with Domain, Application, and Infrastructure layers.
- 🎭 **Flexible RBAC**: Simplified yet powerful Account Role management via an extensible Enum-based system.
- 🚄 **Modern Tooling**: Leveraging `uv` for lightning-fast dependency management and `Ruff` for uncompromising code quality.

---

## 🛠️ Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python)
- **Database**: [PostgreSQL](https://www.postgresql.org/) with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) ORM
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Identity**: [PyJWT](https://pyjwt.readthedocs.io/) for token handling & [Azure Identity](https://learn.microsoft.com/en-us/python/api/overview/azure/identity-readme) for cloud-native secret management.
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/) for strict type safety and data integrity.
- **Tooling**: [uv](https://github.com/astral-sh/uv), [Ruff](https://github.com/astral-sh/ruff), [Pytest](https://docs.pytest.org/).

---

## 🚀 Getting Started

### Prerequisites

Ensure you have [uv](https://github.com/astral-sh/uv) installed:

```bash
curl -LsSf https://astral-sh.uv.run/install.sh | sh
```

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Nicola-Ibrahim/IdentityX.git
   cd IdentityX
   ```

2. **Setup the environment**:
   ```bash
   uv sync
   ```

3. **Run migrations**:
   ```bash
   uv run poe db-upgrade
   ```

4. **Start the development server**:
   ```bash
   uv run poe dev
   ```

The API will be available at `http://localhost:8000`. Explore the interactive documentation at `http://localhost:8000/docs`.

---

## 🏗️ Architecture

IdentityX follows a **Modular Monolith** approach inspired by Clean Architecture:

- **Domain**: Pure business logic, entities (Account, Session), and value objects (Email, Password).
- **Application**: Use cases and orchestration (AuthenticationService).
- **Infrastructure**: Concrete implementations of persistence (SQL Repositories), token generation, and external integrations.
- **API**: FastAPI routes and dependency injection.

---

## 🧪 Testing & Quality

We maintain high standards through automated testing and linting:

```bash
# Run tests
uv run poe test

# Check linting
uv run poe lint

# Format code
uv run poe format
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
