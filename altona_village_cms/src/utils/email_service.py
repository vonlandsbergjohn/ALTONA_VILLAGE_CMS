import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
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
        
        # Send email with enhanced authentication
        print(f"[EMAIL] Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print(f"[EMAIL] Logging in as {from_email}")
        
        # Try different authentication methods
        try:
            server.login(from_email, from_password)
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"[EMAIL ERROR] Authentication failed: {auth_error}")
            # Try with explicit AUTH LOGIN
            server.ehlo()
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
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        
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
        print(f"[EMAIL] Sending rejection email to {to_email}")
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        success_msg = f"Rejection email sent successfully to {to_email}"
        print(f"[EMAIL SUCCESS] {success_msg}")
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Error sending rejection email to {to_email}: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False, error_msg

def send_registration_notification_to_admin(user_email, first_name, last_name):
    """
    Send notification to admin when new user registers
    """
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        admin_email = os.getenv('ADMIN_EMAIL', 'vonlandsbergjohn@gmail.com')
        app_url = os.getenv('APP_URL', 'http://localhost:5173')
        
        # Validate email configuration
        if not from_email or not from_password:
            error_msg = "Email configuration missing. Please set FROM_EMAIL and EMAIL_PASSWORD in .env file"
            print(f"[EMAIL ERROR] {error_msg}")
            return False
        
        if from_email == 'vonlandsbergjohn@gmail.com' and from_password == 'your-gmail-app-password-here':
            error_msg = "Please update .env file with your actual Gmail App Password"
            print(f"[EMAIL ERROR] {error_msg}")
            return False
        
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
• Name: {first_name} {last_name}
• Email: {user_email}
• Registration Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please log in to the admin dashboard to review and approve this registration.

Admin Login: {app_url}/login

Best regards,
Altona Village Portal System

