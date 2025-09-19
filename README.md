# DealNest Partner Request & Chat API

A comprehensive FastAPI application that implements partner request workflow and real-time chat functionality for DealNest. Users can send partner requests to connect with other users, engage in real-time chat with presence tracking, and receive read receipts.

## Features

### Partner Request System
- **User Management**: Create and manage users with email and name
- **Partner Requests**: Send, receive, and respond to partner requests
- **Partnership Creation**: Automatic partnership creation when requests are accepted
- **Email Notifications**: Mock email notifications for request events

### Real-Time Chat System
- **Chat Channels**: Create channels with multiple users
- **Real-Time Messaging**: WebSocket-based instant messaging
- **Presence Tracking**: See who's online/offline with last seen timestamps
- **Read Receipts**: Know when messages have been read
- **WebSocket Events**: Real-time presence changes and message notifications

### Technical Features
- **SQLite Database**: Simple SQLite database for data persistence
- **Redis Support**: Optional Redis for presence storage (falls back to in-memory)
- **Comprehensive Testing**: 24 tests covering all functionality
- **Auto Documentation**: Interactive API docs at `/docs`

## Requirements

- Python 3.9+
- Poetry (for dependency management)

## Installation

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/emekastack/assessment-api
   cd assessment-api
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

### Chat System

- `POST /chat/channels/` - Create a new chat channel
- `GET /chat/channels/{channel_id}` - Get channel details
- `POST /chat/channels/{channel_id}/messages/` - Send a message to a channel
- `GET /chat/channels/{channel_id}/messages/` - Get messages from a channel
- `POST /chat/messages/{message_id}/mark-read/` - Mark a message as read
- `GET /chat/presence/{user_id}` - Get user presence status
- `GET /chat/presence/online/` - Get list of online users
- `WebSocket /chat/ws/{user_id}` - Real-time WebSocket connection

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

### 5. Chat System

```bash
# Create a chat channel
curl -X POST "http://localhost:8004/chat/channels/" \
     -H "Content-Type: application/json" \
     -d '{"name": "General Chat", "member_ids": [1, 2]}'

# Send a message
curl -X POST "http://localhost:8004/chat/channels/1/messages/" \
     -H "Content-Type: application/json" \
     -d '{"sender_id": 1, "body": "Hello everyone!"}'

# Mark message as read
curl -X POST "http://localhost:8004/chat/messages/1/mark-read/"

# Check user presence
curl -X GET "http://localhost:8004/chat/presence/1/"
```

## Database

The application uses SQLite with the following tables:

### Core Tables
- **users**: User information (id, email, name, created_at)
- **partner_requests**: Partner requests (id, sender_id, recipient_id, status, created_at)
- **partnerships**: Created partnerships (id, user_a_id, user_b_id, created_at)

### Chat Tables
- **chat_channels**: Chat channels (id, name, created_at)
- **channel_members**: Many-to-many relationship between channels and users
- **messages**: Chat messages (id, sender_id, channel_id, body, is_read, created_at)

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

## Frontend Demo

A complete HTML/JavaScript demo is included to showcase the real-time chat functionality:

1. **Start the API server**:
   ```bash
   poetry run python -m app.main
   ```

2. **Open the demo**: Open `static/chat_demo.html` in your browser

3. **Features demonstrated**:
   - Connect as different users via WebSocket
   - Create and join chat channels
   - Send real-time messages
   - See presence status (online/offline)
   - Receive read receipts
   - View event logs for debugging

The demo includes a modern UI with connection status, message history, presence indicators, and real-time event logging.

## Testing

Run the test suite:

```bash
poetry run pytest tests/ -v
```

The tests cover:
- User creation and retrieval
- Partner request creation and validation
- Request acceptance and rejection
- Chat channel creation and management
- Real-time messaging functionality
- Presence tracking
- Read receipts
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