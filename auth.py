from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import User, db
import os

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # Jika pengguna sudah login, langsung arahkan ke halaman utama
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')
        
        user = User.query.filter_by(name=name).first()

        if not user or not check_password_hash(user.password, password):
            flash('Nama atau password salah. Silakan coba lagi.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=True)
        
        # Selalu arahkan ke 'main.index' setelah login berhasil.
        # 'main.index' yang akan memutuskan tujuan akhir (admin atau presensi).
        return redirect(url_for('main.index'))

    return render_template('login.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        user = User.query.filter_by(name=name).first()
        if user:
            flash('Nama tersebut sudah terdaftar.', 'warning')
            return redirect(url_for('auth.signup'))
        
        new_user = User(
            name=name,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Registrasi Akun berhasil! Langkah selanjutnya adalah mendaftarkan wajah Anda.', 'success')
        return redirect(url_for('main.register_face'))
    
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Anda telah berhasil logout.', 'info')
    # Setelah logout, selalu kembali ke halaman login.
    return redirect(url_for('auth.login'))
