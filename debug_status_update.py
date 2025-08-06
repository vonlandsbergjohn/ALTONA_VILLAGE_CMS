import requests
import json

# Test the status update endpoint directly
def test_status_update():
    # You'll need to replace these with actual values
    base_url = "http://127.0.0.1:5000"
    
    # Get a token first (you'll need admin credentials)
    login_data = {
        "email": "admin@altonavillage.co.za",  # Replace with actual admin email
        "password": "your_admin_password"      # Replace with actual admin password
    }
    
    try:
        # Login to get token
        login_response = requests.post(f"{base_url}/api/auth/login", json=login_data)
        if login_response.status_code != 200:
            print(f"Login failed: {login_response.text}")
            return
            
        token = login_response.json().get('token')
        print(f"Got token: {token[:20]}...")
        
        # Get transition requests to find one to test with
        headers = {"Authorization": f"Bearer {token}"}
        requests_response = requests.get(f"{base_url}/api/transition/admin/requests", headers=headers)
        
        if requests_response.status_code != 200:
            print(f"Failed to get requests: {requests_response.text}")
            return
            
        requests_data = requests_response.json()
        if not requests_data.get('requests'):
            print("No transition requests found")
            return
            
        # Get the first request
        first_request = requests_data['requests'][0]
        request_id = first_request['id']
        print(f"Testing with request ID: {request_id}")
        print(f"Current status: {first_request.get('status')}")
        
        # Try to update status to completed
        update_data = {
            "status": "completed",
            "admin_notes": "Test status update"
        }
        
        update_response = requests.put(
            f"{base_url}/api/transition/admin/request/{request_id}/status",
            headers=headers,
            json=update_data
        )
        
        print(f"Status update response: {update_response.status_code}")
        print(f"Response body: {update_response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_status_update()
