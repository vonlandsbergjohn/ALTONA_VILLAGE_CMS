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
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    resident = db.relationship('Resident', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'status': self.status,
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
    is_owner = db.Column(db.Boolean, nullable=False)
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

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone_number': self.phone_number,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_number': self.emergency_contact_number,
            'is_owner': self.is_owner,
            'moving_in_date': self.moving_in_date.isoformat() if self.moving_in_date else None,
            'moving_out_date': self.moving_out_date.isoformat() if self.moving_out_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Property(db.Model):
    __tablename__ = 'properties'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    erf_number = db.Column(db.String(50), unique=True, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    resident_id = db.Column(db.String(36), db.ForeignKey('residents.id'))
    plot_registered_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
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
            'plot_registered_date': self.plot_registered_date.isoformat() if self.plot_registered_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    resident_id = db.Column(db.String(36), db.ForeignKey('residents.id'), nullable=False)
    registration_number = db.Column(db.String(50), unique=True, nullable=False)
    make = db.Column(db.String(100))
    model = db.Column(db.String(100))
    color = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Vehicle {self.registration_number}>'

    def to_dict(self):
        return {
            'id': self.id,
            'resident_id': self.resident_id,
            'registration_number': self.registration_number,
            'make': self.make,
            'model': self.model,
            'color': self.color,
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
