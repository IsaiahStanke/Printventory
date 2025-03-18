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
DEFAULT_MASTER_PASSWORD = "MySecurePassword"  # Default password from PostgreSQL auto-install
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
        service_name = "postgresql-x64-17"  # Change based on version
        subprocess.run(["net", "start", service_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        subprocess.run(["sudo", "systemctl", "start", "postgresql"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def check_master_credentials(username, password, host, port):
    """Check if PostgreSQL master credentials work."""
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user=username,
            password=password,
            host=host,
            port=port
        )
        conn.close()
        return True
    except psycopg2.OperationalError:
        return False

def get_master_credentials():
    """Automatically use default credentials or ask the user if needed."""
    print("\nChecking PostgreSQL master credentials...")

    # Try default credentials first
    if check_master_credentials(DEFAULT_MASTER_USER, DEFAULT_MASTER_PASSWORD, DEFAULT_HOST, DEFAULT_PORT):
        print("Using default PostgreSQL credentials.")
        return {
            "MASTER_USER": DEFAULT_MASTER_USER,
            "MASTER_PASSWORD": DEFAULT_MASTER_PASSWORD,
            "MASTER_HOST": DEFAULT_HOST,
            "MASTER_PORT": DEFAULT_PORT
        }

    # If default fails, ask the user
    print("Default credentials failed. Please enter PostgreSQL master credentials manually.")
    master_user = input("Enter PostgreSQL master username (default: postgres): ") or "postgres"
    master_password = getpass.getpass("Enter PostgreSQL master password: ")
    master_host = input("Enter PostgreSQL host (default: localhost): ") or "localhost"
    master_port = input("Enter PostgreSQL port (default: 5432): ") or "5432"

    return {
        "MASTER_USER": master_user,
        "MASTER_PASSWORD": master_password,
        "MASTER_HOST": master_host,
        "MASTER_PORT": master_port
    }

def ask_for_app_credentials():
    """Prompt the user to set a password for printer_user."""
    print("\nSet the password for the application database user (printer_user).")
    while True:
        db_password = getpass.getpass("Enter password for printer_user: ")
        confirm_password = getpass.getpass("Confirm password: ")
        if db_password == confirm_password:
            return db_password
        print("Passwords do not match. Try again.")

def create_database_and_user(master_creds, app_password):
    """Create PostgreSQL database and user for the application."""
    print("\nSetting up PostgreSQL database...")

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

        # Create database if it doesn't exist
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}';")
        if not cur.fetchone():
            cur.execute(f"CREATE DATABASE {DB_NAME};")
            print(f"Database '{DB_NAME}' created successfully.")
        else:
            print(f"Database '{DB_NAME}' already exists.")

        # Create user if it doesn't exist
        cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname = '{DB_USER}';")
        if not cur.fetchone():
            cur.execute(f"CREATE USER {DB_USER} WITH PASSWORD '{app_password}';")
            print(f"User '{DB_USER}' created successfully.")

        # Grant privileges
        cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

def install_dependencies():
    """Install required dependencies."""
    print("\nInstalling dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def setup_database(app_password):
    """Run Flask migrations and set up the default admin user."""
    database_url = f"postgresql://{DB_USER}:{app_password}@localhost/{DB_NAME}"

    print("\nRunning database migrations and setting up default admin user...")

    try:
        from __init__ import create_app, db
        from models import User, Printer, Toner

        app = create_app(database_url)  # ✅ Pass the correct database URL
        db.init_app(app)

        with app.app_context():
            db.create_all()

            # Ensure "admin" user exists
            existing_admin = User.query.filter_by(username="admin").first()
            if not existing_admin:
                hashed_pw = generate_password_hash("admin", method="pbkdf2:sha256")
                admin_user = User(username="admin", password_hash=hashed_pw, must_change_password=True)
                db.session.add(admin_user)
                db.session.commit()
                print("Default admin user 'admin' created (password: admin). User must change password on first login.")

    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)



def run_application():
    """Start the Flask application."""
    print("\nStarting the Flask app...")
    os.system("python main.py")

if __name__ == "__main__":
    if platform.system() == "Windows" and not check_postgresql_installed():
        install_postgresql_windows()

    ensure_postgresql_running()

    master_creds = get_master_credentials()

    app_password = ask_for_app_credentials()

    install_dependencies()

    create_database_and_user(master_creds, app_password)

    setup_database(app_password)

    run_application()
