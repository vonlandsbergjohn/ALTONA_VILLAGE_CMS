from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Resident, db
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

communication_bp = Blueprint('communication', __name__)

def admin_required():
    """Decorator to check if user is admin"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return jsonify({'error': 'Admin access required'}), 403
    return None

@communication_bp.route('/send-email', methods=['POST'])
@jwt_required()
def send_bulk_email():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        data = request.get_json()
        subject = data.get('subject')
        message = data.get('message')
        recipient_type = data.get('recipient_type', 'all')  # 'all', 'owners', 'tenants'
        
        if not subject or not message:
            return jsonify({'error': 'Subject and message are required'}), 400
        
        # Get recipients based on type
        query = User.query.join(Resident).filter(User.status == 'active', User.role == 'resident')
        
        if recipient_type == 'owners':
            query = query.filter(Resident.is_owner == True)
        elif recipient_type == 'tenants':
            query = query.filter(Resident.is_owner == False)
        
        recipients = query.all()
        
        if not recipients:
            return jsonify({'error': 'No recipients found'}), 404
        
        # For demo purposes, we'll simulate email sending
        # In production, you would integrate with an email service like SendGrid, AWS SES, etc.
        sent_count = 0
        failed_emails = []
        
        for user in recipients:
            try:
                # Simulate email sending
                # send_email_via_service(user.email, subject, message)
                sent_count += 1
            except Exception as e:
                failed_emails.append(user.email)
        
        return jsonify({
            'message': f'Email sent successfully to {sent_count} recipients',
            'sent_count': sent_count,
            'failed_count': len(failed_emails),
            'failed_emails': failed_emails
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@communication_bp.route('/send-whatsapp', methods=['POST'])
@jwt_required()
def send_whatsapp_message():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        data = request.get_json()
        message = data.get('message')
        recipient_type = data.get('recipient_type', 'all')
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Get phone numbers based on recipient type
        query = Resident.query.join(User).filter(
            User.status == 'active', 
            User.role == 'resident',
            Resident.phone_number.isnot(None)
        )
        
        if recipient_type == 'owners':
            query = query.filter(Resident.is_owner == True)
        elif recipient_type == 'tenants':
            query = query.filter(Resident.is_owner == False)
        
        residents = query.all()
        
        if not residents:
            return jsonify({'error': 'No phone numbers found'}), 404
        
        # For demo purposes, we'll simulate WhatsApp API integration
        # In production, you would integrate with WhatsApp Business API
        sent_count = 0
        failed_numbers = []
        
        for resident in residents:
            try:
                # Simulate WhatsApp message sending
                # send_whatsapp_via_api(resident.phone_number, message)
                sent_count += 1
            except Exception as e:
                failed_numbers.append(resident.phone_number)
        
        return jsonify({
            'message': f'WhatsApp message sent successfully to {sent_count} recipients',
            'sent_count': sent_count,
            'failed_count': len(failed_numbers),
            'failed_numbers': failed_numbers
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@communication_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_message_templates():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    # Predefined message templates for common communications
    templates = [
        {
            'id': 'maintenance',
            'name': 'Maintenance Notice',
            'subject': 'Scheduled Maintenance - Altona Village',
            'message': 'Dear Residents,\n\nWe would like to inform you of scheduled maintenance work that will take place on [DATE] from [TIME] to [TIME].\n\nAffected areas: [AREAS]\n\nWe apologize for any inconvenience caused.\n\nBest regards,\nAltona Village Management'
        },
        {
            'id': 'security',
            'name': 'Security Alert',
            'subject': 'Security Notice - Altona Village',
            'message': 'Dear Residents,\n\nPlease be advised of the following security matter:\n\n[SECURITY_DETAILS]\n\nFor your safety, please:\n- [SAFETY_INSTRUCTION_1]\n- [SAFETY_INSTRUCTION_2]\n\nIf you notice anything suspicious, please contact security immediately.\n\nBest regards,\nAltona Village Management'
        },
        {
            'id': 'community',
            'name': 'Community Update',
            'subject': 'Community Update - Altona Village',
            'message': 'Dear Residents,\n\nWe hope this message finds you well. We wanted to share some important community updates:\n\n[UPDATE_DETAILS]\n\nThank you for being part of our community.\n\nBest regards,\nAltona Village Management'
        },
        {
            'id': 'emergency',
            'name': 'Emergency Notice',
            'subject': 'URGENT: Emergency Notice - Altona Village',
            'message': 'URGENT NOTICE\n\nDear Residents,\n\nWe need to inform you of an emergency situation:\n\n[EMERGENCY_DETAILS]\n\nImmediate action required:\n[ACTION_REQUIRED]\n\nFor assistance, contact: [EMERGENCY_CONTACT]\n\nAltona Village Management'
        }
    ]
    
    return jsonify(templates), 200

@communication_bp.route('/statistics', methods=['GET'])
@jwt_required()
def get_communication_statistics():
    admin_check = admin_required()
    if admin_check:
        return admin_check
    
    try:
        # Get communication statistics
        total_residents = User.query.filter_by(status='active', role='resident').count()
        residents_with_email = User.query.filter_by(status='active', role='resident').count()
        residents_with_phone = Resident.query.join(User).filter(
            User.status == 'active',
            User.role == 'resident',
            Resident.phone_number.isnot(None)
        ).count()
        
        owners_count = Resident.query.join(User).filter(
            User.status == 'active',
            User.role == 'resident',
            Resident.is_owner == True
        ).count()
        
        tenants_count = Resident.query.join(User).filter(
            User.status == 'active',
            User.role == 'resident',
            Resident.is_owner == False
        ).count()
        
        stats = {
            'total_residents': total_residents,
            'residents_with_email': residents_with_email,
            'residents_with_phone': residents_with_phone,
            'owners_count': owners_count,
            'tenants_count': tenants_count,
            'email_coverage': round((residents_with_email / total_residents * 100) if total_residents > 0 else 0, 1),
            'phone_coverage': round((residents_with_phone / total_residents * 100) if total_residents > 0 else 0, 1)
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def send_email_via_service(to_email, subject, message):
    """
    Placeholder function for email service integration
    In production, integrate with services like:
    - SendGrid
    - AWS SES
    - Mailgun
    - SMTP server
    """
    # Example SMTP implementation (commented out for demo)
    """
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    
    if not smtp_username or not smtp_password:
        raise Exception('SMTP credentials not configured')
    
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(message, 'plain'))
    
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    text = msg.as_string()
    server.sendmail(smtp_username, to_email, text)
    server.quit()
    """
    pass

def send_whatsapp_via_api(phone_number, message):
    """
    Placeholder function for WhatsApp API integration
    In production, integrate with:
    - WhatsApp Business API
    - Twilio WhatsApp API
    - Other WhatsApp providers
    """
    # Example implementation would make HTTP requests to WhatsApp API
    pass

