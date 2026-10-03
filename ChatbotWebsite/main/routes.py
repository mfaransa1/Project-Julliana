from flask import Blueprint, render_template
from ChatbotWebsite.main.resources import get_support_resources

main = Blueprint("main", __name__)


# Home Page
@main.route("/")
def home():
    return render_template("home.html", title="Juliana | Mental wellbeing companion")


# About Page
@main.route("/about")
def about():
    return render_template("about.html", title="About Juliana")


# SOS Page
@main.route("/sos")
def sos():
    return render_template(
        "sos.html", title="Urgent support", support_resources=get_support_resources()
    )


@main.route("/how-it-works")
def how_it_works():
    return render_template("how_it_works.html", title="How Juliana works")


@main.route("/safety")
def safety():
    return render_template("safety.html", title="Safety")


@main.route("/explore")
def explore():
    return render_template("explore.html", title="Explore wellbeing tools")


@main.route("/resources")
def resources():
    return render_template(
        "resources.html", title="Resources", support_resources=get_support_resources()
    )
