from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    nim = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    face_encoding = db.Column(db.LargeBinary)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)  # PERBAIKAN: Add unique constraint
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)  # PERBAIKAN: Nullable true untuk optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'
    
    # PERBAIKAN: Method untuk validasi
    def validate_data(self):
        errors = []
        
        if not self.code or not self.code.strip():
            errors.append("Kode mata kuliah harus diisi")
        
        if not self.name or not self.name.strip():
            errors.append("Nama mata kuliah harus diisi")
        
        if len(self.code.strip()) > 20:
            errors.append("Kode mata kuliah maksimal 20 karakter")
        
        if len(self.name.strip()) > 255:
            errors.append("Nama mata kuliah maksimal 255 karakter")
        
        return errors

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='hadir')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AttendanceRecord {self.user.name} - {self.subject.name}>'from app import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    nim = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    face_encoding = db.Column(db.LargeBinary)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Subject(db.Model):
    __tablename__ = 'subjects'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False, unique=True)  # PERBAIKAN: Add unique constraint
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)  # PERBAIKAN: Nullable true untuk optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='subject', lazy=True)
    
    def __repr__(self):
        return f'<Subject {self.code}: {self.name}>'
    
    # PERBAIKAN: Method untuk validasi
    def validate_data(self):
        errors = []
        
        if not self.code or not self.code.strip():
            errors.append("Kode mata kuliah harus diisi")
        
        if not self.name or not self.name.strip():
            errors.append("Nama mata kuliah harus diisi")
        
        if len(self.code.strip()) > 20:
            errors.append("Kode mata kuliah maksimal 20 karakter")
        
        if len(self.name.strip()) > 255:
            errors.append("Nama mata kuliah maksimal 255 karakter")
        
        return errors

class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='hadir')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AttendanceRecord {self.user.name} - {self.subject.name}>'
