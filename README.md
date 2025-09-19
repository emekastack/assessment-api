# DealNest Partner Request API

A minimal FastAPI application that implements a partner request workflow system for DealNest. Users can send partner requests to connect with other users, and recipients can accept or reject these requests.

## Features

- **User Management**: Create and manage users with email and name
- **Partner Requests**: Send, receive, and respond to partner requests
- **Partnership Creation**: Automatic partnership creation when requests are accepted
- **Email Notifications**: Mock email notifications for request events
- **SQLite Database**: Simple SQLite database for data persistence

## Requirements

- Python 3.9+
- Poetry (for dependency management)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd dealnest-api
   ```

2. **Install dependencies using Poetry**:
   ```bash
   poetry install
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env file with your specific configuration if needed
   ```

4. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

## Running the Application

1. **Start the development server**:
   ```bash
   poetry run python -m app.main
   ```
   
   Or alternatively:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8004
   ```

2. **Access the API**:
   - API Base URL: `http://localhost:8004`
   - Interactive API Documentation: `http://localhost:8004/docs`
   - Alternative API Documentation: `http://localhost:8004/redoc`

## API Endpoints

### Users

- `POST /users/` - Create a new user
- `GET /users/` - Get all users
- `GET /users/{user_id}` - Get a specific user by ID

### Partner Requests

- `POST /partner-requests/` - Create a new partner request
- `GET /partner-requests/received/{user_id}/` - Get pending requests received by a user
- `POST /partner-requests/respond/` - Respond to a partner request (accept/reject)

## Usage Examples

### 1. Create Users

```bash
# Create Alice
curl -X POST "http://localhost:8004/users/" \
     -H "Content-Type: application/json" \
     -d '{"email": "alice@example.com", "name": "Alice"}'

# Create Bob
curl -X POST "http://localhost:8004/users/" \
     -H "Content-Type: application/json" \
     -d '{"email": "bob@example.com", "name": "Bob"}'
```

### 2. Send Partner Request

```bash
curl -X POST "http://localhost:8004/partner-requests/" \
     -H "Content-Type: application/json" \
     -d '{"sender_id": 1, "recipient_id": 2}'
```

### 3. Check Received Requests

```bash
curl -X GET "http://localhost:8004/partner-requests/received/2/"
```

### 4. Respond to Request

```bash
# Accept the request
curl -X POST "http://localhost:8004/partner-requests/respond/" \
     -H "Content-Type: application/json" \
     -d '{"request_id": 1, "action": "accept"}'

# Or reject the request
curl -X POST "http://localhost:8004/partner-requests/respond/" \
     -H "Content-Type: application/json" \
     -d '{"request_id": 1, "action": "reject"}'
```

## Database

The application uses SQLite with the following tables:

- **users**: User information (id, email, name, created_at)
- **partner_requests**: Partner requests (id, sender_id, recipient_id, status, created_at)
- **partnerships**: Created partnerships (id, user_a_id, user_b_id, created_at)

The database file (`dealnest.db`) is created automatically when the application starts.

## Environment Configuration

The application uses environment variables for configuration. A `.env.example` file is provided as a template:

```bash
# Application Settings
APP_ENV=development
APP_PORT=8004
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=sqlite:///./dealnest.db

# Email Configuration (for future production use)
EMAIL_SERVICE_URL=
EMAIL_API_KEY=
EMAIL_FROM_ADDRESS=noreply@dealnest.com

# Redis Configuration (for future caching)
REDIS_URL=redis://localhost:6379

# Security (for future authentication)
SECRET_KEY=your-secret-key-here-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

Copy `.env.example` to `.env` and modify the values as needed for your environment.

## Testing

Run the test suite:

```bash
poetry run pytest tests/ -v
```

The tests cover:
- User creation and retrieval
- Partner request creation and validation
- Request acceptance and rejection
- Error handling for duplicate requests and invalid actions

## Email Notifications

The application includes a mock email notification system that logs notifications to the console. When:

- A partner request is created: Recipient receives notification
- A partner request is accepted: Sender receives notification

Example notification log:
```
📧 EMAIL NOTIFICATION: To: Bob
📧 EMAIL NOTIFICATION: Subject: New Partner Request
📧 EMAIL NOTIFICATION: Body: You have a new partner request from Alice.
📧 EMAIL NOTIFICATION: Timestamp: 2024-01-15 10:30:00
📧 EMAIL NOTIFICATION: Status: Sent (mocked)
```

## Project Structure

```
dealnest-api/
├── app/
│   ├── api/
│   │   ├── schemas.py          # Pydantic models for API validation
│   │   ├── users.py            # User endpoints
│   │   └── partner_requests.py # Partner request endpoints
│   ├── core/
│   │   ├── config.py           # Application configuration
│   │   └── logging.py          # Logging configuration
│   ├── db/
│   │   ├── database.py         # Database configuration
│   │   └── models.py           # SQLAlchemy models
│   ├── services/
│   │   └── notification_service.py # Email notification service
│   └── main.py                 # FastAPI application entry point
├── tests/
│   ├── test_users.py           # User endpoint tests
│   └── test_partner_requests.py # Partner request tests
├── pyproject.toml              # Poetry dependencies
└── README.md                   # This file
```

## Design Decisions

### Models and Relationships
- **User Model**: Simple stub with id, email, name, and created_at timestamp
- **PartnerRequest Model**: Links sender and recipient with status tracking
- **Partnership Model**: Created when requests are accepted, represents the partnership relationship

### Status Transitions
- Partner requests start as "pending"
- Can transition to "accepted" or "rejected"
- Once responded to, status cannot be changed again

### Notifications
- Mock email service logs notifications to console
- Notifications sent for request creation and acceptance
- Easy to replace with real email service in production

### Error Handling
- Comprehensive validation for all endpoints
- Prevents duplicate requests between same users
- Prevents self-requests
- Validates user existence before operations

## Scaling Considerations

For handling thousands of requests per second, consider:

1. **Database Optimization**:
   - Use PostgreSQL or MySQL instead of SQLite
   - Add database indexes on frequently queried fields
   - Implement connection pooling

2. **Caching**:
   - Cache user data and request statuses
   - Use Redis for session management

3. **Background Processing**:
   - Move email notifications to background queues (Celery/RQ)
   - Use message brokers for async processing

4. **API Optimization**:
   - Implement pagination for large result sets
   - Add rate limiting
   - Use async/await throughout the application

5. **Monitoring**:
   - Add application metrics and monitoring
   - Implement health checks and alerting
   - Use structured logging

## Health Check

The application includes a health check endpoint:

```bash
curl -X GET "http://localhost:8004/health"
```

This returns `{"status": "ok"}` when the application is running properly.