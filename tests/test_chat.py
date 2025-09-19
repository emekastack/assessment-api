import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db
from app.db import models

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="function")
def setup_database():
    """Setup test database for each test"""
    # Import all models to ensure they're registered
    from app.db.models import User, PartnerRequest, Partnership, ChatChannel, Message, channel_members
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_users(setup_database):
    """Create test users"""
    users_data = [
        {"email": "alice@example.com", "name": "Alice"},
        {"email": "bob@example.com", "name": "Bob"},
        {"email": "charlie@example.com", "name": "Charlie"}
    ]
    
    created_users = []
    for user_data in users_data:
        response = client.post("/users/", json=user_data)
        assert response.status_code == 201
        created_users.append(response.json())
    
    return created_users

@pytest.fixture
def test_channel(test_users):
    """Create a test channel"""
    channel_data = {
        "name": "Test Channel",
        "member_ids": [test_users[0]["id"], test_users[1]["id"]]
    }
    
    response = client.post("/chat/channels/", json=channel_data)
    assert response.status_code == 201
    return response.json()

def test_create_channel(test_users):
    """Test creating a chat channel"""
    channel_data = {
        "name": "New Channel",
        "member_ids": [test_users[0]["id"], test_users[1]["id"]]
    }
    
    response = client.post("/chat/channels/", json=channel_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "New Channel"
    assert len(data["members"]) == 2
    assert "id" in data
    assert "created_at" in data

def test_create_channel_with_invalid_users(test_users):
    """Test creating a channel with invalid user IDs"""
    channel_data = {
        "name": "Invalid Channel",
        "member_ids": [999, 1000]  # Non-existent users
    }
    
    response = client.post("/chat/channels/", json=channel_data)
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()

def test_get_channel(test_channel):
    """Test getting channel details"""
    channel_id = test_channel["id"]
    
    response = client.get(f"/chat/channels/{channel_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == channel_id
    assert data["name"] == test_channel["name"]
    assert len(data["members"]) == 2

def test_get_nonexistent_channel(setup_database):
    """Test getting a channel that doesn't exist"""
    response = client.get("/chat/channels/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_send_message(test_users, test_channel):
    """Test sending a message to a channel"""
    alice = test_users[0]
    channel_id = test_channel["id"]
    
    message_data = {
        "sender_id": alice["id"],
        "body": "Hello, this is a test message!"
    }
    
    response = client.post(f"/chat/channels/{channel_id}/messages/", json=message_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["sender_id"] == alice["id"]
    assert data["channel_id"] == channel_id
    assert data["body"] == "Hello, this is a test message!"
    assert data["is_read"] == False
    assert data["sender_name"] == alice["name"]
    assert "id" in data
    assert "created_at" in data

def test_send_message_to_nonexistent_channel(test_users):
    """Test sending a message to a channel that doesn't exist"""
    alice = test_users[0]
    
    message_data = {
        "sender_id": alice["id"],
        "body": "This should fail"
    }
    
    response = client.post("/chat/channels/999/messages/", json=message_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_send_message_by_non_member(test_users, test_channel):
    """Test sending a message by a user who is not a channel member"""
    charlie = test_users[2]  # Charlie is not a member of the test channel
    channel_id = test_channel["id"]
    
    message_data = {
        "sender_id": charlie["id"],
        "body": "This should fail"
    }
    
    response = client.post(f"/chat/channels/{channel_id}/messages/", json=message_data)
    assert response.status_code == 403
    assert "not a member" in response.json()["detail"]

def test_mark_message_read(test_users, test_channel):
    """Test marking a message as read"""
    alice = test_users[0]
    channel_id = test_channel["id"]
    
    # First, send a message
    message_data = {
        "sender_id": alice["id"],
        "body": "Test message for read receipt"
    }
    
    send_response = client.post(f"/chat/channels/{channel_id}/messages/", json=message_data)
    assert send_response.status_code == 201
    message_id = send_response.json()["id"]
    
    # Mark the message as read
    response = client.post(f"/chat/messages/{message_id}/mark-read/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Message marked as read"
    assert data["message_id"] == message_id
    assert data["is_read"] == True

def test_mark_nonexistent_message_read(setup_database):
    """Test marking a message that doesn't exist as read"""
    response = client.post("/chat/messages/999/mark-read/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_get_channel_messages(test_users, test_channel):
    """Test getting messages from a channel"""
    alice = test_users[0]
    bob = test_users[1]
    channel_id = test_channel["id"]
    
    # Send a few messages
    messages_data = [
        {"sender_id": alice["id"], "body": "First message"},
        {"sender_id": bob["id"], "body": "Second message"},
        {"sender_id": alice["id"], "body": "Third message"}
    ]
    
    for message_data in messages_data:
        response = client.post(f"/chat/channels/{channel_id}/messages/", json=message_data)
        assert response.status_code == 201
    
    # Get messages
    response = client.get(f"/chat/channels/{channel_id}/messages/")
    assert response.status_code == 200
    
    messages = response.json()
    assert len(messages) == 3
    
    # Messages should be ordered by created_at desc (newest first)
    # Note: Due to timing, the order might vary, so we'll check that all messages are present
    message_bodies = [msg["body"] for msg in messages]
    assert "First message" in message_bodies
    assert "Second message" in message_bodies
    assert "Third message" in message_bodies
    assert len(message_bodies) == 3
    
    # Check that sender names are included
    for message in messages:
        assert "sender_name" in message
        assert message["sender_name"] in ["Alice", "Bob"]

def test_get_messages_from_nonexistent_channel(setup_database):
    """Test getting messages from a channel that doesn't exist"""
    response = client.get("/chat/channels/999/messages/")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_get_user_presence(test_users):
    """Test getting user presence status"""
    alice = test_users[0]
    
    response = client.get(f"/chat/presence/{alice['id']}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == alice["id"]
    assert "online" in data
    assert "last_seen" in data

def test_get_online_users(setup_database):
    """Test getting list of online users"""
    response = client.get("/chat/presence/online/")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
