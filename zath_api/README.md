# ZATH API - Asynchronous Job Processing System

A robust FastAPI-based backend system for managing asynchronous job processing with Redis queues, PostgreSQL persistence, and comprehensive authentication.

## 🚀 Features

### Core Functionality
- **Asynchronous Job Processing**: Create, queue, and monitor background jobs
- **Redis Job Queue**: Reliable job queuing with Redis
- **PostgreSQL Persistence**: Persistent job storage and user management
- **Real-time Status Updates**: Track job progress and completion
- **Webhook Callbacks**: Automatic notifications when jobs complete
- **Retry Logic**: Exponential backoff for failed callbacks

### Authentication & Security
- **Dual Authentication**: API key and JWT token support
- **User Registration/Login**: Email and password-based accounts
- **Password Reset**: Simple password reset flow
- **User Isolation**: Each user can only access their own jobs
- **Secure Password Hashing**: Bcrypt-based password security

### API Features
- **RESTful Design**: Clean, intuitive API endpoints
- **Comprehensive Documentation**: Auto-generated OpenAPI/Swagger docs
- **Input Validation**: Pydantic models for request/response validation
- **Error Handling**: Detailed error messages and proper HTTP status codes
- **CORS Support**: Cross-origin resource sharing for frontend integration

## 🏗️ Architecture

```
zath_api/
├── main.py                 # FastAPI application entry point
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container configuration
├── pytest.ini            # Test configuration
├── run_tests.py          # Test runner script
│
├── auth/                  # Authentication module
│   ├── models.py         # Pydantic models and JWT utilities
│   ├── routes.py         # Authentication endpoints
│   ├── middleware.py     # API key verification middleware
│   └── __init__.py
│
├── api/                   # API endpoints
│   ├── routes.py         # API router aggregation
│   ├── jobs.py           # Job management endpoints
│   └── __init__.py
│
├── db/                    # Database layer
│   ├── connection.py     # PostgreSQL connection pool
│   └── __init__.py
│
├── config/                # Configuration
│   ├── redis.py          # Redis client configuration
│   └── __init__.py
│
├── workers/               # Background job processing
│   ├── job_worker.py     # Main worker logic
│   ├── run_worker.py     # Worker entry point
│   └── __init__.py
│
└── tests/                 # Test suite
    ├── conftest.py       # Pytest configuration
    ├── test_authentication.py
    ├── test_jobs_api.py
    ├── test_callback_notifier.py
    ├── test_callback_retry.py
    └── README.md
```

## 🛠️ Technology Stack

- **Framework**: FastAPI (Python 3.10+)
- **Database**: PostgreSQL with asyncpg
- **Cache/Queue**: Redis with redis.asyncio
- **Authentication**: JWT (python-jose) + bcrypt
- **Validation**: Pydantic models
- **Testing**: pytest + pytest-asyncio
- **Containerization**: Docker + Docker Compose

## 📋 Prerequisites

- Python 3.10 or higher
- PostgreSQL 12 or higher
- Redis 6 or higher
- Docker and Docker Compose (for containerized setup)

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

1. **Clone and navigate to the project:**
   ```bash
   cd ZATH
   ```

2. **Start all services:**
   ```bash
   docker compose up --build -d
   ```

3. **Access the application:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Frontend: http://localhost:3000

### Option 2: Local Development

1. **Set up environment variables:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your database and Redis credentials
   ```

2. **Install dependencies:**
   ```bash
   cd zath_api
   pip install -r requirements.txt
   ```

3. **Start the API server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Start the worker (in a separate terminal):**
   ```bash
   python workers/run_worker.py
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `zath_api` directory:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=zathdb
DB_USER=zathuser
DB_PASSWORD=zathpass

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_SSL=false

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## 📚 API Documentation

### Authentication Endpoints

#### Register User
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Login User
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

#### Forgot Password
```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

#### Simple Password Reset
```http
POST /auth/simple-reset-password
Content-Type: application/json

{
  "email": "user@example.com",
  "new_password": "newpassword123"
}
```

### Job Management Endpoints

#### Create Job
```http
POST /api/jobs
X-API-Key: your_api_key
Content-Type: application/json

{
  "task_type": "email_send",
  "payload": {
    "to": "recipient@example.com",
    "subject": "Hello World",
    "body": "This is a test email"
  },
  "callback_url": "https://webhook.site/abc123"
}
```

#### Get Job Status
```http
GET /api/jobs/{job_id}
X-API-Key: your_api_key
```

#### List Jobs
```http
GET /api/jobs?page=1&limit=10&status=completed&task_type=email_send
X-API-Key: your_api_key
```

## 🧪 Testing

### Run All Tests
```bash
cd zath_api
python run_tests.py
```

### Run Specific Test Categories
```bash
# Authentication tests
pytest tests/test_authentication_pytest.py -v

# Job API tests
pytest tests/test_jobs_api.py -v

# Callback tests
pytest tests/test_callback_notifier.py -v
pytest tests/test_callback_retry.py -v

# Manual tests
python tests/test_jobs_manual.py
```

### Test Coverage
The test suite covers:
- ✅ User registration and authentication
- ✅ Job creation and status retrieval
- ✅ Job listing and filtering
- ✅ Callback notification system
- ✅ Retry logic with exponential backoff
- ✅ Error handling and edge cases
- ✅ API key and JWT authentication
- ✅ User isolation and security

## 🔒 Security Features

### Authentication
- **API Key Authentication**: For programmatic access
- **JWT Token Authentication**: For web frontend
- **Password Hashing**: Bcrypt with salt
- **Token Expiration**: Configurable JWT token lifetime

### Data Protection
- **User Isolation**: Jobs are isolated per user
- **Input Validation**: All inputs validated with Pydantic
- **SQL Injection Protection**: Parameterized queries
- **CORS Configuration**: Controlled cross-origin access

### Error Handling
- **Graceful Degradation**: System continues working even if Redis is down
- **Detailed Logging**: Comprehensive logging for debugging
- **Proper HTTP Status Codes**: Accurate error responses

## 📊 Monitoring & Logging

### Logging Configuration
The application uses structured logging with the following levels:
- **INFO**: General application events
- **WARNING**: Non-critical issues
- **ERROR**: Critical errors that need attention

### Health Checks
- **Database Connection**: Automatic connection pool management
- **Redis Connection**: Connection health monitoring
- **Worker Status**: Background job processing status

## 🚀 Deployment

### Production Considerations
1. **Environment Variables**: Use secure, environment-specific configuration
2. **Database**: Use managed PostgreSQL service
3. **Redis**: Use managed Redis service
4. **SSL/TLS**: Configure HTTPS for production
5. **Monitoring**: Set up application monitoring and alerting
6. **Backup**: Regular database backups
7. **Scaling**: Consider horizontal scaling for high load

### Docker Deployment
```bash
# Build production image
docker build -t zath-api .

# Run with production environment
docker run -d \
  --name zath-api \
  -p 8000:8000 \
  --env-file .env.production \
  zath-api
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the API documentation at `/docs`
2. Review the test files for usage examples
3. Check the logs for error details
4. Open an issue on the repository

---

**ZATH API** - Building reliable asynchronous job processing systems, one job at a time! 🚀