---
This is an automated notification from the Altona Village Community Management System.
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        print(f"[EMAIL] Sending admin notification about new registration: {user_email}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        text = msg.as_string()
        server.sendmail(from_email, admin_email, text)
        server.quit()
        
        print(f"[EMAIL SUCCESS] Admin notification sent for new registration: {user_email}")
        return True
        
    except Exception as e:
        error_msg = f"Error sending admin notification email: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False

def send_transition_request_notification(to_email, user_name, erf_number, request_type):
    """
    Send notification when a new transition request is submitted
    Returns: (success: bool, error_message: str)
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        app_url = os.getenv('APP_URL', 'http://localhost:5173')
        
        if not from_email or not from_password:
            return False, "Email configuration missing"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Transition Request Submitted - ERF {erf_number}'
        
        # Create HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Transition Request Submitted</h2>
                
                <p>Dear {user_name},</p>
                
                <p>Your transition request has been successfully submitted and is now being reviewed by our admin team.</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Request Details:</h3>
                    <ul style="margin: 0;">
                        <li><strong>Property:</strong> ERF {erf_number}</li>
                        <li><strong>Transition Type:</strong> {request_type.replace('_', ' ').title()}</li>
                        <li><strong>Status:</strong> Pending Review</li>
                        <li><strong>Submitted:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</li>
                    </ul>
                </div>
                
                <p>You can track the progress of your request by visiting:</p>
                <p><a href="{app_url}/resident/transition-requests" style="color: #2563eb; text-decoration: none;">{app_url}/resident/transition-requests</a></p>
                
                <p>Our admin team will review your request and provide updates as the transition process progresses.</p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="font-size: 12px; color: #6b7280;">
                    This is an automated email from Altona Village CMS. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL SUCCESS] Transition request notification sent to {to_email}")
        return True, "Email sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending transition request notification: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False, error_msg

def send_transition_status_update(to_email, user_name, erf_number, old_status, new_status, admin_note=None):
    """
    Send notification when transition request status changes
    Returns: (success: bool, error_message: str)
    """
    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        app_url = os.getenv('APP_URL', 'http://localhost:5173')
        
        if not from_email or not from_password:
            return False, "Email configuration missing"
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = f'Transition Update - ERF {erf_number} Status Changed'
        
        # Create HTML body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb;">Transition Request Update</h2>
                
                <p>Dear {user_name},</p>
                
                <p>There's an update on your property transition request for ERF {erf_number}.</p>
                
                <div style="background-color: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Status Change:</h3>
                    <p style="margin: 10px 0;">
                        <span style="color: #ef4444; text-decoration: line-through;">{old_status.replace('_', ' ').title()}</span>
                        <span style="margin: 0 10px;">→</span>
                        <span style="color: #10b981; font-weight: bold;">{new_status.replace('_', ' ').title()}</span>
                    </p>
                    <p style="margin: 5px 0;"><strong>Updated:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                
                {f'<div style="background-color: #fef3c7; padding: 15px; border-radius: 8px; margin: 20px 0;"><h4 style="margin-top: 0;">Admin Note:</h4><p style="margin-bottom: 0;">{admin_note}</p></div>' if admin_note else ''}
                
                <p>You can view full details and add comments by visiting:</p>
                <p><a href="{app_url}/resident/transition-requests" style="color: #2563eb; text-decoration: none;">{app_url}/resident/transition-requests</a></p>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="font-size: 12px; color: #6b7280;">
                    This is an automated email from Altona Village CMS. Please do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, from_password)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL SUCCESS] Transition status update sent to {to_email}")
        return True, "Email sent successfully"
        
    except Exception as e:
        error_msg = f"Error sending transition status update: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False, error_msg


def send_custom_email(to_email, subject, message, recipient_name=None):
    """
    Send a custom email using the same configuration as registration emails
    Returns: (success: bool, error_message: str)
    """
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        
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
        msg['Subject'] = subject
        
        # Add reply-to for community communications
        msg['Reply-To'] = "altonavillagehoa@gmail.com, lynette@sir-worcester.co.za"
        
        # Create email body with community branding
        greeting = f"Dear {recipient_name}," if recipient_name else "Dear Resident,"
        
        body = f"""
{greeting}

{message}

Best regards,
Altona Village Management Team

---
This is a message from the Altona Village Community Management System.
For any questions or concerns, please contact us at altonavillagehoa@gmail.com
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email using the same method as registration emails
        print(f"[EMAIL] Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print(f"[EMAIL] Logging in as {from_email}")
        
        # Try different authentication methods like in approval email
        try:
            server.login(from_email, from_password)
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"[EMAIL ERROR] Authentication failed: {auth_error}")
            # Try with explicit AUTH LOGIN
            server.ehlo()
            server.login(from_email, from_password)
        
        text = msg.as_string()
        print(f"[EMAIL] Sending custom email to {to_email}")
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        success_msg = f"Custom email sent successfully to {to_email}"
        print(f"[EMAIL SUCCESS] {success_msg}")
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Error sending custom email to {to_email}: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False, error_msg


def send_email_with_attachment(to_email, subject, message, attachment_path=None, recipient_name=None):
    """
    Send an email with optional PDF attachment
    Returns: (success: bool, error_message: str)
    """
    try:
        # Email configuration from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        from_email = os.getenv('FROM_EMAIL')
        from_password = os.getenv('EMAIL_PASSWORD')
        
        # Validate email configuration
        if not from_email or not from_password:
            error_msg = "Email configuration missing. Please set FROM_EMAIL and EMAIL_PASSWORD in .env file"
            print(f"[EMAIL ERROR] {error_msg}")
            return False, error_msg
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg['Reply-To'] = "altonavillagehoa@gmail.com, lynette@sir-worcester.co.za"
        
        # Create email body
        greeting = f"Dear {recipient_name}," if recipient_name else "Dear Resident,"
        
        body = f"""
{greeting}

{message}

Best regards,
Altona Village Management Team

---
This is a message from the Altona Village Community Management System.
For any questions or concerns, please contact us at altonavillagehoa@gmail.com
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            try:
                print(f"[EMAIL] Adding attachment: {attachment_path}")
                with open(attachment_path, "rb") as attachment:
                    # Create MIMEBase object
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                # Encode file
                encoders.encode_base64(part)
                
                # Add header with filename
                filename = os.path.basename(attachment_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                
                # Attach the part to message
                msg.attach(part)
                print(f"[EMAIL] Attachment added successfully: {filename}")
                
            except Exception as attachment_error:
                print(f"[EMAIL WARNING] Failed to attach file: {attachment_error}")
                # Continue without attachment rather than failing completely
        elif attachment_path:
            print(f"[EMAIL WARNING] Attachment file not found: {attachment_path}")
        
        # Send email
        print(f"[EMAIL] Connecting to {smtp_server}:{smtp_port}")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        print(f"[EMAIL] Logging in as {from_email}")
        
        try:
            server.login(from_email, from_password)
        except smtplib.SMTPAuthenticationError as auth_error:
            print(f"[EMAIL ERROR] Authentication failed: {auth_error}")
            server.ehlo()
            server.login(from_email, from_password)
        
        text = msg.as_string()
        print(f"[EMAIL] Sending email with {'attachment' if attachment_path else 'no attachment'} to {to_email}")
        server.sendmail(from_email, to_email, text)
        server.quit()
        
        success_msg = f"Email sent successfully to {to_email}"
        if attachment_path and os.path.exists(attachment_path):
            success_msg += f" with attachment: {os.path.basename(attachment_path)}"
        print(f"[EMAIL SUCCESS] {success_msg}")
        return True, success_msg
        
    except Exception as e:
        error_msg = f"Error sending email with attachment to {to_email}: {str(e)}"
        print(f"[EMAIL ERROR] {error_msg}")
        return False, error_msg
