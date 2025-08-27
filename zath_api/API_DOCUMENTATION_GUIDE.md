# API Documentation Guide

## Overview
All API documentation is embedded directly in the code using FastAPI docstrings. This ensures documentation is always up-to-date and automatically appears in the FastAPI docs interface.

## Documentation Standards

### 1. Endpoint Documentation
Use comprehensive docstrings for all endpoint functions:

```python
@router.post("/endpoint", response_model=ResponseModel)
async def endpoint_function(request_data: RequestModel, request: Request):
    """
    Brief description of what the endpoint does.
    
    ## Request Body
    
    - **field1** (type, required/optional): Description with examples
    - **field2** (type, optional): Description
    
    ## Response
    
    Returns status code with response details:
    
    - **field1** (type): Description
    - **field2** (type): Description
    
    ## Authentication
    
    Requires valid API key in header:
    - `X-API-Key: your_api_key_here`
    - `Authorization: Bearer your_api_key_here`
    
    ## Example Usage
    
    ```bash
    curl -X POST "http://localhost:8000/api/endpoint" \\
         -H "Content-Type: application/json" \\
         -H "X-API-Key: your_api_key" \\
         -d '{"field1": "value1", "field2": "value2"}'
    ```
    
    ## Error Responses
    
    - **400 Bad Request**: Invalid input data
    - **401 Unauthorized**: Missing or invalid API key
    - **422 Unprocessable Content**: Validation errors
    - **500 Internal Server Error**: Database or server errors
    
    ## Notes
    
    Additional implementation details and usage notes.
    """
```

### 2. Model Documentation
Add docstrings and Field descriptions to Pydantic models:

```python
class RequestModel(BaseModel):
    """
    Request model for the endpoint.
    
    Attributes:
        field1: Description of field1
        field2: Description of field2
    """
    field1: str = Field(..., description="Description of field1")
    field2: Optional[str] = Field(None, description="Description of field2")
```

### 3. Self-Sufficient Files
Each API file should contain:
- Data models with documentation
- Validation logic
- Database operations
- Endpoint functions with comprehensive docstrings
- Error handling

### 4. File Structure
```
api/
├── routes.py          # Router aggregator (no documentation needed)
├── jobs.py            # Self-sufficient jobs API with full documentation
├── users.py           # Self-sufficient users API with full documentation
└── ...
```

## Benefits

1. **Always Up-to-Date**: Documentation is in the code
2. **Interactive**: FastAPI docs show live examples
3. **Discoverable**: Developers can explore APIs at `/docs`
4. **Maintainable**: No separate documentation files to keep in sync
5. **Self-Contained**: Each API file has everything it needs

## Viewing Documentation

- **Interactive Docs**: Visit `http://localhost:8000/docs`
- **OpenAPI Spec**: Visit `http://localhost:8000/openapi.json`
- **ReDoc**: Visit `http://localhost:8000/redoc`

## Adding New APIs

1. Create self-sufficient API file (e.g., `api/users.py`)
2. Add comprehensive docstrings to all functions and models
3. Add router to `api/routes.py`
4. Documentation automatically appears in FastAPI docs
