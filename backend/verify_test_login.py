import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_login_flow():
    print("Testing Login Flow...")
    
    # 1. Login to get OTP
    login_payload = {
        "email": "testuser@geoscope.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_payload)
        print(f"Login Response: {response.status_code}")
        print(response.json())
        
        if response.status_code != 200:
            print("Login failed")
            return

        json_resp = response.json()
        if not json_resp.get("otp_required"):
             print("OTP requirement missing in response")
             return

        print("Login successful, OTP required.")

        # 2. Verify OTP
        # Since we deleted backend_otp.txt, we might not have the OTP.
        # However, for now, reverting to previous state or a placeholder.
        # If the user implies seed_test_user handles it, maybe we don't need to verify OTP?
        # But the response says OTP required.
        # Let's keep the payload structure but maybe just log that we can't verify automatically without the file/hardcode?
        # Or maybe the "logic in seed_test_user.py" implies we don't NEED OTP? 
        # But the backend says we do.
        # I'll just put a placeholder or comment.
        verify_payload = {
            "email": "testuser@geoscope.com",
            "otp": "123456" 
        }

        response = requests.post(f"{BASE_URL}/verify-login-otp", json=verify_payload)
        print(f"Verify OTP Response: {response.status_code}")
        print(response.json())

        if response.status_code == 200 and "access_token" in response.json():
            print("OTP Verification Successful! Access Token Received.")
        else:
             print("OTP Verification Failed.")

    except Exception as e:
        print(f"Error during request: {e}")

if __name__ == "__main__":
    # Wait for server to start if running immediately after start command
    time.sleep(2) 
    test_login_flow()
