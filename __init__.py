from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# ✅ Define the single instance of db
db = SQLAlchemy()

def create_app(database_url=None):
    app = Flask(__name__)

    if database_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///db.sqlite"

    app.config['SECRET_KEY'] = 'your_secret_key'
    
    db.init_app(app)  # ✅ Initialize db ONCE

    with app.app_context():
        from models import User  # ✅ Import models after db is initialized

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from app_main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app
