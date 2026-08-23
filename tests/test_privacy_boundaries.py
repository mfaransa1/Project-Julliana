from ChatbotWebsite import db
from ChatbotWebsite.models import ChatMessage, Journal

from conftest import login


def test_user_cannot_open_another_users_journal(client, app, make_user):
    alice_id = make_user()
    bob_id = make_user("bob", "bob@example.com")
    with app.app_context():
        bob_journal = Journal(mood="Private", content="Bob's entry", user_id=bob_id)
        db.session.add(bob_journal)
        db.session.commit()
        journal_id = bob_journal.id

    assert login(client).status_code == 302
    assert client.get(f"/journal/{journal_id}").status_code == 404
    assert client.get(f"/journal/{journal_id}/update").status_code == 404
    assert client.post(f"/journal/{journal_id}/delete").status_code == 404


def test_chat_history_only_displays_the_signed_in_users_messages(client, app, make_user):
    alice_id = make_user()
    bob_id = make_user("bob", "bob@example.com")
    with app.app_context():
        db.session.add_all(
            [
                ChatMessage(sender="user", message="Alice private chat", user_id=alice_id),
                ChatMessage(sender="user", message="Bob private chat", user_id=bob_id),
            ]
        )
        db.session.commit()

    assert login(client).status_code == 302
    response = client.get("/chat")

    assert b"Alice private chat" in response.data
    assert b"Bob private chat" not in response.data
