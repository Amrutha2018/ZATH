# ZATH Authentication System

## Overview

The authentication system uses API keys stored in the `users` table. Every request (except public endpoints) automatically checks for a valid API key.

## How It Works

### 1. Middleware Protection

- All requests automatically go through authentication middleware
- Public paths (/, /docs, /redoc, /openapi.json, /auth/register, /auth/login) are excluded
- API keys can be sent via `X-API-Key` header or `Authorization: Bearer <key>`

### 2. User Registration

```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email": "user@example.com"}'
```

Response:

```json
{
  "id": "uuid",
  "email": "user@example.com",
  "api_key": "generated_api_key",
  "created_at": "2024-01-01T00:00:00"
}
```

### 3. Using Protected Endpoints

```bash
curl -X GET "http://localhost:8000/protected" \
     -H "X-API-Key: your_api_key_here"
```

### 4. Regenerating API Key

```bash
curl -X POST "http://localhost:8000/auth/regenerate-key" \
     -H "X-API-Key: your_current_api_key"
```

## Database Schema

The system uses the existing `users` table:

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Adding New Protected Endpoints

Simply create your endpoint normally. The middleware will automatically:

1. Check for API key
2. Validate the key against the database
3. Add user info to `request.state.user`

Example:

```python
@app.get("/my-protected-endpoint")
async def my_endpoint(request: Request):
    user = request.state.user
    return {"user_id": user['id'], "user_email": user['email']}
```

## Error Responses

- **401 Unauthorized**: Missing or invalid API key
- **400 Bad Request**: Email already exists during registration
