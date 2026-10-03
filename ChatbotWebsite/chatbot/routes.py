import secrets

from flask import Blueprint, current_app, jsonify, render_template, request, session
from flask_login import current_user
from ChatbotWebsite import db
from ChatbotWebsite.chatbot.engine import get_reply
from ChatbotWebsite.chatbot.learning import propose_candidate
from ChatbotWebsite.chatbot.mindfulness import get_description, mindfulness_exercises
from ChatbotWebsite.chatbot.starters import get_conversation_starters
from ChatbotWebsite.chatbot.test import get_questions, get_test_messages, tests
from ChatbotWebsite.chatbot.topic import get_content, topics
from ChatbotWebsite.models import ChatMessage, LearningCandidate

chatbot = Blueprint("chatbot", __name__)


def _conversation_id() -> str:
    if current_user.is_authenticated:
        return f"user:{current_user.id}"
    return f"guest:{session.setdefault('chat_context_id', secrets.token_urlsafe(16))}"


# Chat Page (Main Page)
@chatbot.route("/chat")
def chat():
    messages = None
    if current_user.is_authenticated:
        messages = ChatMessage.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "chat/chat.html",
        title="Chat",
        topics=topics,
        messages=messages,
        tests=tests,
        mindfulness_exercises=mindfulness_exercises,
        conversation_starters=get_conversation_starters(),
    )


# Chat Messages, Post reqeust, get response from chatbot and add both messages to database
@chatbot.route("/chat_messages", methods=["POST"])
def chatting():
    message = request.form.get("msg", "").strip()
    if not message:
        return jsonify({"error": "Please enter a message."}), 400
    if len(message) > 3000:
        return jsonify({"error": "Messages must be 3,000 characters or fewer."}), 400
    chatbot_reply = get_reply(message, conversation_id=_conversation_id())
    response = chatbot_reply.text
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=message, user=current_user)
        bot_message = ChatMessage(sender="bot", message=response, user=current_user)
        db.session.add(user_message)
        db.session.add(bot_message)
        if (
            current_app.config["LEARNING_CANDIDATES_ENABLED"]
            and chatbot_reply.learning_eligible
        ):
            candidate = propose_candidate(
                message,
                proposed_intent=chatbot_reply.proposed_intent,
                confidence=chatbot_reply.confidence,
                threshold=current_app.config["LEARNING_CONFIDENCE_THRESHOLD"],
            )
            if candidate:
                db.session.add(
                    LearningCandidate(
                        anonymized_text=candidate.anonymized_text,
                        proposed_intent=candidate.proposed_intent,
                        confidence=candidate.confidence,
                        language=chatbot_reply.language,
                    )
                )
        db.session.commit()
    return jsonify(
        {
            "msg": response,
            "safety_level": chatbot_reply.safety_level,
        }
    )


# Topic, Post request, get contents from topic and add all messages to database
@chatbot.route("/topic", methods=["POST"])
def topic():
    title = request.form.get("title", "").strip()
    if not title:
        return jsonify({"error": "Please choose a topic."}), 400
    contents = get_content(title)
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=title, user=current_user)
        db.session.add(user_message)
        for content in contents:
            bot_message = ChatMessage(sender="bot", message=content, user=current_user)
            db.session.add(bot_message)
        db.session.commit()
    return jsonify({"contents": contents})


# Test, Post request, get questions from test
@chatbot.route("/test", methods=["POST"])
def test():
    title = request.form.get("title", "").strip()
    if not title:
        return jsonify({"error": "Please choose a test."}), 400
    questions = get_questions(title)
    if current_user.is_authenticated:
        user_message = ChatMessage(sender="user", message=title, user=current_user)
        db.session.add(user_message)
        db.session.commit()
    return jsonify({"questions": questions})


# Test Score, Post request, get score message from test and add result to database
@chatbot.route("/score", methods=["POST"])
def score():
    score = request.form.get("score", "")
    title = request.form.get("title", "").strip()
    if not title or not score.isdigit():
        return jsonify({"error": "Please submit a valid test score."}), 400
    score_message = get_test_messages(title, score)
    if current_user.is_authenticated:
        bot_score_message = ChatMessage(
            sender="bot", message=score_message, user=current_user
        )
        db.session.add(bot_score_message)
        db.session.commit()
    return jsonify({"score_message": score_message})


# Mindfulness, Post request, get description, file_name from mindfulness exercise
@chatbot.route("/mindfulness", methods=["POST"])
def mindfulness():
    title = request.form.get("title", "").strip()
    if not title:
        return jsonify({"error": "Please choose an exercise."}), 400
    description, file_name = get_description(title)
    return jsonify({"description": description, "file_name": file_name})

@chatbot.route("/privacy")
def privacy():
    return render_template("privacy.html", title="Privacy Policy")
