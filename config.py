import os

class Config:
    # 🔐 Secret key for session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'Aarti@CollegeAppKey2025'

    # 🗄 Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///noticeboard.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 📁 File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # 📧 Email configuration (Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'aartimadihali2102@gmail.com'   # Your Gmail
    MAIL_PASSWORD = 'mlrpoopgppvijjzf'              # App password (not your Gmail login password)

    # 📄 Allowed upload file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'docx'}
