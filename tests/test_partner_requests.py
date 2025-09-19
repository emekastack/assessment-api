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

def test_create_partner_request(test_users):
    """Test creating a partner request"""
    alice = test_users[0]
    bob = test_users[1]
    
    request_data = {
        "sender_id": alice["id"],
        "recipient_id": bob["id"]
    }
    
    response = client.post("/partner-requests/", json=request_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["message"] == "Partner request created successfully"
    assert data["status"] == "pending"
    assert "request_id" in data

def test_get_received_requests(test_users):
    """Test getting received partner requests"""
    alice = test_users[0]
    bob = test_users[1]
    
    # Create a request from Alice to Bob
    request_data = {
        "sender_id": alice["id"],
        "recipient_id": bob["id"]
    }
    client.post("/partner-requests/", json=request_data)
    
    # Get Bob's received requests
    response = client.get(f"/partner-requests/received/{bob['id']}/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == bob["id"]
    assert data["count"] == 1
    assert len(data["pending_requests"]) == 1
    assert data["pending_requests"][0]["sender_name"] == "Alice"

def test_accept_partner_request(test_users):
    """Test accepting a partner request"""
    alice = test_users[0]
    bob = test_users[1]
    
    # Create a request from Alice to Bob
    request_data = {
        "sender_id": alice["id"],
        "recipient_id": bob["id"]
    }
    create_response = client.post("/partner-requests/", json=request_data)
    request_id = create_response.json()["request_id"]
    
    # Bob accepts the request
    response_data = {
        "request_id": request_id,
        "action": "accept"
    }
    
    response = client.post("/partner-requests/respond/", json=response_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Partner request accepted and partnership created"
    assert data["status"] == "accepted"
    assert data["action"] == "accept"

def test_reject_partner_request(test_users):
    """Test rejecting a partner request"""
    alice = test_users[0]
    bob = test_users[1]
    
    # Create a request from Alice to Bob
    request_data = {
        "sender_id": alice["id"],
        "recipient_id": bob["id"]
    }
    create_response = client.post("/partner-requests/", json=request_data)
    request_id = create_response.json()["request_id"]
    
    # Bob rejects the request
    response_data = {
        "request_id": request_id,
        "action": "reject"
    }
    
    response = client.post("/partner-requests/respond/", json=response_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Partner request rejected"
    assert data["status"] == "rejected"
    assert data["action"] == "reject"

def test_duplicate_partner_request(test_users):
    """Test that duplicate partner requests are not allowed"""
    alice = test_users[0]
    bob = test_users[1]
    
    request_data = {
        "sender_id": alice["id"],
        "recipient_id": bob["id"]
    }
    
    # Create first request
    response1 = client.post("/partner-requests/", json=request_data)
    assert response1.status_code == 201
    
    # Try to create duplicate request
    response2 = client.post("/partner-requests/", json=request_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]

def test_self_partner_request(test_users):
    """Test that users cannot send partner requests to themselves"""
    alice = test_users[0]
    
    request_data = {
        "sender_id": alice["id"],
        "recipient_id": alice["id"]
    }
    
    response = client.post("/partner-requests/", json=request_data)
    assert response.status_code == 400
    assert "yourself" in response.json()["detail"]
