from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_mail import Mail
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from ChatbotWebsite.config import Config, get_config

# Initialize the extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
mail = Mail()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'


def create_app(config_class: type[Config] | None = None):
    app = Flask(__name__)
    selected_config = config_class or get_config()
    app.config.from_object(selected_config)
    selected_config.validate()
    app.static_folder = 'static'

    # Initialize the extensions
    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    login_manager.init_app(app)
    csrf.init_app(app)

    if app.config["AUTO_CREATE_SCHEMA"]:
        # This opt-in bootstrap is only for a new empty database on platforms
        # without a release-command feature. It never performs schema upgrades.
        from ChatbotWebsite import models  # noqa: F401

        with app.app_context():
            db.create_all()
        app.logger.warning("Created missing database tables via AUTO_CREATE_SCHEMA.")

    # Import the routes
    from ChatbotWebsite.main.routes import main
    from ChatbotWebsite.chatbot.routes import chatbot
    from ChatbotWebsite.users.routes import users
    from ChatbotWebsite.errors.handlers import errors
    from ChatbotWebsite.journal.routes import journals
    from ChatbotWebsite.admin.routes import admin, is_admin_user

    # Register the routes
    app.register_blueprint(users)
    app.register_blueprint(chatbot)
    app.register_blueprint(main)
    app.register_blueprint(errors)
    app.register_blueprint(journals)
    app.register_blueprint(admin)

    @app.context_processor
    def inject_admin_state():
        return {"is_admin": is_admin_user(current_user)}

    return app
