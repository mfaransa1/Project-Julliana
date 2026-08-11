from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required
from sqlalchemy import or_
from ChatbotWebsite.models import Journal
from ChatbotWebsite.journal.forms import JournalForm
from ChatbotWebsite import db

journals = Blueprint("journals", __name__)


# All Journals Page
@journals.route("/all_journals")
@login_required
def all_journals():
    page = request.args.get("page", 1, type=int)  # Pagination
    search_query = request.args.get("q", "", type=str).strip()[:100]
    query = Journal.query.filter_by(user_id=current_user.id)
    if search_query:
        query = query.filter(
            or_(
                Journal.mood.ilike(f"%{search_query}%"),
                Journal.content.ilike(f"%{search_query}%"),
            )
        )
    journals = query.order_by(Journal.timestamp.desc()).paginate(
        page=page, per_page=5, error_out=False
    )
    return render_template(
        "all_journals.html",
        title="Journals",
        journals=journals,
        search_query=search_query,
    )


# New Journal Page
@journals.route("/journal/new", methods=["GET", "POST"])
@login_required
def new_journal():
    form = JournalForm()  # Create Journal Form
    if (
        form.validate_on_submit()
    ):  # If form is submitted, create new journal and add to database
        flash("Journal has been created!", "success")
        journal = Journal(
            mood=form.mood.data, content=form.content.data, user=current_user
        )
        db.session.add(journal)
        db.session.commit()
        return redirect(url_for("journals.all_journals"))
    return render_template(
        "create_journal.html", title="New Journal", legend="New Journal", form=form
    )


# Journal Page
@journals.route("/journal/<int:journal_id>")
@login_required
def journal(journal_id):
    journal = Journal.query.filter_by(
        id=journal_id, user_id=current_user.id
    ).first_or_404()
    return render_template(
        "journal.html", title="Journal #" + str(journal.id), journal=journal
    )


# Update Journal Page
@journals.route("/journal/<int:journal_id>/update", methods=["GET", "POST"])
@login_required
def update_journal(journal_id):
    journal = Journal.query.filter_by(
        id=journal_id, user_id=current_user.id
    ).first_or_404()
    form = JournalForm()  # Create Journal Form
    if (
        form.validate_on_submit()
    ):  # If form is submitted, update journal and add to database
        journal.mood = form.mood.data
        journal.content = form.content.data
        db.session.commit()
        flash("Journal has been updated!", "success")
        return redirect(url_for("journals.journal", journal_id=journal.id))
    elif request.method == "GET":
        form.mood.data = journal.mood
        form.content.data = journal.content
    return render_template(
        "create_journal.html",
        title="Update Journal",
        legend="Update Journal",
        journal=journal,
        form=form,
    )


# Delete Journal Route
@journals.route("/journal/<int:journal_id>/delete", methods=["POST"])
@login_required
def delete_journal(journal_id):
    journal = Journal.query.filter_by(
        id=journal_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(journal)
    db.session.commit()
    flash("Journal has been deleted!", "success")
    return redirect(url_for("journals.all_journals"))
