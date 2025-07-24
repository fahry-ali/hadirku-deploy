from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import cv2
import numpy as np
from datetime import datetime
import pytz
import base64
from io import BytesIO
from PIL import Image
from models import db, User, Subject, AttendanceRecord  # PERBAIKAN: MataKuliah → Subject
from face_utils_mediapipe import generate_encoding_from_image, find_match_in_db
import logging

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('index.html', user=current_user)
    return render_template('index.html')

@main.route('/register_face')
@login_required
def register_face():
    return render_template('register_face.html')

@main.route('/process_face_registration', methods=['POST'])
@login_required
def process_face_registration():
    try:
        data = request.get_json()
        image_data = data.get('image')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'Tidak ada data gambar'})
        
        # Decode base64 image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        
        # Convert ke RGB array
        image_rgb = np.array(image.convert('RGB'))
        
        # Generate face encoding
        encoding = generate_encoding_from_image(image_rgb)
        
        if encoding is None:
            return jsonify({'success': False, 'message': 'Wajah tidak terdeteksi. Pastikan wajah terlihat jelas.'})
        
        # Save encoding to user
        current_user.face_encoding = encoding.tobytes()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registrasi wajah berhasil!'})
        
    except Exception as e:
        logging.error(f"Face registration error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@main.route('/attendance')
@login_required
def attendance():
    subjects = Subject.query.all()  # PERBAIKAN: MataKuliah → Subject
    return render_template('attendance.html', subjects=subjects)

@main.route('/process_attendance', methods=['POST'])
@login_required
def process_attendance():
    try:
        data = request.get_json()
        image_data = data.get('image')
        subject_id = data.get('subject_id')
        
        if not image_data or not subject_id:
            return jsonify({'success': False, 'message': 'Data tidak lengkap'})
        
        # Decode image
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))
        image_rgb = np.array(image.convert('RGB'))
        
        # Generate encoding from captured image
        captured_encoding = generate_encoding_from_image(image_rgb)
        
        if captured_encoding is None:
            return jsonify({'success': False, 'message': 'Wajah tidak terdeteksi'})
        
        # Find match in database
        matched_user = find_match_in_db(captured_encoding)
        
        if not matched_user:
            return jsonify({'success': False, 'message': 'Wajah tidak dikenali'})
        
        # Check if user already attended today
        today = datetime.now(pytz.timezone('Asia/Jakarta')).date()
        existing_record = AttendanceRecord.query.filter_by(
            user_id=matched_user.id,
            subject_id=subject_id
        ).filter(
            db.func.date(AttendanceRecord.timestamp) == today
        ).first()
        
        if existing_record:
            return jsonify({'success': False, 'message': 'Anda sudah melakukan presensi hari ini'})
        
        # Create attendance record
        attendance = AttendanceRecord(
            user_id=matched_user.id,
            subject_id=subject_id,
            status='hadir',
            timestamp=datetime.now(pytz.timezone('Asia/Jakarta'))
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Presensi berhasil untuk {matched_user.name}',
            'user_name': matched_user.name
        })
        
    except Exception as e:
        logging.error(f"Attendance processing error: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@main.route('/records')
@login_required
def records():
    if current_user.is_admin:
        # Admin can see all records
        records = AttendanceRecord.query.join(User).join(Subject).order_by(
            AttendanceRecord.timestamp.desc()
        ).all()
    else:
        # Users can only see their own records
        records = AttendanceRecord.query.filter_by(user_id=current_user.id).join(Subject).order_by(
            AttendanceRecord.timestamp.desc()
        ).all()
    
    return render_template('records.html', records=records)

@main.route('/setup')
def setup():
    try:
        # Create tables
        db.create_all()
        
        # Create admin user if not exists
        admin_user = User.query.filter_by(is_admin=True).first()
        if not admin_user:
            from werkzeug.security import generate_password_hash
            admin_user = User(
                name='Administrator',
                nim='ADMIN001',
                email='admin@hadirku.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin_user)
        
        # Add sample subjects if not exist
        sample_subjects = [
            {'code': 'S1076', 'name': 'Kecerdasan Bisnis', 'description': 'Yanuar Wicaksono, S.Kom., M.Kom'},
            {'code': 'S1079', 'name': 'Sistem Pendukung Keputusan', 'description': 'Dadang Heksaputra, S.Kom., M.Kom.'},
            {'code': 'S1081', 'name': 'Manajemen Proyek', 'description': 'Raden Nur Rachman Dzakiyullah, S.Kom., M.Sc.'},
            {'code': 'S1084', 'name': 'Statistika untuk Bisnis', 'description': 'Asti Ratnasari, S.Kom., M.Kom'},
        ]
        
        for subject_data in sample_subjects:
            if not Subject.query.filter_by(code=subject_data['code']).first():  # PERBAIKAN: MataKuliah → Subject
                subject = Subject(**subject_data)  # PERBAIKAN: MataKuliah → Subject
                db.session.add(subject)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Database setup completed successfully!',
            'admin_email': 'admin@hadirku.com',
            'admin_password': 'admin123'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
