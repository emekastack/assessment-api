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

def test_create_user(setup_database):
    """Test creating a user"""
    user_data = {
        "email": "test@example.com",
        "name": "Test User"
    }
    
    response = client.post("/users/", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"
    assert "id" in data
    assert "created_at" in data

def test_create_duplicate_user(setup_database):
    """Test that duplicate emails are not allowed"""
    user_data = {
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Create first user
    response1 = client.post("/users/", json=user_data)
    assert response1.status_code == 201
    
    # Try to create user with same email
    response2 = client.post("/users/", json=user_data)
    assert response2.status_code == 400
    assert "already exists" in response2.json()["detail"]

def test_get_users(setup_database):
    """Test getting all users"""
    # Create some test users
    users_data = [
        {"email": "alice@example.com", "name": "Alice"},
        {"email": "bob@example.com", "name": "Bob"}
    ]
    
    for user_data in users_data:
        client.post("/users/", json=user_data)
    
    # Get all users
    response = client.get("/users/")
    assert response.status_code == 200
    
    data = response.json()
    assert len(data) == 2
    assert data[0]["name"] in ["Alice", "Bob"]
    assert data[1]["name"] in ["Alice", "Bob"]

def test_get_user_by_id(setup_database):
    """Test getting a specific user by ID"""
    user_data = {
        "email": "test@example.com",
        "name": "Test User"
    }
    
    # Create user
    create_response = client.post("/users/", json=user_data)
    user_id = create_response.json()["id"]
    
    # Get user by ID
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"

def test_get_nonexistent_user(setup_database):
    """Test getting a user that doesn't exist"""
    response = client.get("/users/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]
