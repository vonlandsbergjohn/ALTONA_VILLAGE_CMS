#!/usr/bin/env python3
"""
Quick test to check what user profile data looks like
"""
import requests
import json

# Test the profile API to see what data structure we get
def test_profile_api():
    try:
        # You'll need to get a valid token first
        print("To test the profile API:")
        print("1. Log into the app")
        print("2. Open browser developer tools")
        print("3. Check localStorage for 'token'")
        print("4. Run this command with the token:")
        print()
        print("curl -H 'Authorization: Bearer YOUR_TOKEN_HERE' http://localhost:5000/api/auth/profile")
        print()
        print("This will show the exact structure being returned by the profile API")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_profile_api()
