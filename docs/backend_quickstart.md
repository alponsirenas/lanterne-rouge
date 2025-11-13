# Backend Quick Start Guide

## Prerequisites

Ensure you have installed all dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start (3 Steps)

### 1. Initialize Database

Run the migrations to create the database tables:

```bash
alembic upgrade head
```

This creates:
- `users` table
- `sessions` table  
- `audit_logs` table

### 2. Seed Initial Accounts

Create admin and tester accounts:

```bash
python scripts/seed_database.py
```

This creates:
- **Admin**: `admin@lanterne-rouge.com` / `admin_password_123`
- **Tester**: `tester@lanterne-rouge.com` / `tester_password_123`

### 3. Start the Server

```bash
python scripts/run_backend.py
```

The API is now available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **API Documentation**: http://127.0.0.1:8000/redoc

## Testing the API

### Register a New User

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "myuser@example.com",
    "password": "mypassword123"
  }'
```

### Login

```bash
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "myuser@example.com",
    "password": "mypassword123"
  }'
```

Response:
```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### Use Access Token

Include the access token in the Authorization header:

```bash
curl -X GET http://127.0.0.1:8000/protected-endpoint \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh Token

When your access token expires (after 30 minutes), get a new one:

```bash
curl -X POST http://127.0.0.1:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

## Interactive API Docs

Visit http://127.0.0.1:8000/docs for interactive API documentation where you can:
- View all endpoints
- See request/response schemas
- Test endpoints directly in the browser
- Authenticate and save tokens

## Running Tests

```bash
python -m pytest tests/test_backend_auth.py -v
```

Expected output:
```
13 passed in ~5s
```

## Configuration

Configure via environment variables (create a `.env` file):

```env
# Database
DATABASE_URL=sqlite:///./memory/lanterne.db

# Security  
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=false

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Troubleshooting

### Database errors
If you encounter database errors, try resetting:
```bash
alembic downgrade base
alembic upgrade head
python scripts/seed_database.py
```

### Port already in use
Change the port in `scripts/run_backend.py` or run manually:
```bash
PYTHONPATH=src uvicorn lanterne_rouge.backend.main:app --host 127.0.0.1 --port 8080
```

### Import errors
Make sure PYTHONPATH includes src:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## Next Steps

- Read [Complete API Documentation](backend_api.md)
- Read [Verification Report](backend_verification.md)
- Explore the interactive docs at http://127.0.0.1:8000/docs
- Add new endpoints by following the structure in `src/lanterne_rouge/backend/api/`

## Support

For issues, please refer to:
1. [Backend API Documentation](backend_api.md)
2. [Backend Verification](backend_verification.md)
3. Interactive docs at `/docs` endpoint

---

**Security Note**: The default admin and tester passwords are for development only. Change them in production!
