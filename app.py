import os
from flask import Flask
from flask_login import LoginManager

#Impor db dan model dari file models.py
from models import db, User

def create_app():
    """
    Factory function untuk membuat dan mengkonfigurasi aplikasi Flask.
    """
    app = Flask(__name__, instance_relative_config=True)

    # --- Konfigurasi Aplikasi ---
    # Production environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ganti-dengan-kunci-rahasia-yang-sangat-kuat')
    
    # Database configuration untuk Railway
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Railway PostgreSQL - fix untuk Railway
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local SQLite fallback
        app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(app.instance_path, 'attendance.db')}"
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

    # --- Inisialisasi Ekstensi ---
    db.init_app(app)
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # --- User Loader ---
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Registrasi Blueprints (Rute) ---
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Health check endpoint untuk Railway
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'hadirku-project'}

    with app.app_context():
        # --- Inisialisasi Panel Admin ---
        from admin import setup_admin
        setup_admin(app, db)

        # --- Membuat Folder dan Database ---
        try:
            os.makedirs(app.instance_path)
        except OSError:
            pass 

        captures_path = os.path.join(app.static_folder, 'captures')
        if not os.path.exists(captures_path):
            os.makedirs(captures_path)
            
        # Membuat semua tabel database jika belum ada
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

