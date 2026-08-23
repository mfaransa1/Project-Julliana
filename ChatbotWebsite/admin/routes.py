"""Opt-in administration views with no access to private content."""

from __future__ import annotations

from functools import wraps

from flask import Blueprint, abort, current_app, render_template
from flask_login import current_user, login_required
from sqlalchemy import func, inspect

from ChatbotWebsite import db
from ChatbotWebsite.models import ChatMessage, Journal, LearningCandidate, ModelVersion, User


admin = Blueprint("admin", __name__, url_prefix="/admin")


def is_admin_user(user) -> bool:
    """Return whether a signed-in user is explicitly configured as an admin."""
    return bool(
        user
        and user.is_authenticated
        and user.username.casefold()
        in current_app.config.get("ADMIN_USERNAMES", frozenset())
    )


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not is_admin_user(current_user):
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def _table_exists(table_name: str) -> bool:
    """Keep the dashboard usable before optional learning migrations run."""
    return inspect(db.engine).has_table(table_name)


def _count_by(model, field):
    return db.session.query(field, func.count(model.id)).group_by(field).order_by(func.count(model.id).desc()).all()


@admin.route("/")
@admin_required
def dashboard():
    """Show high-level operational metrics without selecting private text."""
    stats = {
        "users": db.session.query(func.count(User.id)).scalar() or 0,
        "messages": db.session.query(func.count(ChatMessage.id)).scalar() or 0,
        "journals": db.session.query(func.count(Journal.id)).scalar() or 0,
        "candidates": 0,
        "models": 0,
    }
    candidate_statuses = []
    intent_distribution = []
    language_distribution = []
    model_statuses = []

    if _table_exists(LearningCandidate.__tablename__):
        stats["candidates"] = db.session.query(func.count(LearningCandidate.id)).scalar() or 0
        candidate_statuses = _count_by(LearningCandidate, LearningCandidate.status)
        intent_distribution = _count_by(LearningCandidate, LearningCandidate.proposed_intent)
        language_distribution = _count_by(LearningCandidate, LearningCandidate.language)

    if _table_exists(ModelVersion.__tablename__):
        stats["models"] = db.session.query(func.count(ModelVersion.id)).scalar() or 0
        model_statuses = _count_by(ModelVersion, ModelVersion.status)

    return render_template(
        "admin/dashboard.html",
        title="Insights | Juliana",
        stats=stats,
        candidate_statuses=candidate_statuses,
        intent_distribution=intent_distribution,
        language_distribution=language_distribution,
        model_statuses=model_statuses,
    )
