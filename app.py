import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_admin import Admin
from werkzeug.security import generate_password_hash
from datetime import datetime
import pytz

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'hadirku-super-secret-key-2025')
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'attendance.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # PERBAIKAN: Error handling configuration
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF untuk admin panel
    
    # Logging configuration
    if not app.debug:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silakan login untuk mengakses halaman ini.'
    login_manager.login_message_category = 'info'
    
    # Import models
    from models import User, Subject, AttendanceRecord
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # PERBAIKAN: Error handlers
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error('Server Error: %s', error)
        flash('Terjadi kesalahan internal. Silakan coba lagi.', 'danger')
        return redirect(url_for('admin.index'))
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        db.session.rollback()
        app.logger.error('Unhandled Exception: %s', e)
        flash(f'Error: {str(e)}', 'danger')
        return redirect(request.referrer or url_for('main.index'))
    
    # Register blueprints
    from main import main
    from auth import auth
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    
    # Initialize admin
    from admin import init_admin
    init_admin(app)
    
    # Create database tables and setup
    with app.app_context():
        try:
            # Create tables
            db.create_all()
            
            # Create admin user if not exists
            admin_user = User.query.filter_by(is_admin=True).first()
            if not admin_user:
                admin_user = User(
                    name='Administrator',
                    nim='ADMIN001',
                    email='admin@hadirku.com',
                    is_admin=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                
                # Add sample subjects
                sample_subjects = [
                    {'code': 'S1076', 'name': 'Kecerdasan Bisnis', 'description': 'Yanuar Wicaksono, S.Kom., M.Kom'},
                    {'code': 'S1079', 'name': 'Sistem Pendukung Keputusan', 'description': 'Dadang Heksaputra, S.Kom., M.Kom.'},
                    {'code': 'S1081', 'name': 'Manajemen Proyek', 'description': 'Raden Nur Rachman Dzakiyullah, S.Kom., M.Sc.'},
                    {'code': 'S1084', 'name': 'Statistika untuk Bisnis', 'description': 'Asti Ratnasari, S.Kom., M.Kom'},
                ]
                
                for subject_data in sample_subjects:
                    if not Subject.query.filter_by(code=subject_data['code']).first():
                        subject = Subject(**subject_data)
                        db.session.add(subject)
                
                db.session.commit()
                app.logger.info("Database initialized with admin user and sample subjects")
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database initialization error: {e}")
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'service': 'hadirku-project',
            'timestamp': datetime.now().isoformat()
        }
    
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)    
