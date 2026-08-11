from datetime import datetime
from ChatbotWebsite import db, login_manager
from flask_login import UserMixin
from itsdangerous import BadSignature, SignatureExpired
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer
from flask import current_app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# User class for the database


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    profile_image = db.Column(
        db.String(20), nullable=False, default='default.jpg')
    # Backref One to many relationship with ChatMessage Class
    messages = db.relationship('ChatMessage', backref='user', lazy=True)
    # Backref One to many relationship with Journal Class
    journals = db.relationship('Journal', backref='user', lazy=True)

    # Reset password token
    def get_reset_token(self):
        s = Serializer(current_app.config['SECRET_KEY'])
        token = s.dumps({'user_id': self.id}, salt="password-reset")
        return token

    # Verify reset password token
    @staticmethod
    def verify_reset_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token, salt="password-reset", max_age=1800)["user_id"]
        except (BadSignature, SignatureExpired, KeyError, TypeError):
            return None
        return db.session.get(User, user_id)

    # String representation of the user
    def __repr__(self):
        return f'User({self.username}, {self.email})'

# ChatMessage class for the database


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender = db.Column(db.String(5), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    message = db.Column(db.String(3000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)  # Foreign key to User Class

    # String representation of the chat message
    def __repr__(self):
        return f'ChatMessage({self.sender}, {self.timestamp}, {self.message})'

# Journal class for the database


class Journal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.now)
    mood = db.Column(db.String(30), nullable=False)
    content = db.Column(db.String(3000), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'user.id'), nullable=False)  # Foreign key to User Class

    # String representation of the journal
    def __repr__(self):
        return f'Journal({self.timestamp}, {self.mood}, {self.content})'


class LearningCandidate(db.Model):
    """A reviewed, anonymized training proposal with no user relationship."""

    __tablename__ = "learning_candidate"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="learning_candidate_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    anonymized_text = db.Column(db.String(1000), nullable=False)
    proposed_intent = db.Column(db.String(80), nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    language = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="pending", index=True)
    approved_intent = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class ModelVersion(db.Model):
    """Metadata for a candidate, active, or archived local chatbot model."""

    __tablename__ = "model_version"
    __table_args__ = (
        db.CheckConstraint(
            "status IN ('candidate', 'validated', 'current', 'archived', 'failed')",
            name="model_version_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    version = db.Column(db.String(80), nullable=False, unique=True)
    artifact_path = db.Column(db.String(255), nullable=False, unique=True)
    dataset_version = db.Column(db.String(80), nullable=False)
    validation_accuracy = db.Column(db.Float, nullable=True)
    safety_tests_passed = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default="candidate", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    promoted_at = db.Column(db.DateTime, nullable=True)
