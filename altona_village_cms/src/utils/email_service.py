import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'))

def send_approval_email(to_email, first_name):
    """
    Send approval notification email to newly approved user
    Returns: (success: bool, error_message: str)
    """
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        app_url = os.getenv('APP_URL', 'http://localhost:5173')
        
        # Validate email configuration
        if not from_email or not from_password:
            error_msg = "Email configuration missing. Please set FROM_EMAIL and EMAIL_PASSWORD in .env file"
            print(f"[EMAIL ERROR] {error_msg}")
            return False, error_msg
        
        if from_email == 'vonlandsbergjohn@gmail.com' and from_password == 'your-gmail-app-password-here':
            error_msg = "Please update .env file with your actual Gmail App Password"
            print(f"[EMAIL ERROR] {error_msg}")
            return False, error_msg
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Welcome to Altona Village - Account Approved!"
        
        # Email body
        body = f"""
Dear {first_name},

Great news! Your Altona Village community portal account has been approved by the estate management.

You can now log in to access:
• Community announcements and updates
• Submit maintenance requests
• View your account information
• Connect with neighbors

Please log in at: {app_url}/login

Welcome to the Altona Village community!

Best regards,
Altona Village Management Team

---
This is an automated message from the Altona Village Community Management System.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print(f"[EMAIL] Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print(f"[EMAIL] Logging in as {from_email}")
        server.login(from_email, from_password)
        text = msg.as_string()
        print(f"[EMAIL] Sending approval email to {to_email}")
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        success_msg = f"Approval email sent successfully to {to_email}"
        print(f"[EMAIL SUCCESS] {success_msg}")
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Error sending approval email to {to_email}: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False, error_msg

def send_rejection_email(to_email, first_name):
    """
    Send rejection notification email to rejected user
    Returns: (success: bool, error_message: str)
    """
    try:
        # Email configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL', 'your-email@gmail.com')
        from_password = os.getenv('EMAIL_PASSWORD', 'your-app-password')
        
        # For testing purposes, if no email config is set, simulate success
        if from_email == 'your-email@gmail.com':
            print(f"[EMAIL SIMULATION] Rejection email would be sent to {to_email} for {first_name}")
            return True, "Email simulation successful"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = "Altona Village Registration - Application Status"
        
        # Email body
        body = f"""
        Dear {first_name},
        
        Thank you for your interest in joining the Altona Village community portal.
        
        After reviewing your application, we regret to inform you that your registration has not been approved at this time.
        
        If you believe this is an error or would like to discuss your application further, please contact the estate management office directly.
        
        Thank you for your understanding.
        
        Best regards,
        Altona Village Management Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        return True, "Email sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending rejection email: {str(e)}"
        print(error_msg)
        return False, error_msg

def send_registration_notification_to_admin(user_email, first_name, last_name):
    """
    Send notification to admin when new user registers
    """
    try:
        # Email configuration
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL', 'your-email@gmail.com')
        from_password = os.getenv('EMAIL_PASSWORD', 'your-app-password')
        admin_email = os.getenv('ADMIN_EMAIL', 'vonlandsbergjohn@gmail.com')
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = admin_email
        msg['Subject'] = "New Registration - Altona Village Portal"
        
        # Email body
        body = f"""
        Dear Admin,
        
        A new user has registered for the Altona Village community portal and is awaiting approval.
        
        User Details:
        - Name: {first_name} {last_name}
        - Email: {user_email}
        
        Please log in to the admin dashboard to review and approve this registration.
        
        Login at: http://localhost:5173/login
        
        Best regards,
        Altona Village Portal System
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, admin_email, text)
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Error sending admin notification email: {str(e)}")
        return False
