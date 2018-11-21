import os

from datetime import datetime
from cs50 import SQL, eprint
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
app.config['MAIL_USERNAME'] = "clan.honor.me@gmail.com"
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

# Configure CS50 Library to use SQLite database
db = SQL("postgres://fybljbtjcgjkst:a806f19f3debc10d81fd69ceb2f8651f9438192aea5918f08c4edd99827c3990@ec2-54-246-85-234.eu-west-1.compute.amazonaws.com:5432/dabfsmfgenkbhs")

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


@app.route("/hub", methods=["GET", "POST"])
@login_required
def hub():
    """Creating user events"""

    if request.method == "POST":

        # Define variables
        date = request.form.get("date")
        time = request.form.get("time")
        game = request.form.get("game")
        numberPlayers = request.form.get("numberPlayers")
        eventNumber = request.form.get("eventNumber")

        # Check if there are valid inputs for new event or joining existing event
        if not eventNumber and not date and not time and not game and not numberPlayers:
            error = "provide event number"
            return render_template("hub.html", error=error)

        # If user wants to join event (event Number is given)
        # Query for event data
        elif eventNumber:
            playerLoggedIn = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]
            playerTable = db.execute("SELECT number, player FROM players WHERE number = :eventNumber", eventNumber=eventNumber)
            maxPlayer = db.execute("SELECT numberPlayers FROM event WHERE number = :eventNumber",
                                   eventNumber=eventNumber)[0]["numberPlayers"]

            # Chek if event is full
            if (len(playerTable) >= maxPlayer):
                error = "event already full"
                return render_template("hub.html", error=error)

            # Check if player is already in event
            if any(d['player'] == playerLoggedIn for d in playerTable):
                error = "you cannot join event again"
                return render_template("hub.html", error=error)

            # Insert player to table
            db.execute("INSERT INTO players (number, player) VALUES (:number, :playerLoggedIn)",
                       number=eventNumber, playerLoggedIn=playerLoggedIn)
            return redirect("/")

        # Else if user wants to create an event
        elif date and time and game and numberPlayers:

            # Query db for creator of event
            creator = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]

            # Insert data for a new event into db
            db.execute("INSERT INTO event (creator, date, time, game, numberPlayers) VALUES (:creator, :date, :time, :game, :numberPlayers)",
                       creator=creator, date=date, time=time, game=game, numberPlayers=numberPlayers)

            # Query for newest event number
            latestEventNumber = db.execute("SELECT number FROM event")[-1]["number"]

            # Insert creator into players table
            db.execute("INSERT INTO players (number, player) VALUES (:latestEventNumber, :creator)",
                       latestEventNumber=latestEventNumber, creator=creator)

            return redirect("/")

    else:
        # If user reaches page per redirect or GET request
        # Query db for data
        event = db.execute("SELECT e.number, e.creator, e.date, e.time, e.game, e.numberPlayers, \
                           (SELECT GROUP_CONCAT(p.player) FROM players p WHERE p.number = e.number) \
                            AS players FROM event e ORDER BY e.number ASC")

        return render_template("hub.html", event=event)


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


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "provide username"
            return render_template("login.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "must provide password"
            return render_template("login.html", error=error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("login.html", error=error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "provide username"
            return render_template("register.html", error=error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "provide password"
            return render_template("register.html", error=error)

        # Ensure password was confirmed
        elif not request.form.get("confirmation"):
            error = "confirm password"
            return render_template("register.html", error=error)

        # Ensure password and confirm password do match
        elif request.form.get("password") != request.form.get("confirmation"):
            error = "passwords do not match"
            return render_template("register.html", error=error)

        # Ensure username is not already taken
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) == 1:
            error = "username is already taken"
            return render_template("register.html", error=error)

        # Insert user to database and log him into session
        session["user_id"] = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get
                                        ("username"), hash=generate_password_hash(request.form.get("password")))

        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
