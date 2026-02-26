# Fleet SaaS — Project Context for AI

## Project Overview
B2B SaaS for vehicle fleet management. Multi-tenant architecture.
Stack: FastAPI + SQLAlchemy 2.0 + PostgreSQL + React.js + Celery + Redis.

## Architecture Rules
- Modular monolith: modules/ directory, each module has router/service/models/schemas
- All DB operations async (AsyncSession)
- All endpoints require authentication via Depends(get_current_user)
- All data scoped to tenant_id — never query without tenant filter
- Business logic in service.py, never in router.py
- HTTP exceptions raised in service layer, not router

## Code Conventions
- Python 3.11+, use type hints everywhere
- Pydantic v2 for schemas
- SQLAlchemy 2.0 style (select() not query())
- UUID primary keys for all models
- snake_case for Python, camelCase for JSON responses
- Always use async/await for I/O operations
- Mobile first design for frontend
- Use logging instead of print()
- Use environment variables for all config, never hardcode
- Use .env files for local development, but never commit them to git
- Use Alembic for DB migrations, never alter DB schema manually
- Use Resend for email notifications, never send emails directly from FastAPI
- Use Celery for any long-running tasks (reports, notifications), never block request threads
- Use pytest + pytest-asyncio for testing, never write tests that depend on external services (use mocks)
- Use factory
- Use a test driven approach: write tests before implementing features

## Database
- PostgreSQL 15 with Row Level Security
- Migrations via Alembic — never alter DB manually
- Connection: AsyncSession from app.core.database

## Current Modules
- auth: Google OAuth 2.0, JWT in httpOnly cookies
- fleet: Vehicle management, GPS positions
- orders: Order CRUD, CSV import/export
- reports: PDF generation, async via Celery
- notifications: Email via Resend

## What NOT to do
- Never use sync SQLAlchemy (db.query(...))
- Never hardcode tenant_id or user_id
- Never commit .env files
- Never write business logic in routers
- Never use print() — use logging

## Testing
- pytest + pytest-asyncio
- Test files in tests/modules/<module_name>/
- Use factories (factory_boy) for test data
- Each endpoint needs at least one happy path test
