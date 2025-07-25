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
    
    # Setup endpoint untuk Railway manual setup
    @app.route('/setup-admin/<password>')
    def setup_admin_endpoint(password):
        """
        Endpoint untuk create admin secara manual di Railway
        Usage: https://your-app.railway.app/setup-admin/yourpassword
        """
        if password != "railway123":  # Simple security
            return {'error': 'Invalid setup password'}, 403
            
        from models import User, MataKuliah
        from werkzeug.security import generate_password_hash
        
        try:
            # Create admin if not exists
            admin_exists = User.query.filter_by(is_admin=True).first()
            if not admin_exists:
                admin_user = User(
                    name="admin",
                    password=generate_password_hash("admin123", method='pbkdf2:sha256'),
                    is_admin=True
                )
                db.session.add(admin_user)
            
            # Create courses if not exists
            course_exists = MataKuliah.query.first()
            if not course_exists:
                courses = [
                    MataKuliah(kode_mk="S1076", nama_mk="Kecerdasan Bisnis", dosen_pengampu="Yanuar Wicaksono, S.Kom., M.Kom"),
                    MataKuliah(kode_mk="SI079", nama_mk="Sistem Pendukung Keputusan", dosen_pengampu="Dadang Heksaputra, S.Kom., M.Kom."),
                    MataKuliah(kode_mk="S1081", nama_mk="Manajemen Proyek", dosen_pengampu="Raden Nur Rachman Dzakiyullah, S.Kom., M.Sc."),
                    MataKuliah(kode_mk="S1084", nama_mk="Statistika untuk Bisnis", dosen_pengampu="Asti Ratnasari, S.Kom., M.Kom"),
                    MataKuliah(kode_mk="SI078", nama_mk="Bisnis Digital", dosen_pengampu="Eko Setiawan, S.Kom., M.Sc."),
                    MataKuliah(kode_mk="SI080", nama_mk="Integrasi Sistem", dosen_pengampu="Dadang Heksaputra, S.Kom., M.Kom.")
                ]
                for course in courses:
                    db.session.add(course)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'message': 'Admin and courses created successfully',
                'admin_username': 'admin',
                'admin_password': 'admin123',
                'login_url': '/login'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 500

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
        
        # --- AUTO SETUP untuk Railway ---
        setup_initial_data()

    return app

def setup_initial_data():
    """
    Setup initial data untuk Railway deployment
    """
    from models import User, MataKuliah
    from werkzeug.security import generate_password_hash
    
    # 1. Create default admin jika belum ada
    admin_exists = User.query.filter_by(is_admin=True).first()
    if not admin_exists:
        default_admin = User(
            name="admin",
            password=generate_password_hash("admin123", method='pbkdf2:sha256'),
            is_admin=True
        )
        db.session.add(default_admin)
        print("✅ Default admin created: username=admin, password=admin123")
    
    # 2. Create mata kuliah jika belum ada
    course_exists = MataKuliah.query.first()
    if not course_exists:
        courses = [
            MataKuliah(kode_mk="S1076", nama_mk="Kecerdasan Bisnis", dosen_pengampu="Yanuar Wicaksono, S.Kom., M.Kom"),
            MataKuliah(kode_mk="SI079", nama_mk="Sistem Pendukung Keputusan", dosen_pengampu="Dadang Heksaputra, S.Kom., M.Kom."),
            MataKuliah(kode_mk="S1081", nama_mk="Manajemen Proyek", dosen_pengampu="Raden Nur Rachman Dzakiyullah, S.Kom., M.Sc."),
            MataKuliah(kode_mk="S1084", nama_mk="Statistika untuk Bisnis", dosen_pengampu="Asti Ratnasari, S.Kom., M.Kom"),
            MataKuliah(kode_mk="SI078", nama_mk="Bisnis Digital", dosen_pengampu="Eko Setiawan, S.Kom., M.Sc."),
            MataKuliah(kode_mk="SI080", nama_mk="Integrasi Sistem", dosen_pengampu="Dadang Heksaputra, S.Kom., M.Kom.")
        ]
        for course in courses:
            db.session.add(course)
        print("✅ Default courses created")
    
    try:
        db.session.commit()
        print("✅ Initial data setup completed")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error setting up initial data: {e}")

if __name__ == '__main__':
    app = create_app()
    # Production configuration
    port = int(os.environ.get('PORT', 5000))
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

