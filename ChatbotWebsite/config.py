import os

class Config:
    DEBUG = True  # True for local testing, False for production
    SECRET_KEY = os.environ.get("SECRET_KEY") or "admin"  # fallback for local testing

    # MySQL configuration
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://julliana:mfaransa@localhost/julliana_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email configuration (optional, only if sending emails)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME") or "finghost@gmail.com"
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD") or "dpiz oshn ufck iwgl"
