from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='resident')
    status = db.Column(db.String(50), nullable=False, default='pending')
    
    # Email notification tracking
    approval_email_sent = db.Column(db.Boolean, default=False)
    approval_email_sent_at = db.Column(db.DateTime)
    rejection_email_sent = db.Column(db.Boolean, default=False)
    rejection_email_sent_at = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - Updated for multi-group support
    resident = db.relationship('Resident', backref='user', uselist=False, cascade='all, delete-orphan')
    owner = db.relationship('Owner', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_resident(self):
        """Check if user is a resident (including owner-residents)"""
        return self.resident is not None
    
    def is_owner(self):
        """Check if user is an owner (including owner-residents)"""
        return self.owner is not None
    
    def is_owner_resident(self):
        """Check if user is both owner and resident"""
        return self.resident is not None and self.owner is not None
    
    def get_full_name(self):
        """Get full name from resident or owner record"""
        if self.resident:
            return f"{self.resident.first_name} {self.resident.last_name}"
        elif self.owner:
            return f"{self.owner.first_name} {self.owner.last_name}"
        else:
            return self.email.split('@')[0].replace('.', ' ').title()

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'status': self.status,
            'is_resident': self.is_resident(),
            'is_owner': self.is_owner(),
            'is_owner_resident': self.is_owner_resident(),
            'full_name': self.get_full_name(),
            'approval_email_sent': self.approval_email_sent,
            'approval_email_sent_at': self.approval_email_sent_at.isoformat() if self.approval_email_sent_at else None,
            'rejection_email_sent': self.rejection_email_sent,
            'rejection_email_sent_at': self.rejection_email_sent_at.isoformat() if self.rejection_email_sent_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Resident(db.Model):
    __tablename__ = 'residents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    emergency_contact_name = db.Column(db.String(255))
    emergency_contact_number = db.Column(db.String(20))
    id_number = db.Column(db.String(50), nullable=False)
    erf_number = db.Column(db.String(50), nullable=False)
    
    # Separated address components for better sorting and gate access
    street_number = db.Column(db.String(10), nullable=False)
    street_name = db.Column(db.String(100), nullable=False)
    full_address = db.Column(db.String(255), nullable=False)  # For display purposes
    intercom_code = db.Column(db.String(20))  # Intercom access code
    
    moving_in_date = db.Column(db.Date)
    moving_out_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    properties = db.relationship('Property', backref='resident', lazy=True)
    vehicles = db.relationship('Vehicle', backref='resident', lazy=True, cascade='all, delete-orphan')
    complaints = db.relationship('Complaint', backref='resident', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Resident {self.first_name} {self.last_name}>'
    
    @property
    def display_address(self):
        """Get formatted address for display"""
        return f"{self.street_number} {self.street_name}"
    
    @property
    def gate_access_info(self):
        """Get formatted info for gate access register"""
        return {
            'name': f"{self.last_name}, {self.first_name}",
            'address': f"{self.street_name} {self.street_number}",
            'erf': self.erf_number,
            'phone': self.phone_number
        }

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_number': self.emergency_contact_number,
            'id_number': self.id_number,
            'erf_number': self.erf_number,
            'street_number': self.street_number,
            'street_name': self.street_name,
            'full_address': self.full_address,
            'intercom_code': self.intercom_code,
            'display_address': self.display_address,
            'gate_access_info': self.gate_access_info,
            'moving_in_date': self.moving_in_date.isoformat() if self.moving_in_date else None,
            'moving_out_date': self.moving_out_date.isoformat() if self.moving_out_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Owner(db.Model):
    __tablename__ = 'owners'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20))
    id_number = db.Column(db.String(50), nullable=False)
    erf_number = db.Column(db.String(50), nullable=False)
    
    # Separated address components for better sorting
    street_number = db.Column(db.String(10), nullable=False)
    street_name = db.Column(db.String(100), nullable=False)
    full_address = db.Column(db.String(255), nullable=False)  # For display purposes
    intercom_code = db.Column(db.String(20))  # Intercom access code
    
    # Owner-specific fields
    title_deed_number = db.Column(db.String(100))
    acquisition_date = db.Column(db.Date)
    
    # Separated postal address components for non-resident owners
    postal_street_number = db.Column(db.String(10))
    postal_street_name = db.Column(db.String(100))
    postal_suburb = db.Column(db.String(100))
    postal_city = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    postal_province = db.Column(db.String(50))
    full_postal_address = db.Column(db.String(500))  # Complete postal address
    
    emergency_contact_name = db.Column(db.String(255))
    emergency_contact_number = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Owner-specific relationships
    owned_properties = db.relationship('Property', backref='owner', lazy=True)
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Owner {self.first_name} {self.last_name}>'
    
    @property
    def display_address(self):
        """Get formatted address for display"""
        return f"{self.street_number} {self.street_name}"
    
    @property
    def display_postal_address(self):
        """Get formatted postal address for display"""
        if self.full_postal_address:
            return self.full_postal_address
        
        parts = []
        if self.postal_street_number and self.postal_street_name:
            parts.append(f"{self.postal_street_number} {self.postal_street_name}")
        if self.postal_suburb:
            parts.append(self.postal_suburb)
        if self.postal_city:
            parts.append(self.postal_city)
        if self.postal_code:
            parts.append(self.postal_code)
        if self.postal_province:
            parts.append(self.postal_province)
        
        return ", ".join(parts) if parts else None
    
    @property
    def gate_access_info(self):
        """Get formatted info for gate access register"""
        return {
            'name': f"{self.last_name}, {self.first_name}",
            'address': f"{self.street_name} {self.street_number}",
            'erf': self.erf_number,
            'phone': self.phone_number,
            'owner_type': 'Owner-Resident' if hasattr(self.user, 'resident') and self.user.resident else 'Non-Resident Owner'
        }

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'id_number': self.id_number,
            'erf_number': self.erf_number,
            'street_number': self.street_number,
            'street_name': self.street_name,
            'full_address': self.full_address,
            'intercom_code': self.intercom_code,
            'display_address': self.display_address,
            'title_deed_number': self.title_deed_number,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'postal_street_number': self.postal_street_number,
            'postal_street_name': self.postal_street_name,
            'postal_suburb': self.postal_suburb,
            'postal_city': self.postal_city,
            'postal_code': self.postal_code,
            'postal_province': self.postal_province,
            'full_postal_address': self.full_postal_address,
            'display_postal_address': self.display_postal_address,
            'gate_access_info': self.gate_access_info,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_number': self.emergency_contact_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    erf_number = db.Column(db.String(50), unique=True, nullable=False)
    
    # Separated address components for better sorting and gate access
    street_number = db.Column(db.String(10))
    street_name = db.Column(db.String(100))
    address = db.Column(db.String(255), nullable=False)  # Full address for display
    
    # Updated to support both resident and owner relationships
    resident_id = db.Column(db.String(36), db.ForeignKey('residents.id'))
    owner_id = db.Column(db.String(36), db.ForeignKey('owners.id'))
    plot_registered_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def display_address(self):
        """Get formatted address for display"""
        if self.street_number and self.street_name:
            return f"{self.street_number} {self.street_name}"
        return self.address
    
    def to_dict(self):
        return {
            'id': self.id,
            'erf_number': self.erf_number,
            'street_number': self.street_number,
            'street_name': self.street_name,
            'address': self.address,
            'display_address': self.display_address,
            'resident_id': self.resident_id,
            'owner_id': self.owner_id,
            'plot_registered_date': self.plot_registered_date.isoformat() if self.plot_registered_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    # Relationships
    builder = db.relationship('Builder', backref='property', uselist=False, cascade='all, delete-orphan')
    meters = db.relationship('Meter', backref='property', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Property {self.erf_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'erf_number': self.erf_number,
            'address': self.address,
            'resident_id': self.resident_id,
            'owner_id': self.owner_id,
            'plot_registered_date': self.plot_registered_date.isoformat() if self.plot_registered_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id = db.Column(db.String(36), db.ForeignKey('residents.id'), nullable=True)
    owner_id = db.Column(db.String(36), db.ForeignKey('owners.id'), nullable=True)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    make = db.Column(db.String(100))
    model = db.Column(db.String(100))
    color = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')  # active, inactive
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Vehicle {self.registration_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'resident_id': self.resident_id,
            'owner_id': self.owner_id,
            'registration_number': self.registration_number,
            'make': self.make,
            'model': self.model,
            'color': self.color,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Builder(db.Model):
    __tablename__ = 'builders'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    contact_number = db.Column(db.String(20))
    building_start_date = db.Column(db.Date)
    building_end_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Builder {self.company_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'company_name': self.company_name,
            'contact_person': self.contact_person,
            'contact_number': self.contact_number,
            'building_start_date': self.building_start_date.isoformat() if self.building_start_date else None,
            'building_end_date': self.building_end_date.isoformat() if self.building_end_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Meter(db.Model):
    __tablename__ = 'meters'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    property_id = db.Column(db.String(36), db.ForeignKey('properties.id'), nullable=False)
    meter_type = db.Column(db.String(50), nullable=False)
    meter_number = db.Column(db.String(100), unique=True, nullable=False)
    installation_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Meter {self.meter_type} - {self.meter_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'property_id': self.property_id,
            'meter_type': self.meter_type,
            'meter_number': self.meter_number,
            'installation_date': self.installation_date.isoformat() if self.installation_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Complaint(db.Model):
    __tablename__ = 'complaints'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id = db.Column(db.String(36), db.ForeignKey('residents.id'), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='open')
    priority = db.Column(db.String(50))
    assigned_to = db.Column(db.String(36), db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    updates = db.relationship('ComplaintUpdate', backref='complaint', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Complaint {self.subject}>'

    def to_dict(self):
        return {
            'id': self.id,
            'resident_id': self.resident_id,
            'subject': self.subject,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'assigned_to': self.assigned_to,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ComplaintUpdate(db.Model):
    __tablename__ = 'complaint_updates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    complaint_id = db.Column(db.String(36), db.ForeignKey('complaints.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    update_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<ComplaintUpdate {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'complaint_id': self.complaint_id,
            'user_id': self.user_id,
            'update_text': self.update_text,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserTransitionRequest(db.Model):
    __tablename__ = 'user_transition_requests'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    erf_number = db.Column(db.String(50), nullable=False)
    
    # Request type and basic info
    request_type = db.Column(db.String(50), nullable=False)  # 'owner_sale', 'tenant_moveout', 'owner_moving', 'other'
    current_role = db.Column(db.String(50), nullable=False)  # 'owner', 'tenant', 'owner_resident'
    
    # Timeline information
    intended_moveout_date = db.Column(db.Date)
    property_transfer_date = db.Column(db.Date)
    new_occupant_movein_date = db.Column(db.Date)
    notice_period = db.Column(db.String(50))
    
    # Sale specific details
    sale_agreement_signed = db.Column(db.Boolean, default=False)
    transfer_attorney = db.Column(db.String(255))
    expected_transfer_date = db.Column(db.Date)
    new_owner_details_known = db.Column(db.Boolean, default=False)
    
    # Tenant specific details
    lease_end_date = db.Column(db.Date)
    moveout_reason = db.Column(db.String(100))  # 'lease_expiry', 'early_termination', 'owner_reclaim', 'other'
    moveout_reason_other = db.Column(db.String(255))
    deposit_return_required = db.Column(db.Boolean, default=False)
    
    # Owner moving out (renting property)
    property_management_company = db.Column(db.String(255))
    new_tenant_selected = db.Column(db.Boolean, default=False)
    rental_start_date = db.Column(db.Date)
    
    # Community services to transfer/cancel
    gate_access_transfer = db.Column(db.Boolean, default=True)
    intercom_access_transfer = db.Column(db.Boolean, default=True)
    vehicle_registration_transfer = db.Column(db.Boolean, default=True)
    visitor_access_transfer = db.Column(db.Boolean, default=True)
    community_notifications_transfer = db.Column(db.Boolean, default=True)
    
    # Outstanding matters
    unpaid_levies = db.Column(db.Boolean, default=False)
    pending_maintenance = db.Column(db.Boolean, default=False)
    community_violations = db.Column(db.Boolean, default=False)
    outstanding_matters_other = db.Column(db.Text)
    
    # New occupant information (if known)
    new_occupant_type = db.Column(db.String(50))  # 'new_owner', 'new_tenant', 'unknown'
    new_occupant_name = db.Column(db.String(255))
    new_occupant_phone = db.Column(db.String(20))
    new_occupant_email = db.Column(db.String(255))
    new_occupant_adults = db.Column(db.Integer)
    new_occupant_children = db.Column(db.Integer)
    new_occupant_pets = db.Column(db.Integer)
    
    # Special instructions
    access_handover_requirements = db.Column(db.Text)
    property_condition_notes = db.Column(db.Text)
    community_introduction_needs = db.Column(db.Text)
    
    # System fields
    status = db.Column(db.String(50), nullable=False, default='pending_review')  # pending_review, in_progress, awaiting_docs, ready_for_transition, completed, cancelled
    priority = db.Column(db.String(50), default='standard')  # standard, urgent, emergency
    assigned_admin = db.Column(db.String(36), db.ForeignKey('users.id'))
    admin_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    
    # Extended new occupant information for user creation
    new_occupant_first_name = db.Column(db.Text)
    new_occupant_last_name = db.Column(db.Text)
    new_occupant_id_number = db.Column(db.Text)
    create_new_user_account = db.Column(db.Boolean, default=False)
    transfer_property_ownership = db.Column(db.Boolean, default=False)
    new_user_temp_password = db.Column(db.Text)
    
    # New occupant address information
    new_occupant_street_number = db.Column(db.Text)
    new_occupant_street_name = db.Column(db.Text)
    new_occupant_full_address = db.Column(db.Text)
    new_occupant_intercom_code = db.Column(db.Text)
    
    # Emergency contact
    new_occupant_emergency_contact_name = db.Column(db.Text)
    new_occupant_emergency_contact_number = db.Column(db.Text)
    
    # Additional move-in details
    new_occupant_moving_in_date = db.Column(db.Date)
    
    # Owner-specific fields
    new_occupant_title_deed_number = db.Column(db.Text)
    new_occupant_acquisition_date = db.Column(db.Date)
    
    # Postal address
    new_occupant_postal_street_number = db.Column(db.Text)
    new_occupant_postal_street_name = db.Column(db.Text)
    new_occupant_postal_suburb = db.Column(db.Text)
    new_occupant_postal_city = db.Column(db.Text)
    new_occupant_postal_code = db.Column(db.Text)
    new_occupant_postal_province = db.Column(db.Text)
    new_occupant_full_postal_address = db.Column(db.Text)
    
    # Migration tracking fields
    migration_completed = db.Column(db.Boolean, default=False)
    migration_date = db.Column(db.DateTime)
    new_user_id = db.Column(db.String(36), db.ForeignKey('users.id'))
    
    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='transition_requests')
    admin = db.relationship('User', foreign_keys=[assigned_admin])
    new_user = db.relationship('User', foreign_keys=[new_user_id])
    updates = db.relationship('TransitionRequestUpdate', backref='transition_request', lazy=True, cascade='all, delete-orphan')
    vehicles = db.relationship('TransitionVehicle', backref='transition_request', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<UserTransitionRequest {self.request_type} - ERF {self.erf_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'erf_number': self.erf_number,
            'request_type': self.request_type,
            'current_role': self.current_role,
            'intended_moveout_date': self.intended_moveout_date.isoformat() if self.intended_moveout_date else None,
            'property_transfer_date': self.property_transfer_date.isoformat() if self.property_transfer_date else None,
            'new_occupant_movein_date': self.new_occupant_movein_date.isoformat() if self.new_occupant_movein_date else None,
            'notice_period': self.notice_period,
            'sale_agreement_signed': self.sale_agreement_signed,
            'transfer_attorney': self.transfer_attorney,
            'expected_transfer_date': self.expected_transfer_date.isoformat() if self.expected_transfer_date else None,
            'new_owner_details_known': self.new_owner_details_known,
            'lease_end_date': self.lease_end_date.isoformat() if self.lease_end_date else None,
            'moveout_reason': self.moveout_reason,
            'moveout_reason_other': self.moveout_reason_other,
            'deposit_return_required': self.deposit_return_required,
            'property_management_company': self.property_management_company,
            'new_tenant_selected': self.new_tenant_selected,
            'rental_start_date': self.rental_start_date.isoformat() if self.rental_start_date else None,
            'gate_access_transfer': self.gate_access_transfer,
            'intercom_access_transfer': self.intercom_access_transfer,
            'vehicle_registration_transfer': self.vehicle_registration_transfer,
            'visitor_access_transfer': self.visitor_access_transfer,
            'community_notifications_transfer': self.community_notifications_transfer,
            'unpaid_levies': self.unpaid_levies,
            'pending_maintenance': self.pending_maintenance,
            'community_violations': self.community_violations,
            'outstanding_matters_other': self.outstanding_matters_other,
            'new_occupant_type': self.new_occupant_type,
            'new_occupant_name': self.new_occupant_name,
            'new_occupant_phone': self.new_occupant_phone,
            'new_occupant_email': self.new_occupant_email,
            'new_occupant_adults': self.new_occupant_adults,
            'new_occupant_children': self.new_occupant_children,
            'new_occupant_pets': self.new_occupant_pets,
            'access_handover_requirements': self.access_handover_requirements,
            'property_condition_notes': self.property_condition_notes,
            'community_introduction_needs': self.community_introduction_needs,
            'status': self.status,
            'priority': self.priority,
            'assigned_admin': self.assigned_admin,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'new_occupant_first_name': self.new_occupant_first_name,
            'new_occupant_last_name': self.new_occupant_last_name,
            'new_occupant_id_number': self.new_occupant_id_number,
            'create_new_user_account': self.create_new_user_account,
            'transfer_property_ownership': self.transfer_property_ownership,
            'new_user_temp_password': self.new_user_temp_password,
            'new_occupant_street_number': self.new_occupant_street_number,
            'new_occupant_street_name': self.new_occupant_street_name,
            'new_occupant_full_address': self.new_occupant_full_address,
            'new_occupant_intercom_code': self.new_occupant_intercom_code,
            'new_occupant_emergency_contact_name': self.new_occupant_emergency_contact_name,
            'new_occupant_emergency_contact_number': self.new_occupant_emergency_contact_number,
            'new_occupant_moving_in_date': self.new_occupant_moving_in_date.isoformat() if self.new_occupant_moving_in_date else None,
            'new_occupant_title_deed_number': self.new_occupant_title_deed_number,
            'new_occupant_acquisition_date': self.new_occupant_acquisition_date.isoformat() if self.new_occupant_acquisition_date else None,
            'new_occupant_postal_street_number': self.new_occupant_postal_street_number,
            'new_occupant_postal_street_name': self.new_occupant_postal_street_name,
            'new_occupant_postal_suburb': self.new_occupant_postal_suburb,
            'new_occupant_postal_city': self.new_occupant_postal_city,
            'new_occupant_postal_code': self.new_occupant_postal_code,
            'new_occupant_postal_province': self.new_occupant_postal_province,
            'new_occupant_full_postal_address': self.new_occupant_full_postal_address,
            'migration_completed': self.migration_completed,
            'migration_date': self.migration_date.isoformat() if self.migration_date else None,
            'new_user_id': self.new_user_id
        }

class TransitionRequestUpdate(db.Model):
    __tablename__ = 'transition_request_updates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transition_request_id = db.Column(db.String(36), db.ForeignKey('user_transition_requests.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    update_text = db.Column(db.Text, nullable=False)
    update_type = db.Column(db.String(50), default='comment')  # comment, status_change, admin_note
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<TransitionRequestUpdate {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'transition_request_id': self.transition_request_id,
            'user_id': self.user_id,
            'update_text': self.update_text,
            'update_type': self.update_type,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class TransitionVehicle(db.Model):
    __tablename__ = 'transition_vehicles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    transition_request_id = db.Column(db.String(36), db.ForeignKey('user_transition_requests.id'), nullable=False)
    vehicle_make = db.Column(db.String(100))
    vehicle_model = db.Column(db.String(100))
    license_plate = db.Column(db.String(50))
    color = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<TransitionVehicle {self.license_plate}>'

    def to_dict(self):
        return {
            'id': self.id,
            'transition_request_id': self.transition_request_id,
            'vehicle_make': self.vehicle_make,
            'vehicle_model': self.vehicle_model,
            'license_plate': self.license_plate,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class GateAccessLog(db.Model):
    __tablename__ = 'gate_access_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vehicle_id = db.Column(db.String(36), db.ForeignKey('vehicles.id'))
    access_time = db.Column(db.DateTime, nullable=False)
    access_type = db.Column(db.String(50), nullable=False)
    gate_id = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<GateAccessLog {self.access_type} - {self.access_time}>'

    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'access_time': self.access_time.isoformat() if self.access_time else None,
            'access_type': self.access_type,
            'gate_id': self.gate_id,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
