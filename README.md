# 🚀 ZATH - Zapier Async & Transformation Hub

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5+-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://www.docker.com/)

> **ZATH** is a powerful backend service that acts as an "off-ramp" for complex tasks in Zapier workflows. It addresses critical pain points in Zapier's automation platform by providing asynchronous job processing, advanced data transformations, and robust error handling.

## 🎯 **What Problem Does ZATH Solve?**

Zapier users face several significant limitations that ZATH directly addresses:

### **💰 Cost & Task Limitations**

- **High Task Costs**: Zapier charges per task, making complex workflows expensive
- **Task Limits**: Free plan limited to ~100 tasks/month, paid plans cap at 750-2000 tasks
- **Multi-step Penalties**: Complex workflows consume multiple tasks, increasing costs exponentially

### **⏱️ Timeout & Performance Issues**

- **30-Second Timeout**: HTTP requests timeout after ~30 seconds, breaking long-running processes
- **No Loops**: Zapier lacks native looping capabilities, forcing users to create multiple Zaps
- **Limited Processing**: Complex data transformations require multiple formatter steps

### **🔧 Technical Limitations**

- **No Mobile App**: No dedicated mobile app for monitoring and management
- **Poor Error Handling**: Vague error messages make debugging difficult
- **Limited Integration Depth**: Many integrations provide only basic triggers/actions
- **No Custom Code**: Limited ability to run custom scripts without consuming tasks

### **📊 Monitoring & Debugging**

- **Hidden Logs**: Limited visibility into job execution and failures
- **No Real-time Monitoring**: Difficult to track workflow performance
- **Poor Error Diagnostics**: Unclear error messages and limited debugging tools

---

## 🏗️ **Architecture Overview**

ZATH is built as a microservices architecture with the following components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Layer     │    │  Processing     │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Workers)     │
│   Port 3001     │    │   Port 8001     │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │   (Metadata)    │    │   (Job Queue)   │
                       └─────────────────┘    └─────────────────┘
```

---

## 🧩 **Core Components**

### **1. 🚀 FastAPI Backend (`zath_api/`)**

**Main Application (`main.py`)**

- FastAPI server with async capabilities
- CORS middleware for cross-origin requests
- Authentication middleware with API key validation
- OpenAPI documentation with security schemes
- Database connection pool management

**API Endpoints (`api/jobs.py`)**

- `POST /jobs` - Create new jobs
- `GET /jobs/{job_id}` - Get job status and details
- `GET /jobs` - List jobs with filtering and pagination
- `POST /jobs/{job_id}/retry` - Retry failed jobs
- `DELETE /jobs/{job_id}` - Cancel queued jobs
- `GET /jobs/dead-letter-queue` - View failed jobs
- `POST /jobs/dead-letter-queue/{job_id}/retry` - Retry dead letter jobs

**Authentication (`auth/`)**

- JWT token-based authentication
- API key management
- User registration and login
- Password reset functionality
- Secure middleware for protected endpoints

### **2. ⚙️ Job Processing System (`workers/`)**

**Job Worker (`job_worker.py`)**

- Asynchronous job processing from Redis queue
- Configurable processing delays and timeouts
- Automatic retry logic with exponential backoff
- Webhook callback delivery with retry mechanism
- Comprehensive error handling and logging
- Graceful shutdown and cleanup

**Task Handlers (`task_handlers.py`)**

- **HTTP Call Handler**: Simulates HTTP requests (extensible for real API calls)
- **Data Transform Handler**: Advanced data transformation with sequential processing
- **Email Send Handler**: Email delivery functionality
- **Webhook Call Handler**: External webhook notifications
- **File Upload Handler**: File processing capabilities
- **Report Generate Handler**: Report generation and formatting

**Logic Utilities (`logic_utils.py`)**

- **`map_records()`**: Apply functions to collections of data
- **`conditional()`**: Conditional logic with if/else branching
- **`create_condition_function()`**: Dynamic condition creation from specifications
- **`create_transform_function()`**: Dynamic transformation creation from specifications

**Transform Utilities (`transform_utils.py`)**

- **JSON Flattening**: Convert nested JSON to flat key-value pairs
- **CSV to JSON**: Convert CSV data to JSON format
- **Data Filtering**: Filter records based on conditions
- **Data Aggregation**: Aggregate data with various functions (sum, count, average)

### **3. 🗄️ Data Layer**

**PostgreSQL Database (`init.sql`)**

- **`jobs` table**: Job metadata, status, and configuration
- **`job_logs` table**: Comprehensive logging with different log levels
- **`users` table**: User authentication and API key management
- **Indexes**: Optimized queries for job status, task type, and timestamps
- **Constraints**: Data validation and referential integrity

**Redis Queue System**

- **Job Queue**: Primary queue for pending jobs
- **Dead Letter Queue**: Failed jobs that exceeded retry limits
- **Queue Statistics**: Monitoring and analytics
- **Job Prioritization**: Support for job priority levels

### **4. 📊 Logging & Monitoring (`utils/job_logger.py`)**

**Structured Logging System**

- **Batch Processing**: Efficient batch inserts for performance
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Metadata Support**: Rich context information for each log entry
- **Job Lifecycle Tracking**: Start, completion, failure, retry events
- **Callback Failure Tracking**: Special handling for webhook failures

### **5. 🎨 Frontend Dashboard (`zath_frontend/`)**

**Next.js Application**

- **React 19** with TypeScript
- **Material-UI** components for consistent design
- **Responsive Design** for mobile and desktop
- **Real-time Updates** with automatic refresh

**Key Features**

- **Job Dashboard**: Table view with filtering and pagination
- **Job Details**: Expandable rows with full job information
- **Status Management**: Retry and cancel job actions
- **Real-time Monitoring**: Live status updates
- **Error Display**: Detailed error messages and logs
- **Authentication**: Login and registration forms

---

## 🚀 **Quick Start**

### **Prerequisites**

- Docker and Docker Compose
- Git

### **1. Clone the Repository**

```bash
git clone <repository-url>
cd ZATH
```

### **2. Start Development Environment**

```bash
# Make scripts executable
chmod +x dev.sh prod.sh

