import os
import pytz
from flask import url_for, redirect, flash, render_template, request
from flask_login import current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import BaseForm
from markupsafe import Markup
from wtforms import validators

from models import User, MataKuliah, AttendanceRecord, db

class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('auth.login'))
        
        recent_records = AttendanceRecord.query.order_by(AttendanceRecord.timestamp.desc()).limit(10).all()
        wib = pytz.timezone('Asia/Jakarta')
        for record in recent_records:
            record.local_time = record.timestamp.replace(tzinfo=pytz.utc).astimezone(wib)

        return self.render('admin/index.html', recent_records=recent_records)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "warning")
        return redirect(url_for('auth.login'))


class AttendanceAdminView(ModelView):
    can_create = False
    can_edit = False
    can_delete = True
    page_size = 50
    column_list = ['user', 'matakuliah', 'timestamp', 'location', 'image_path']
    column_labels = {'user': 'Nama Mahasiswa', 'matakuliah': 'Mata Kuliah', 'timestamp': 'Waktu Presensi (UTC)', 'location': 'Lokasi (Peta)', 'image_path': 'Bukti Foto'}

    def _location_formatter(view, context, model, name):
        if model.latitude and model.longitude:
            link = f"https://www.google.com/maps?q={model.latitude},{model.longitude}"
            return Markup(f'<a href="{link}" target="_blank">Lihat Lokasi</a>')
        return "N/A"

    def _list_thumbnail(self, context, model, name):
        if not model.image_path: return ''
        return Markup(f'<img src="{url_for("static", filename=model.image_path)}" width="100" class="img-thumbnail">')

    column_formatters = {'image_path': _list_thumbnail, 'location': _location_formatter}
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


class UserAdminView(ModelView):
    column_list = ['id', 'name', 'is_admin']
    column_exclude_list = ['password']
    # Sesuaikan dengan nama kolom baru di model User
    form_excluded_columns = ['password', 'records', 'face_encoding']
    column_searchable_list = ['name']
    column_filters = ['is_admin']

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


class MataKuliahAdminView(ModelView):
    can_create = True
    can_edit = True
    can_delete = True
    page_size = 20
    
    # Kolom yang ditampilkan di list view
    column_list = ['kode_mk', 'nama_mk', 'dosen_pengampu']
    column_labels = {
        'kode_mk': 'Kode Mata Kuliah',
        'nama_mk': 'Nama Mata Kuliah', 
        'dosen_pengampu': 'Dosen Pengampu'
    }
    
    # Kolom yang bisa dicari
    column_searchable_list = ['kode_mk', 'nama_mk', 'dosen_pengampu']
    
    # Kolom yang dikecualikan dari form (relationship)
    form_excluded_columns = ['records']
    
    # Validasi form dengan validators WTForms
    form_args = {
        'kode_mk': {
            'validators': [validators.DataRequired(), validators.Length(max=20)],
            'render_kw': {'placeholder': 'Contoh: S1076', 'class': 'form-control'}
        },
        'nama_mk': {
            'validators': [validators.DataRequired(), validators.Length(max=100)],
            'render_kw': {'placeholder': 'Contoh: Kecerdasan Bisnis', 'class': 'form-control'}
        },
        'dosen_pengampu': {
            'validators': [validators.DataRequired(), validators.Length(max=100)],
            'render_kw': {'placeholder': 'Contoh: Yanuar Wicaksono, S.Kom., M.Kom', 'class': 'form-control'}
        }
    }

    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        flash("Anda harus login sebagai admin untuk mengakses halaman ini.", "warning")
        return redirect(url_for('auth.login'))
    
    def on_model_change(self, form, model, is_created):
        """Override untuk custom logic saat model diubah/dibuat"""
        try:
            # Validasi kode MK harus unik
            if is_created:
                existing = MataKuliah.query.filter_by(kode_mk=model.kode_mk).first()
                if existing:
                    flash(f"Kode mata kuliah '{model.kode_mk}' sudah ada!", "error")
                    raise ValueError(f"Duplicate kode_mk: {model.kode_mk}")
            
            # Strip whitespace dari input
            model.kode_mk = model.kode_mk.strip() if model.kode_mk else ""
            model.nama_mk = model.nama_mk.strip() if model.nama_mk else ""
            model.dosen_pengampu = model.dosen_pengampu.strip() if model.dosen_pengampu else ""
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error: {str(e)}", "error")
            raise
    
    def on_model_delete(self, model):
        """Override untuk custom logic saat model dihapus"""
        try:
            # Cek apakah ada attendance record yang terkait
            if model.records.count() > 0:
                flash(f"Tidak dapat menghapus mata kuliah '{model.nama_mk}' karena masih ada riwayat presensi yang terkait.", "warning")
                raise ValueError("Cannot delete mata kuliah with existing attendance records")
        except Exception as e:
            flash(f"Error: {str(e)}", "error")
            raise


def setup_admin(app, db):
    admin = Admin(app, name='Dashboard Presensi', template_mode='bootstrap4', base_template='admin/my_master.html', index_view=MyAdminIndexView(name="Dashboard", url="/admin"))
    
    admin.add_view(UserAdminView(User, db.session, name="Data Pengguna"))
    admin.add_view(MataKuliahAdminView(MataKuliah, db.session, name="Data Mata Kuliah", category="Manajemen"))
    admin.add_view(AttendanceAdminView(AttendanceRecord, db.session, name="Riwayat Presensi", category="Manajemen"))
    
