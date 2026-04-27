# 🌌 Horizon Chat System

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![Domain-Driven Design](https://img.shields.io/badge/DDD-Architecture-blue?style=for-the-badge)](docs/ddd/resources.md)

**Horizon Chat System** is a production-ready, AI-native communication platform built with a focus on high-quality software engineering principles. It leverages **Domain-Driven Design (DDD)** and a **Modular Monolith** architecture to provide a scalable, maintainable, and robust system for bot-driven and user-driven conversations.

---

## ✨ Project Highlights

- 🧩 **Modular Monolith**: Clear boundaries between Bounded Contexts (Auth, Chat, AI).
- 🏗️ **Clean Architecture**: Deep separation of Domain, Application, and Infrastructure concerns.
- 🤖 **AI-Native**: Seamlessly integrated with external AI providers for intelligent bot interactions.
- ⚡ **Event-Driven**: Asynchronous workflows powered by an internal mediator and domain events.
- 🚄 **Modern Tooling**: Leveraging `uv` for lightning-fast Python dependency management.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2.
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS.
- **Infrastructure**: PostgreSQL, Redis, NGINX, Docker & Docker Compose.
- **Development**: Ruff (linting), Pytest (testing), uv (package management).

---

## 🚀 Getting Started

Quickly spin up the entire stack using Docker:

```bash
docker compose -f docker-compose.dev.yml up --build
```

- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **API Documentation**: [http://localhost/docs](http://localhost/docs) (via NGINX)

For detailed local setup, troubleshooting, and backend/frontend development, visit the [**Setup Guide**](docs/building/setup.md).

---

## 📚 Documentation Deep-Dive

We take documentation seriously. Explore our detailed guides:

- **[Documentation Index](docs/README.md)** - Your map to everything.
- **[Architecture & Design](docs/design/architecture.md)** - How the system is built.
- **[DDD Implementation](docs/ddd/implementation.md)** - Mapping theory to our codebase.
- **[Feature Guides](docs/features/conversations.md)** - Details on Auth, RBAC, and Conversations.
