from ChatbotWebsite import db
from ChatbotWebsite.models import ChatMessage, Journal, User

from conftest import login


def test_registration_login_and_post_only_logout(client, app):
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "safe-password",
            "confirm_password": "safe-password",
        },
    )
    assert response.status_code == 302

    assert login(client, "newuser@example.com").status_code == 302
    assert client.get("/logout").status_code == 405
    assert client.post("/logout").status_code == 302


def test_password_reset_request_does_not_disclose_account_existence(client):
    response = client.post("/reset_password", data={"email": "missing@example.com"}, follow_redirects=True)

    assert response.status_code == 200
    assert b"If that email address has an account" in response.data


def test_account_deletion_removes_owned_messages_and_journals(client, app, make_user):
    user_id = make_user()
    with app.app_context():
        db.session.add_all(
            [
                ChatMessage(sender="user", message="private message", user_id=user_id),
                Journal(mood="Low", content="private journal", user_id=user_id),
            ]
        )
        db.session.commit()

    assert login(client).status_code == 302
    assert client.post("/delete_account", follow_redirects=True).status_code == 200

    with app.app_context():
        assert db.session.get(User, user_id) is None
        assert ChatMessage.query.count() == 0
        assert Journal.query.count() == 0
