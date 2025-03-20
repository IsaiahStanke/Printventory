import os
import platform
import subprocess
import psycopg2
import sys
import getpass
from werkzeug.security import generate_password_hash

# Database details
DB_NAME = "printer_inventory"
DB_USER = "printer_user"

DEFAULT_MASTER_USER = "postgres"
DEFAULT_MASTER_PASSWORD = "MySecurePassword"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = "5432"

def check_postgresql_installed():
    """Check if PostgreSQL is installed."""
    try:
        subprocess.run(["psql", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("PostgreSQL is already installed.")
        return True
    except FileNotFoundError:
        print("PostgreSQL is not installed.")
        return False

def install_postgresql_windows():
    """Automatically download and install PostgreSQL on Windows."""
    print("\nInstalling PostgreSQL...")

    postgres_url = "https://sbp.enterprisedb.com/getfile.jsp?fileid=1259402"
    installer_path = os.path.join(os.getcwd(), "postgresql-17.4-1-windows-x64.exe")

    print(f"Downloading PostgreSQL from {postgres_url}...")
    subprocess.run(["powershell", "-Command", f"Invoke-WebRequest -Uri {postgres_url} -OutFile {installer_path}"])

    print("Running PostgreSQL installer...")
    subprocess.run([installer_path, "--mode", "unattended", "--superpassword", DEFAULT_MASTER_PASSWORD], check=True)

    print("PostgreSQL installation complete.")

def ensure_postgresql_running():
    """Ensure PostgreSQL service is running."""
    print("\nChecking PostgreSQL service...")
    if platform.system() == "Windows":
        service_name = "postgresql-x64-17"
        subprocess.run(["net", "start", service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(["sudo", "systemctl", "start", "postgresql"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def get_master_credentials():
    """Prompt user for PostgreSQL master credentials if defaults fail."""
    print("\nChecking PostgreSQL master credentials...")
    return {
        "MASTER_USER": DEFAULT_MASTER_USER,
        "MASTER_PASSWORD": DEFAULT_MASTER_PASSWORD,
        "MASTER_HOST": DEFAULT_HOST,
        "MASTER_PORT": DEFAULT_PORT
    }

def create_database_and_user(master_creds, app_password):
    """Create PostgreSQL database and user for the application."""
    print("\nSetting up PostgreSQL database and user...")

    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=master_creds["MASTER_USER"],
            password=master_creds["MASTER_PASSWORD"],
            host=master_creds["MASTER_HOST"],
            port=master_creds["MASTER_PORT"]
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Create database if it does not exist
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}';")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        # Create `printer_user` if it does not exist
        cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_USER}';")
        if not cur.fetchone():
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{app_password}';")
            print(f"User '{DB_USER}' created successfully.")
        else:
            print(f"User '{DB_USER}' already exists. Updating password...")
            cur.execute(f"ALTER USER {DB_USER} WITH PASSWORD '{app_password}';")

        # Grant privileges to `printer_user`
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")

        # Switch to `printer_inventory` and grant schema permissions
        conn.close()
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=master_creds["MASTER_USER"],
            password=master_creds["MASTER_PASSWORD"],
            host=master_creds["MASTER_HOST"],
            port=master_creds["MASTER_PORT"]
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Grant `printer_user` full access to the public schema
        cur.execute(f"GRANT USAGE, CREATE ON SCHEMA public TO {DB_USER};")
        cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {DB_USER};")
        cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {DB_USER};")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

def setup_database(app_password):
    """Run Flask migrations and set up the default admin user."""
    database_url = f"postgresql://{DB_USER}:{app_password}@localhost/{DB_NAME}"
    print("\nRunning database migrations and setting up default admin user...")

    try:
        from __init__ import create_app, db
        app = create_app(database_url)

        with app.app_context():
            from models import User
            db.create_all()

            existing_admin = User.query.filter_by(username="admin").first()
            if not existing_admin:
                hashed_pw = generate_password_hash("admin", method="pbkdf2:sha256")
                admin_user = User(username="admin", password_hash=hashed_pw, must_change_password=True)
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user 'admin' created. User must change password on first login.")

    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

def run_application():
    """Start the Flask application."""
    print("\nStarting the Flask app...")
    os.system("python app_main.py")

if __name__ == "__main__":
    if platform.system() == "Windows" and not check_postgresql_installed():
        install_postgresql_windows()

    ensure_postgresql_running()
    master_creds = get_master_credentials()
    app_password = getpass.getpass("Enter password for printer_user: ")

    create_database_and_user(master_creds, app_password)

    setup_database(app_password)
    run_application()
