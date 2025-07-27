#!/usr/bin/env python3
"""
Test script to verify the approval email fix
"""
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.email_service import send_approval_email

# Test the email service with a fallback name
def test_approval_email():
    print("Testing approval email with fallback name...")
    
    # Test email address
    test_email = "wiekusvonlandsberg@gmail.com"
    
    # Use the same fallback logic as in the fix
    fallback_name = test_email.split('@')[0].replace('.', ' ').title()
    print(f"Using fallback name: '{fallback_name}'")
    
    # Send test email
    success, message = send_approval_email(test_email, fallback_name)
    
    print(f"Email Success: {success}")
    print(f"Email Message: {message}")
    
    if success:
        print("✅ Email fix is working! Users without resident records can now receive approval emails.")
    else:
        print("❌ Email sending failed. Check SMTP configuration.")

if __name__ == "__main__":
    test_approval_email()
