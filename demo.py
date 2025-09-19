#!/usr/bin/env python3
"""
Demo script to showcase the DealNest Partner Request API functionality.
This script demonstrates the complete workflow of creating users, sending requests, and responding to them.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8004"

def make_request(method, endpoint, data=None):
    """Helper function to make HTTP requests"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"{method.upper()} {endpoint}")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print("-" * 50)
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"❌ Could not connect to {BASE_URL}")
        print("Make sure the API server is running with: poetry run python -m app.main")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def demo_partner_request_workflow():
    """Demonstrate the complete partner request workflow"""
    print("🚀 DealNest Partner Request API Demo")
    print("=" * 50)
    
    # Step 1: Create users
    print("📝 Step 1: Creating users...")
    alice_data = {"email": "alice@example.com", "name": "Alice Johnson"}
    bob_data = {"email": "bob@example.com", "name": "Bob Smith"}
    charlie_data = {"email": "charlie@example.com", "name": "Charlie Brown"}
    
    alice = make_request("POST", "/users/", alice_data)
    if not alice:
        return
    
    bob = make_request("POST", "/users/", bob_data)
    if not bob:
        return
    
    charlie = make_request("POST", "/users/", charlie_data)
    if not charlie:
        return
    
    # Step 2: Send partner requests
    print("📤 Step 2: Sending partner requests...")
    
    # Alice sends request to Bob
    request1_data = {"sender_id": alice["id"], "recipient_id": bob["id"]}
    request1 = make_request("POST", "/partner-requests/", request1_data)
    
    # Charlie sends request to Alice
    request2_data = {"sender_id": charlie["id"], "recipient_id": alice["id"]}
    request2 = make_request("POST", "/partner-requests/", request2_data)
    
    # Step 3: Check received requests
    print("📥 Step 3: Checking received requests...")
    
    # Check Bob's received requests
    bob_requests = make_request("GET", f"/partner-requests/received/{bob['id']}/")
    
    # Check Alice's received requests
    alice_requests = make_request("GET", f"/partner-requests/received/{alice['id']}/")
    
    # Step 4: Respond to requests
    print("✅ Step 4: Responding to requests...")
    
    # Bob accepts Alice's request
    if bob_requests and bob_requests["count"] > 0:
        request_id = bob_requests["pending_requests"][0]["id"]
        response_data = {"request_id": request_id, "action": "accept"}
        make_request("POST", "/partner-requests/respond/", response_data)
    
    # Alice rejects Charlie's request
    if alice_requests and alice_requests["count"] > 0:
        request_id = alice_requests["pending_requests"][0]["id"]
        response_data = {"request_id": request_id, "action": "reject"}
        make_request("POST", "/partner-requests/respond/", response_data)
    
    # Step 5: Check final state
    print("🔍 Step 5: Checking final state...")
    
    # Check Bob's requests again (should be empty now)
    bob_requests_final = make_request("GET", f"/partner-requests/received/{bob['id']}/")
    
    # Check Alice's requests again (should be empty now)
    alice_requests_final = make_request("GET", f"/partner-requests/received/{alice['id']}/")
    
    print("🎉 Demo completed!")
    print("\nSummary:")
    print("- Alice and Bob are now partners (request accepted)")
    print("- Charlie's request to Alice was rejected")
    print("- Check the server logs for email notifications")

def demo_error_cases():
    """Demonstrate error handling"""
    print("\n🚨 Error Cases Demo")
    print("=" * 50)
    
    # Try to create duplicate user
    print("❌ Creating duplicate user...")
    duplicate_data = {"email": "alice@example.com", "name": "Alice Duplicate"}
    make_request("POST", "/users/", duplicate_data)
    
    # Try to send request to non-existent user
    print("❌ Sending request to non-existent user...")
    invalid_request = {"sender_id": 1, "recipient_id": 999}
    make_request("POST", "/partner-requests/", invalid_request)
    
    # Try to send request to self
    print("❌ Sending request to self...")
    self_request = {"sender_id": 1, "recipient_id": 1}
    make_request("POST", "/partner-requests/", self_request)

if __name__ == "__main__":
    print("Make sure the API server is running on http://localhost:8004")
    print("Start it with: poetry run python -m app.main")
    print()
    
    input("Press Enter to start the demo...")
    
    demo_partner_request_workflow()
    demo_error_cases()
    
    print("\n📚 For more information, visit:")
    print("- API Documentation: http://localhost:8004/docs")
    print("- Alternative Docs: http://localhost:8004/redoc")
    print("- Health Check: http://localhost:8004/health")
