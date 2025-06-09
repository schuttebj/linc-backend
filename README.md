# LINC Driver's Licensing System - Backend

## Overview

LINC (Licensing Infrastructure for National Compliance) is a modern, modular driver's licensing platform designed for African countries. This backend provides a robust, multi-tenant API with country-specific configurations, comprehensive audit logging, and scalable file storage.

## Features

- **Multi-Tenant Architecture**: Separate databases per country with shared application logic
- **Country-Specific Configuration**: Customizable modules, license types, fees, and compliance requirements
- **Comprehensive Audit Logging**: Full transaction tracking with business rule validation
- **Secure File Storage**: Local file management with audit trails
- **RESTful API**: OpenAPI/Swagger documentation with versioning
- **Business Rule Engine**: Implementation of driver licensing validation rules
- **Performance Monitoring**: Built-in metrics and health checks

## Technology Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL with SQLAlchemy 2.0+
- **Migration**: Alembic
- **Authentication**: JWT with passlib
- **Logging**: Structured logging with structlog
- **Validation**: Pydantic schemas
- **Testing**: pytest with coverage

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- pip or pipenv

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd LINC\ Backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp env.example .env
# Edit .env with your configuration
```

5. **Set up databases**
```bash
# Create databases for each country
createdb linc_south_africa
createdb linc_kenya
createdb linc_nigeria
```

6. **Run database migrations**
```bash
alembic upgrade head
```

7. **Start the development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive API Docs**: http://localhost:8000/api/v1/docs
- **ReDoc Documentation**: http://localhost:8000/api/v1/redoc
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.json

## Environment Configuration

Key environment variables (see `env.example` for complete list):

```bash
# Database URLs (one per country)
DATABASE_URL_ZA=postgresql://user:pass@localhost/linc_south_africa
DATABASE_URL_KE=postgresql://user:pass@localhost/linc_kenya

# File Storage
FILE_STORAGE_BASE_PATH=/var/linc-data

# Security
SECRET_KEY=your-secure-secret-key-here

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

## Multi-Tenant Architecture

### Country-Specific Databases

Each country has its own PostgreSQL database:
- **South Africa**: `linc_south_africa`
- **Kenya**: `linc_kenya`  
- **Nigeria**: `linc_nigeria`

### API Routing

All country-specific endpoints include the country code:
```
GET /api/v1/{country}/persons/search
POST /api/v1/{country}/persons/
```

## Business Rules Implementation

The system implements comprehensive validation rules:

- **V00001-V00999**: Person identification and validation
- **V01000-V01999**: License application processing
- **V02000-V02999**: Professional driving permits
- **V04000-V04999**: Financial processing

Example validation implementation:
```python
# Implements V00001: Identification Type Mandatory
if not person.identification_type:
    raise ValidationError("V00001", "Identification type is mandatory")
```

## File Storage

Files are stored locally with country separation:
```
/var/linc-data/
├── ZA/
│   ├── images/citizens/photos/
│   ├── images/licenses/cards/
│   └── audit/logs/
├── KE/
│   └── ...
```

## Deployment

### Render.com Deployment

1. **Create Render account** and connect your repository

2. **Set up PostgreSQL database** on Render

3. **Configure environment variables** in Render dashboard:
```bash
POSTGRES_URL=postgresql://user:pass@hostname/database
SECRET_KEY=your-production-secret-key
ALLOWED_ORIGINS=["https://your-frontend-domain.com"]
```

4. **Deploy using render.yaml** (create this file):
```yaml
services:
  - type: web
    name: linc-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.0
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_persons.py
```

### Code Quality

```bash
# Format code
black app/

# Lint code
ruff app/

# Type checking (if using mypy)
mypy app/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## API Endpoints

### Health Checks
- `GET /health` - Basic health check
- `GET /api/v1/health/detailed` - Detailed system health

### Country Configuration
- `GET /api/v1/countries/` - List supported countries
- `GET /api/v1/countries/{country}` - Get country configuration

### Person Management
- `POST /api/v1/{country}/persons/` - Create person
- `GET /api/v1/{country}/persons/search` - Search persons
- `GET /api/v1/{country}/persons/{id}` - Get person details
- `PUT /api/v1/{country}/persons/{id}` - Update person
- `DELETE /api/v1/{country}/persons/{id}` - Soft delete person

### Validation
- `POST /api/v1/{country}/persons/validate` - Validate person data

## Monitoring and Logging

### Health Monitoring

Monitor these endpoints:
- `/health` - Basic health check
- `/api/v1/health/detailed` - Database connectivity
- `/api/v1/health/database/{country}` - Country-specific DB health

### Logging

Structured JSON logs include:
- Transaction IDs for request tracking
- User context and audit trails
- Performance metrics
- Business rule validation results

### File Audit

All file operations are logged to:
- Database audit tables
- Local audit log files
- Performance monitoring metrics

## Security

### Authentication

Currently using JWT tokens. To implement:
1. Create user management endpoints
2. Add authentication middleware
3. Implement role-based access control

### Data Protection

- All sensitive data is encrypted at rest
- Audit logs track all data access
- Country data isolation ensures compliance
- Regular backup verification

## Support

### Common Issues

**Database Connection Errors**
```bash
# Check database connectivity
python -c "from app.core.database import DatabaseManager; print(DatabaseManager.test_connection('ZA'))"
```

**File Storage Issues**
```bash
# Check file storage permissions
ls -la /var/linc-data/
```

### Development Support

- Business Rules: See `Documents/Refactored_Business_Rules_Specification.md`
- Screen Specifications: See `Documents/Refactored_Screen_Field_Specifications.md`
- API Documentation: Visit `/api/v1/docs` when running

## Contributing

1. Follow the coding standards defined in the project
2. Implement business rules with proper validation codes
3. Add comprehensive tests for new features
4. Update documentation for API changes
5. Ensure multi-tenant compatibility

## License

This project is proprietary software for government licensing systems. 