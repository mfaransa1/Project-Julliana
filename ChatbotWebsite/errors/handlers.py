from flask import Blueprint, current_app, render_template, request

errors = Blueprint("errors", __name__)


# 404 Error Page
@errors.app_errorhandler(404)
def error_404(error):
    return render_template("errors/404.html"), 404


# 403 Error Page
@errors.app_errorhandler(403)
def error_403(error):
    return render_template("errors/403.html"), 403


# 500 Error Page
@errors.app_errorhandler(500)
def error_500(error):
    # Do not attach exception details: ORM traces can include private values such
    # as email addresses and message text in bound SQL parameters.
    current_app.logger.error("Unhandled application error")
    return render_template("errors/500.html"), 500


@errors.app_errorhandler(429)
def error_429(error):
    return render_template("errors/429.html"), 429


@errors.after_app_request
def add_security_headers(response):
    """Apply low-risk browser protections without breaking current CDN assets."""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
    if request.endpoint and (
        request.endpoint.startswith("journals.")
        or request.endpoint.startswith("users.account")
        or request.endpoint.startswith("chatbot.chat")
    ):
        response.headers.setdefault("Cache-Control", "no-store, max-age=0")
    return response
