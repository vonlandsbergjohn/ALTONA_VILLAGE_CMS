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
                    body=message,
                    attachment_path=attachment_path
                )
                
                # Clean up attachment file after sending
                try:
                    os.remove(attachment_path)
                    print(f"[DEBUG] Attachment file {attachment_filename} cleaned up successfully")
                except Exception as cleanup_error:
                    print(f"[WARNING] Failed to clean up attachment file: {str(cleanup_error)}")
                
                print(f"[DEBUG] Individual email with attachment sent successfully to {user.email}")
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
                print(f"[DEBUG] Individual email sent successfully to {user.email}")
                return jsonify({
                    'success': True,
                    'message': f'Email sent successfully to {user_name}'
                })
            else:
                print(f"[DEBUG] Failed to send individual email: {error_msg}")
                return jsonify({'error': error_msg}), 500
            
    except Exception as e:
        print(f"[ERROR] Individual email error: {str(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Failed to send email'}), 500
