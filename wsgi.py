"""Production WSGI entry point for Project Juliana."""

from ChatbotWebsite import create_app


app = create_app()
