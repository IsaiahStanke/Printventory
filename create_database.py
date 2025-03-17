from __init__ import create_app, db  # Ensure this is correct based on your project structure

app = create_app()

with app.app_context():  # Ensure SQLAlchemy runs within the Flask app context
    db.create_all()
