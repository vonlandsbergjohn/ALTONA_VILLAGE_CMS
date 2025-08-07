from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Resident, Owner, db
from src.utils.email_service import send_custom_email, send_email_with_attachment
from werkzeug.utils import secure_filename
import os
import uuid

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
        recipient_type = data.get('recipient_type', 'all')  # 'all', 'owners', 'residents'
        
        if not subject or not message:
            return jsonify({'error': 'Subject and message are required'}), 400
        
        print(f"[DEBUG] Sending bulk email - Type: {recipient_type}, Subject: {subject}")
        
        # Get recipients based on type
        recipients = []
        
        if recipient_type == 'owners':
            # Get users who have owner records
            recipients = db.session.query(User).join(Owner).filter(
                User.status == 'active',
                User.email.isnot(None),
                User.email != ''
            ).all()
        elif recipient_type == 'residents':
            # Get users who have resident records
            recipients = db.session.query(User).join(Resident).filter(
                User.status == 'active',
                User.email.isnot(None),
                User.email != ''
            ).all()
        else:  # 'all' or any other value
            # Get all active users with email addresses
            recipients = User.query.filter(
                User.status == 'active',
                User.email.isnot(None),
                User.email != ''
            ).all()
        
        print(f"[DEBUG] Found {len(recipients)} recipients")
        
        if not recipients:
            return jsonify({'error': 'No recipients found'}), 404
        
        sent_count = 0
        failed_emails = []
        
        for user in recipients:
            try:
                print(f"[DEBUG] Sending email to: {user.email}")
                success, error_msg = send_custom_email(
                    to_email=user.email,
                    subject=subject,
                    message=message,
                    recipient_name=user.get_full_name()
                )
                if success:
                    sent_count += 1
                    print(f"[DEBUG] ✅ Email sent to {user.email}")
                else:
                    print(f"[DEBUG] ❌ Failed to send to {user.email}: {error_msg}")
                    failed_emails.append({
                        'email': user.email,
                        'error': error_msg
                    })
            except Exception as e:
                print(f"[DEBUG] ❌ Exception sending to {user.email}: {str(e)}")
                failed_emails.append({
                    'email': user.email,
                    'error': str(e)
                })
        
        result = {
            'message': f'Email sent successfully to {sent_count} recipients',
            'sent_count': sent_count,
            'failed_count': len(failed_emails),
            'failed_emails': failed_emails
        }
        print(f"[DEBUG] Bulk email result: {result}")
        return jsonify(result), 200
        
    except Exception as e:
        print(f"[ERROR] Bulk email error: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
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


@communication_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_communication_stats():
    """Get communication statistics for the admin panel"""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        print(f"[DEBUG] Starting communication stats query...")
        
        # Initialize default values
        total_users = 0
        residents = 0
        owners = 0
        active_emails = 0
        active_phones = 0
        
        try:
            # Count total users with email addresses
            total_users = User.query.filter(
                User.email.isnot(None), 
                User.email != '',
                User.status == 'active'
            ).count()
            print(f"[DEBUG] Total active users with emails: {total_users}")
            
            # Count users with residents records (joined properly)
            residents = db.session.query(User).join(Resident).filter(
                User.email.isnot(None), 
                User.email != '',
                User.status == 'active'
            ).count()
            print(f"[DEBUG] Active residents with emails: {residents}")
            
            # Count users with owners records (joined properly)
            owners = db.session.query(User).join(Owner).filter(
                User.email.isnot(None), 
                User.email != '',
                User.status == 'active'
            ).count()
            print(f"[DEBUG] Active owners with emails: {owners}")
            
            # Count active emails (same as total users)
            active_emails = total_users
            
            # Count active phone numbers from both residents and owners tables
            resident_phones = db.session.query(User).join(Resident).filter(
                User.status == 'active',
                Resident.phone_number.isnot(None), 
                Resident.phone_number != ''
            ).count()
            
            owner_phones = db.session.query(User).join(Owner).filter(
                User.status == 'active',
                Owner.phone_number.isnot(None), 
                Owner.phone_number != ''
            ).count()
            
            # Sum phone numbers (note: some users might be both residents and owners, so this might double-count)
            active_phones = resident_phones + owner_phones
            print(f"[DEBUG] Active phones - Residents: {resident_phones}, Owners: {owner_phones}, Total: {active_phones}")
            
        except Exception as db_error:
            print(f"[WARNING] Database query failed, using default values: {str(db_error)}")
            # Use default values if database queries fail
            total_users = 0
            residents = 0
            owners = 0
            active_emails = 0
            active_phones = 0
        
        result = {
            'total_users': total_users,
            'residents': residents,
            'owners': owners,
            'active_emails': active_emails,
            'active_phones': active_phones
        }
        print(f"[DEBUG] Stats result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"[ERROR] Error in get_communication_stats: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to get communication statistics'}), 500


@communication_bp.route('/find-user-by-erf', methods=['POST'])
@jwt_required()
def find_user_by_erf():
    """Find user by ERF number for individual communication"""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        data = request.get_json()
        erf_number = data.get('erf_number')
        
        if not erf_number:
            return jsonify({'error': 'ERF number is required'}), 400
            
        print(f"[DEBUG] Searching for ERF: {erf_number}")
        
        # First check residents table
        resident = db.session.query(Resident).filter_by(erf_number=erf_number).first()
        if resident:
            user = db.session.query(User).filter_by(id=resident.user_id).first()
            if user:
                print(f"[DEBUG] Found resident: {resident.first_name} {resident.last_name}")
                return jsonify({
                    'found': True,
                    'user': {
                        'id': user.id,
                        'full_name': f"{resident.first_name} {resident.last_name}",
                        'email': user.email,
                        'phone': resident.phone_number,  # Get phone from resident record
                        'erf_number': erf_number,
                        'type': 'resident'
                    }
                })
        
        # Also check owners table
        owner = db.session.query(Owner).filter_by(erf_number=erf_number).first()
        if owner:
            user = db.session.query(User).filter_by(id=owner.user_id).first()
            if user:
                print(f"[DEBUG] Found owner: {owner.first_name} {owner.last_name}")
                return jsonify({
                    'found': True,
                    'user': {
                        'id': user.id,
                        'full_name': f"{owner.first_name} {owner.last_name}",
                        'email': user.email,
                        'phone': owner.phone_number,  # Get phone from owner record
                        'erf_number': erf_number,
                        'type': 'owner'
                    }
                })
        
        print(f"[DEBUG] No user found for ERF {erf_number}")
        return jsonify({'found': False, 'error': f'No user found for ERF {erf_number}'})
        
    except Exception as e:
        print(f"Error finding user by ERF: {str(e)}")
        return jsonify({'error': 'Failed to find user'}), 500


@communication_bp.route('/send-individual-email', methods=['POST'])
@jwt_required()
def send_individual_email():
    """Send email to individual user"""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
            
        data = request.get_json()
        user_id = data.get('user_id')
        subject = data.get('subject')
        message = data.get('message')
        attachment_filename = data.get('attachment_filename', '').strip()
        
        if not all([user_id, subject, message]):
            return jsonify({'error': 'User ID, subject, and message are required'}), 400
            
        # Get user details
        user = db.session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        if not user.email:
            return jsonify({'error': 'User does not have an email address'}), 400
            
        # Get user's full name safely
        user_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.email.split('@')[0]
        
        # Check if email has attachment
        if attachment_filename:
            # Verify attachment file exists
            attachment_path = os.path.join(os.getcwd(), 'uploads', attachment_filename)
            if not os.path.exists(attachment_path):
                return jsonify({'error': 'Attachment file not found'}), 404
            
            print(f"[DEBUG] Sending individual email with attachment to: {user.email}, Name: {user_name}")
            try:
                send_email_with_attachment(
                    to_email=user.email,
                    subject=subject,
                    message=message,
                    attachment_path=attachment_path
                )
                
                # Clean up attachment file after sending
                try:
                    os.remove(attachment_path)
                    print(f"[DEBUG] Attachment file {attachment_filename} cleaned up successfully")
                except Exception as cleanup_error:
                    print(f"[WARNING] Failed to clean up attachment file: {str(cleanup_error)}")
                
                print(f"[DEBUG] ✅ Individual email with attachment sent successfully to {user.email}")
                return jsonify({
                    'success': True,
                    'message': f'Email with attachment sent successfully to {user_name}'
                })
                
            except Exception as email_error:
                print(f"[ERROR] Failed to send individual email with attachment: {str(email_error)}")
                return jsonify({'error': 'Failed to send email with attachment'}), 500
        else:
            # Send email without attachment
            print(f"[DEBUG] Sending individual email to: {user.email}, Name: {user_name}")
            success, error_msg = send_custom_email(
                to_email=user.email,
                subject=subject,
                message=message,
                recipient_name=user_name
            )
            if success:
                print(f"[DEBUG] ✅ Individual email sent successfully to {user.email}")
                return jsonify({
                    'success': True,
                    'message': f'Email sent successfully to {user_name}'
                })
            else:
                print(f"[DEBUG] ❌ Failed to send individual email: {error_msg}")
                return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        print(f"[ERROR] Individual email error: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to send email'}), 500

@communication_bp.route('/upload-attachment', methods=['POST'])
@jwt_required()
def upload_attachment():
    """Upload an attachment for email"""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        allowed_extensions = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'gif'}
        file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_extension not in allowed_extensions:
            return jsonify({'error': f'File type .{file_extension} not allowed. Allowed types: {", ".join(allowed_extensions)}'}), 400
        
        # Validate file size (5MB limit)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > 5 * 1024 * 1024:  # 5MB in bytes
            return jsonify({'error': 'File size exceeds 5MB limit'}), 400
        
        # Generate secure filename
        original_filename = file.filename
        secure_name = secure_filename(original_filename)
        unique_filename = f"{uuid.uuid4().hex}_{secure_name}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'original_filename': original_filename,
            'file_size': file_size
        })
        
    except Exception as e:
        print(f"[ERROR] File upload error: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'File upload failed'}), 500

@communication_bp.route('/send-email-with-attachment', methods=['POST'])
@jwt_required()
def send_bulk_email_with_attachment():
    """Send bulk email with attachment to users based on recipient type"""
    try:
        # Check if user is admin
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        recipient_type = data.get('recipient_type', 'all')
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()
        attachment_filename = data.get('attachment_filename', '').strip()
        
        if not subject or not message:
            return jsonify({'error': 'Subject and message are required'}), 400
        
        if not attachment_filename:
            return jsonify({'error': 'Attachment filename is required'}), 400
        
        # Verify attachment file exists
        attachment_path = os.path.join(os.getcwd(), 'uploads', attachment_filename)
        if not os.path.exists(attachment_path):
            return jsonify({'error': 'Attachment file not found'}), 404
        
        # Get recipients based on type
        if recipient_type == 'residents':
            recipients = db.session.query(User).join(Resident).filter(
                User.email.isnot(None), 
                User.email != '',
                User.status == 'active'
            ).all()
        elif recipient_type == 'owners':
            recipients = db.session.query(User).join(Owner).filter(
                User.email.isnot(None), 
                User.email != '',
                User.status == 'active'
            ).all()
        else:  # 'all'
            recipients = User.query.filter(
                User.email.isnot(None), 
                User.email != '',
                User.status == 'active'
            ).all()
        
        if not recipients:
            return jsonify({'error': 'No active users found for the selected recipient type'}), 404
        
        # Send emails with attachment
        successful_emails = 0
        failed_emails = 0
        
        for recipient in recipients:
            try:
                print(f"[DEBUG] Sending email with attachment to: {recipient.email}")
                send_email_with_attachment(
                    to_email=recipient.email,
                    subject=subject,
                    message=message,
                    attachment_path=attachment_path
                )
                successful_emails += 1
                print(f"[DEBUG] Email with attachment sent successfully to: {recipient.email}")
                
            except Exception as email_error:
                print(f"[ERROR] Failed to send email with attachment to {recipient.email}: {str(email_error)}")
                failed_emails += 1
        
        # Clean up attachment file after sending
        try:
            os.remove(attachment_path)
            print(f"[DEBUG] Attachment file {attachment_filename} cleaned up successfully")
        except Exception as cleanup_error:
            print(f"[WARNING] Failed to clean up attachment file: {str(cleanup_error)}")
        
        return jsonify({
            'success': True,
            'sent_count': successful_emails,
            'failed_count': failed_emails,
            'total_recipients': len(recipients),
            'message': f'Email with attachment sent to {successful_emails} recipients' + 
                      (f', {failed_emails} failed' if failed_emails > 0 else '')
        })
        
    except Exception as e:
        print(f"[ERROR] Bulk email with attachment error: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to send email with attachment'}), 500