# Start development environment
./dev.sh
```

### **3. Access the Application**

- **Frontend Dashboard**: http://localhost:3001
- **API Documentation**: http://localhost:8001/docs
- **API Endpoint**: http://localhost:8001

### **4. Create Your First Job**

```bash
curl -X POST "http://localhost:8001/jobs" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "data_transform",
    "payload": {
      "data": [{"name": "John", "age": 25}, {"name": "Jane", "age": 30}],
      "transformations": [
        {
          "type": "map",
          "function": "add_prefix",
          "params": {"prefix": "Mr. "}
        }
      ]
    },
    "callback_url": "https://hooks.zapier.com/hooks/catch/your-webhook-url"
  }'
```

---

## 🔧 **Configuration**

### **Environment Variables**

Create a `.env` file in the project root:

```env
# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=zathdb
DB_USER=zathuser
DB_PASSWORD=zathpass

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# JWT Configuration
JWT_SECRET_KEY=your-secure-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
SERVER_IP=localhost  # For production, use your server IP
```

### **Docker Compose Configuration**

- **Base**: `docker-compose.yml` - Core services configuration
- **Development**: `docker-compose.dev.yml` - Development overrides
- **Production**: `docker-compose.prod.yml` - Production overrides

---

## 📚 **API Reference**

### **Authentication**

All API endpoints (except public ones) require authentication via:

- **API Key**: `X-API-Key: your-api-key`
- **Bearer Token**: `Authorization: Bearer your-jwt-token`

### **Job Management**

#### **Create Job**

```http
POST /jobs
Content-Type: application/json
X-API-Key: your-api-key

{
  "task_type": "data_transform",
  "payload": {
    "data": [...],
    "transformations": [...]
  },
  "callback_url": "https://hooks.zapier.com/hooks/catch/..."
}
```

#### **Get Job Status**

```http
GET /jobs/{job_id}
X-API-Key: your-api-key
```

#### **List Jobs**

```http
GET /jobs?status=completed&task_type=data_transform&page=1&limit=20
X-API-Key: your-api-key
```

#### **Retry Job**

```http
POST /jobs/{job_id}/retry
X-API-Key: your-api-key
```

#### **Cancel Job**

```http
DELETE /jobs/{job_id}
X-API-Key: your-api-key
```

### **Task Types**

#### **1. HTTP Call (`http_call`)**

```json
{
  "task_type": "http_call",
  "payload": {
    "url": "https://api.example.com/data",
    "method": "GET",
    "headers": { "Authorization": "Bearer token" },
    "timeout": 30
  }
}
```

#### **2. Data Transform (`data_transform`)**

```json
{
  "task_type": "data_transform",
  "payload": {
    "data": [{ "name": "John", "age": 25 }],
    "transformations": [
      {
        "type": "map",
        "function": "add_field",
        "params": { "field": "status", "value": "active" }
      },
      {
        "type": "conditional",
        "condition": { "field": "age", "operator": ">=", "value": 18 },
        "if_transform": {
          "type": "add_field",
          "field": "category",
          "value": "adult"
        },
        "else_transform": {
          "type": "add_field",
          "field": "category",
          "value": "minor"
        }
      }
    ]
  }
}
```

#### **3. Email Send (`email_send`)**

```json
{
  "task_type": "email_send",
  "payload": {
    "to": "user@example.com",
    "subject": "Job Completed",
    "body": "Your job has been completed successfully.",
    "html": true
  }
}
```

#### **4. Webhook Call (`webhook_call`)**

```json
{
  "task_type": "webhook_call",
  "payload": {
    "url": "https://api.example.com/webhook",
    "method": "POST",
    "data": { "status": "completed", "result": "..." },
    "headers": { "Content-Type": "application/json" }
  }
}
```

---

## 🔄 **Zapier Integration**

### **How ZATH Integrates with Zapier**

1. **Trigger**: Zapier sends data to ZATH via webhook
2. **Process**: ZATH processes the job asynchronously
3. **Callback**: ZATH sends results back to Zapier via webhook
4. **Continue**: Zapier continues the workflow with the results

### **Zapier Workflow Example**

```
Zapier Trigger → ZATH API → Job Queue → Worker → Callback → Zapier Continue
```

### **Zapier Setup Steps**

1. **Create Webhook Action**: Use "Webhooks by Zapier" → "Custom Request"
2. **Configure Request**:
   - URL: `https://your-zath-instance.com/jobs`
   - Method: POST
   - Headers: `X-API-Key: your-api-key`
   - Body: Job payload with callback URL
