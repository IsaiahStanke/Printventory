from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

# Initialize database globally
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret-key-goes-here'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'

    # Initialize database with app
    db.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from models import User  # Ensure User model is imported

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        
        # Create default admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            hashed_pw = generate_password_hash('admin', method='pbkdf2:sha256')
            admin = User(username='admin', password_hash=hashed_pw, must_change_password=True)
            db.session.add(admin)
            db.session.commit()

    # Register blueprints AFTER initializing app
    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app
