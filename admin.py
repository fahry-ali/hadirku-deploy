from flask import redirect, url_for, flash, request
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from wtforms import ValidationError
from models import User, Subject, AttendanceRecord
from app import db

class MyAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))

class UserAdmin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
    column_list = ['name', 'nim', 'email', 'is_admin', 'created_at']
    column_searchable_list = ['name', 'nim', 'email']
    column_filters = ['is_admin', 'created_at']
    
    # Hide sensitive fields
    form_excluded_columns = ['password_hash', 'face_encoding']
    column_exclude_list = ['password_hash', 'face_encoding']

class SubjectAdmin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
    # Form configuration
    form_columns = ['code', 'name', 'description']
    column_list = ['code', 'name', 'description', 'created_at']
    column_searchable_list = ['code', 'name']
    column_filters = ['code', 'name']
    
    # Labels dalam bahasa Indonesia
    column_labels = {
        'code': 'Kode MK',
        'name': 'Nama MK', 
        'description': 'Dosen Pengampu',
        'created_at': 'Dibuat Pada'
    }
    
    # Validasi
    def on_model_change(self, form, model, is_created):
        # Validasi required fields
        if not model.code or not model.code.strip():
            raise ValidationError('Kode mata kuliah harus diisi!')
        
        if not model.name or not model.name.strip():
            raise ValidationError('Nama mata kuliah harus diisi!')
        
        # Clean data
        model.code = model.code.strip().upper()
        model.name = model.name.strip()
        if model.description:
            model.description = model.description.strip()
        
        # Check duplicate hanya saat create
        if is_created:
            existing = Subject.query.filter_by(code=model.code).first()
            if existing:
                raise ValidationError(f'Kode mata kuliah "{model.code}" sudah ada!')

class AttendanceAdmin(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('auth.login'))
    
    # PERBAIKAN: Hanya gunakan direct fields untuk column_list dan searchable
    column_list = ['user_id', 'subject_id', 'status', 'timestamp']
    column_searchable_list = ['status']  # PERBAIKAN: Hanya field langsung yang bisa di-search
    column_filters = ['status', 'timestamp', 'user_id', 'subject_id']
    
    # Custom column formatters untuk menampilkan nama
    column_formatters = {
        'user_id': lambda v, c, m, p: m.user.name if m.user else 'N/A',
        'subject_id': lambda v, c, m, p: m.subject.name if m.subject else 'N/A'
    }
    
    column_labels = {
        'user_id': 'Nama Mahasiswa',
        'subject_id': 'Mata Kuliah',
        'status': 'Status',
        'timestamp': 'Waktu Presensi'
    }
    
    # Disable creation from admin panel (attendance should be done via face recognition)
    can_create = False
    can_edit = True
    can_delete = True

def init_admin(app):
    admin = Admin(app, name='Admin Hadirku', template_mode='bootstrap3', index_view=MyAdminIndexView())
    admin.add_view(UserAdmin(User, db.session, name='Pengguna'))
    admin.add_view(SubjectAdmin(Subject, db.session, name='Mata Kuliah'))
    admin.add_view(AttendanceAdmin(AttendanceRecord, db.session, name='Rekord Presensi'))
    return admin
