import requests
import json
import random
import time

BASE_URL = "http://127.0.0.1:5001"

def test_full_flow():
    email = f"flow_{random.randint(10000,99999)}@example.com"
    password = "password123"
    print(f"Testing Full Flow for {email}...")
    
    # 1. Signup
    print("[1] Requesting Signup...")
    res = requests.post(f"{BASE_URL}/signup", json={
        "email": email, "password": password, "first_name": "Flow", "last_name": "Test"
    })
    
    if res.status_code != 201:
        print(f"Signup Failed: {res.status_code} {res.text}")
        return

    print("Signup Success. Waiting for OTP file...")
    time.sleep(1) 
    
    # 2. Get OTP
    try:
        with open("backend/backend_otp.txt", "r") as f:
            otp = f.read().strip()
        print(f"[2] Retrieved OTP: {otp}")
    except Exception as e:
        print(f"Failed to read OTP: {e}")
        return

    # 3. Verify Email
    print("[3] Verifying Email...")
    res = requests.post(f"{BASE_URL}/verify-email", json={"email": email, "otp": otp})
    
    if res.status_code == 200:
        print("Email Verified Successfully!")
        print(res.json())
    else:
        print(f"Verification Failed: {res.status_code} {res.text}")
        return

    # 4. Login (Should trigger 2FA OTP)
    print("[4] Logging in...")
    res = requests.post(f"{BASE_URL}/login", json={"email": email, "password": password})
    
    if res.status_code == 200 and res.json().get("otp_required"):
         print("Login Success. OTP Required triggered.")
    else:
         print(f"Login Check Failed: {res.status_code} {res.text}")

if __name__ == "__main__":
    test_full_flow()
