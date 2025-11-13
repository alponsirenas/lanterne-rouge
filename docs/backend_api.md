# Backend API

## Overview

The Lanterne Rouge backend provides a REST API with email+password authentication, user management, and session tracking.

## Features

- **FastAPI Framework**: Modern, fast Python web framework
- **Email+Password Authentication**: Secure user registration and login
- **JWT Tokens**: Access and refresh token support
- **Admin Flag**: Support for admin users
- **Database Migrations**: Alembic for version-controlled schema changes
- **Audit Logging**: Track important user actions
- **Session Management**: Track and manage user sessions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run Database Migrations

```bash
alembic upgrade head
```

### 3. Seed Initial Users

```bash
python scripts/seed_database.py
```

This creates:
- **Admin user**: `admin@lanterne-rouge.com` / `admin_password_123`
- **Tester user**: `tester@lanterne-rouge.com` / `tester_password_123`

### 4. Start the Server

```bash
python scripts/run_backend.py
```

Or manually:

```bash
PYTHONPATH=src uvicorn lanterne_rouge.backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **Alternative Docs**: http://127.0.0.1:8000/redoc

## API Endpoints

### Health Check

**GET** `/healthz`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T04:26:27.968Z",
  "version": "1.0.0"
}
```

### Authentication

#### Register

**POST** `/auth/register`

Register a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "is_active": true,
  "is_admin": false,
  "created_at": "2025-11-13T04:26:27.968Z"
}
```

#### Login

**POST** `/auth/login`

Login and receive access and refresh tokens.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Refresh Token

**POST** `/auth/refresh`

Get new tokens using a refresh token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Configuration

Settings can be configured via environment variables:

```env
# Database
DATABASE_URL=sqlite:///./memory/lanterne.db

# Security
SECRET_KEY=your-secret-key-here
DEBUG=false

# Token expiration
# ACCESS_TOKEN_EXPIRE_MINUTES=30  # default
# REFRESH_TOKEN_EXPIRE_DAYS=7  # default
```

## Database Schema

### Users Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| email | String(255) | Unique email address |
| hashed_password | String(255) | Bcrypt hashed password |
| is_active | Boolean | Account active status |
| is_admin | Boolean | Admin privileges flag |
| created_at | DateTime | Account creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Sessions Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | User reference |
| access_token_jti | String(36) | JWT access token ID |
| refresh_token_jti | String(36) | JWT refresh token ID |
| is_valid | Boolean | Session validity |
| created_at | DateTime | Session creation time |
| expires_at | DateTime | Session expiration time |

### Audit Logs Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | User reference (nullable) |
| action | String(100) | Action type (login, register, etc.) |
| resource | String(100) | Resource type |
| resource_id | String(255) | Resource identifier |
| details | Text | Additional details |
| ip_address | String(45) | Client IP address |
| user_agent | String(500) | Client user agent |
| created_at | DateTime | Action timestamp |

## Database Migrations

### Create a New Migration

After modifying models:

```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1  # Rollback one migration
alembic downgrade base  # Rollback all migrations
```

### View Migration History

```bash
alembic history
alembic current
```

## Testing

Run all backend tests:

```bash
python -m pytest tests/test_backend_auth.py -v
```

Run specific test:

```bash
python -m pytest tests/test_backend_auth.py::test_login_success -v
```

## Security

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Tokens**: Signed with HS256 algorithm
- **Token Expiration**: Access tokens expire in 30 minutes, refresh tokens in 7 days
- **Unique Tokens**: Each token includes a unique identifier (jti) to prevent collisions
- **Session Tracking**: All sessions are tracked in the database
- **Audit Logging**: Important actions are logged for security monitoring

## Development

### Project Structure

```
src/lanterne_rouge/backend/
├── __init__.py
├── main.py                 # FastAPI application
├── api/
│   ├── __init__.py
│   ├── auth.py            # Authentication endpoints
│   └── health.py          # Health check endpoint
├── core/
│   ├── __init__.py
│   ├── config.py          # Settings management
│   └── security.py        # Security utilities
├── db/
│   ├── __init__.py
│   └── session.py         # Database session
├── models/
│   ├── __init__.py
│   └── user.py            # Database models
└── schemas/
    ├── __init__.py
    └── auth.py            # Pydantic schemas
```

### Adding New Endpoints

1. Create a new router in `src/lanterne_rouge/backend/api/`
2. Define Pydantic schemas in `src/lanterne_rouge/backend/schemas/`
3. Add models if needed in `src/lanterne_rouge/backend/models/`
4. Register router in `src/lanterne_rouge/backend/main.py`
5. Create tests in `tests/`

## Error Handling

The API returns standard HTTP status codes:

- **200**: Success
- **201**: Created
- **400**: Bad Request (validation errors, duplicate email)
- **401**: Unauthorized (invalid credentials, expired token)
- **403**: Forbidden (inactive account)
- **422**: Unprocessable Entity (validation errors)
- **500**: Internal Server Error

Error responses include a `detail` field:

```json
{
  "detail": "Error description"
}
```

## CORS Configuration

CORS is configured to allow requests from:
- `http://localhost:3000`
- `http://localhost:8000`

Modify `cors_origins` in `settings` to add more origins.
