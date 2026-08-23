from types import SimpleNamespace

from ChatbotWebsite import db
from ChatbotWebsite.models import ChatMessage, Journal

from conftest import login


def test_chat_endpoint_rejects_empty_messages(client):
    response = client.post("/chat_messages", data={"msg": "   "})

    assert response.status_code == 400
    assert response.get_json()["error"] == "Please enter a message."


def test_chat_endpoint_persists_a_user_and_bot_message(client, app, make_user, monkeypatch):
    user_id = make_user()
    monkeypatch.setattr(
        "ChatbotWebsite.chatbot.routes.get_reply",
        lambda *_args, **_kwargs: SimpleNamespace(
            text="A safe reply", learning_eligible=False
        ),
    )
    assert login(client).status_code == 302

    response = client.post("/chat_messages", data={"msg": "Hello Juliana"})

    assert response.status_code == 200
    assert response.get_json() == {"msg": "A safe reply"}
    with app.app_context():
        assert [(item.sender, item.message) for item in ChatMessage.query.all()] == [
            ("user", "Hello Juliana"),
            ("bot", "A safe reply"),
        ]


def test_admin_dashboard_requires_configured_user_and_hides_private_content(client, app, make_user):
    make_user()
    make_user("admin", "admin@example.com")
    with app.app_context():
        db.session.add_all(
            [
                Journal(mood="Private", content="journal content must not appear", user_id=user_id),
                ChatMessage(sender="user", message="chat content must not appear", user_id=user_id),
            ]
        )
        db.session.commit()

    assert client.get("/admin/").status_code == 302
    assert login(client).status_code == 302
    assert client.get("/admin/").status_code == 403
    client.post("/logout")

    assert login(client, "admin@example.com").status_code == 302
    response = client.get("/admin/")
    assert response.status_code == 200
    assert b"Service insights" in response.data
    assert b"journal content must not appear" not in response.data
    assert b"chat content must not appear" not in response.data
