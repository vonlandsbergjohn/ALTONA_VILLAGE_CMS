import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_approval_email(to_email, first_name):
    """
    Send approval notification email to newly approved user
    """
    try:
        # Email configuration - you'll need to set these environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL', 'your-email@gmail.com')
        from_password = os.getenv('EMAIL_PASSWORD', 'your-app-password')
        
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
        - Community announcements and updates
        - Submit maintenance requests
        - View your account information
        - Connect with neighbors
        
        Please log in at: http://localhost:5173/login
        
        Welcome to the Altona Village community!
        
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
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

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