3. **Add Catch Hook**: Use "Webhooks by Zapier" → "Catch Hook"
4. **Continue Workflow**: Use the callback data in subsequent steps

---

## 🧪 **Testing**

### **Run Tests**

```bash
# Run all tests
cd zath_api
python -m pytest

# Run specific test file
python -m pytest tests/test_jobs_api.py

# Run with coverage
python -m pytest --cov=.
```

### **Test Categories**

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **API Tests**: REST endpoint testing
- **Worker Tests**: Job processing testing
- **Logic Tests**: Data transformation testing

---

## 📊 **Monitoring & Observability**

### **Job Logs**

Every job execution is logged with:

- **Start/End Times**: Execution duration tracking
- **Status Changes**: Queued → In Progress → Completed/Failed
- **Error Details**: Stack traces and error messages
- **Retry Attempts**: Retry count and reasons
- **Callback Events**: Webhook delivery status

### **Dashboard Metrics**

- **Job Status Distribution**: Success/failure rates
- **Processing Times**: Average job duration
- **Queue Depth**: Pending job count
- **Error Rates**: Failure frequency by task type
- **Callback Success**: Webhook delivery rates

### **Health Checks**

- **API Health**: `GET /` - Basic API status
- **Database Health**: Connection pool status
- **Redis Health**: Queue connectivity
- **Worker Health**: Background process status

---

## 🚀 **Deployment**

### **Development Deployment**

```bash
# Start development environment
./dev.sh

# View logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f
```

### **Production Deployment**

```bash
# Set server IP
export SERVER_IP=your-server-ip

# Start production environment
./prod.sh

# View logs
docker compose -f docker-compose.yml -f docker-compose.prod.yml logs -f
```

### **Environment Differences**

- **Development**: Hot reload, localhost URLs, debug logging
- **Production**: Optimized builds, server IPs, production logging

---

## 🔒 **Security**

### **Authentication**

- **JWT Tokens**: Secure token-based authentication
- **API Keys**: Per-user API key management
- **Password Hashing**: bcrypt for secure password storage
- **CORS**: Configurable cross-origin resource sharing

### **Data Protection**

- **HTTPS**: SSL/TLS encryption in transit
- **Environment Variables**: Secure configuration management
- **Input Validation**: Pydantic models for data validation
- **SQL Injection Prevention**: Parameterized queries

### **Access Control**

- **User Isolation**: Users can only access their own jobs
- **API Key Scoping**: Per-user API key restrictions
- **Rate Limiting**: Configurable request rate limits
- **Audit Logging**: Comprehensive access logging

---

## 🛠️ **Development**

### **Project Structure**

```
ZATH/
├── zath_api/                 # FastAPI backend
│   ├── api/                  # API endpoints
│   ├── auth/                 # Authentication
│   ├── config/               # Configuration
│   ├── db/                   # Database connection
│   ├── workers/              # Job processing
│   ├── utils/                # Utilities
│   ├── tests/                # Test suite
│   └── main.py               # Application entry point
├── zath_frontend/            # Next.js frontend
│   ├── src/
│   │   ├── app/              # Next.js app router
│   │   ├── components/       # React components
│   │   └── lib/              # API client
│   └── package.json
├── docker-compose.yml        # Base Docker configuration
├── docker-compose.dev.yml    # Development overrides
├── docker-compose.prod.yml   # Production overrides
├── init.sql                  # Database schema
└── README.md                 # This file
```

### **Adding New Task Types**

1. **Create Handler**: Add handler function in `task_handlers.py`
2. **Update Router**: Add task type to API validation
3. **Add Tests**: Create test cases for new handler
4. **Update Documentation**: Document new task type

### **Adding New Transformations**

1. **Create Function**: Add transformation function in `logic_utils.py`
2. **Update Handler**: Integrate with data transform handler
3. **Add Tests**: Create test cases for new transformation
4. **Update Documentation**: Document new transformation

---

## 🤝 **Contributing**

### **Development Setup**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### **Code Standards**

- **Python**: Follow PEP 8 style guide
- **TypeScript**: Use strict type checking
- **Testing**: Maintain >80% code coverage
- **Documentation**: Update docs for new features

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- **FastAPI** - Modern, fast web framework for building APIs
- **Next.js** - React framework for production
- **Material-UI** - React component library
- **PostgreSQL** - Powerful, open source object-relational database
- **Redis** - In-memory data structure store
- **Docker** - Containerization platform

---

## 📞 **Support**

- **Documentation**: Check this README and API docs
- **Issues**: Report bugs via GitHub issues
- **Discussions**: Join community discussions
- **Email**: Contact the development team

---

**🎉 ZATH - Making Zapier workflows more powerful, efficient, and cost-effective!**
