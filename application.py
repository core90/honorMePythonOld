import os

from datetime import datetime
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_mail import Mail, Message
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure Mail Server
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config['MAIL_USERNAME'] = os.environ["USER_MAIL"]
app.config['MAIL_PASSWORD'] = os.environ["PW_MAIL"]
app.config["MAIL_PORT"] = 465
app.config['MAIL_USE_TLS'] = False
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set error to none
error = None


@app.route("/")
def index():

    return render_template("/index.html")


@app.route("/members")
def members():

    return render_template("members.html")


@app.route("/gallery")
def gallery():

    return render_template("gallery.html")


@app.route("/achievements")
def achievements():

    return render_template("achievements.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact Form"""

    if request.method == "POST":

        # define variables
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        subject = request.form.get("subject")
        clan_mail = "clan.honor.me@gmail.com"

        # Check inputs
        if not firstname or not lastname or not email or not subject:
            error = "provide data"
            return render_template("contact.html", error=error)

        # Configure Mail
        msg = Message("Request from Contact-Form", sender=clan_mail, recipients=[clan_mail])
        msg.body = firstname + "\n\n" + lastname + "\n\n" + email + "\n\n" + subject
        mail.send(msg)

        msg_return = Message("Request", sender=clan_mail, recipients=[email])
        msg_return.body = "Thank you for your request. We will answer as soon as possible!\n\n Clan Honor-Me"
        mail.send(msg_return)
        return redirect("/")

    else:
        return render_template("contact.html")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
