import os

from datetime import datetime
from cs50 import SQL, eprint
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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
db = SQL("sqlite:///hm.db")


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

    error = None

    if request.method == "POST":

        date = request.form.get("date")
        time = request.form.get("time")
        game = request.form.get("game")
        numberPlayers = request.form.get("numberPlayers")
        eventNumber = request.form.get("eventNumber")

        if not eventNumber and not date and not time and not game and not numberPlayers:
            error ="provide event number"
            return render_template("hub.html", error = error)

        elif eventNumber and not date or not time or not game or not numberPlayers:
            # insert user to existing event
            players = db.execute("SELECT players FROM event WHERE number = :eventNumber", eventNumber=eventNumber)[0]["players"]
            playersLen = len(players)
            eprint(playersLen)

            maxPlayers = db.execute("SELECT numberPlayers FROM event WHERE number = :eventNumber", eventNumber=eventNumber)[0]["numberPlayers"]
            eprint(maxPlayers)


            if maxPlayers < playersLen:
                error = "event already full"
                return render_template("hub.html", error=error)

            else:
                playerLoggedIn = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]
                eprint(playerLoggedIn)
                db.execute("INSERT INTO event (players) VALUES (:playerLoggedIn)", playerLoggedIn=playerLoggedIn)
                return redirect("/")

        # query db for creator of event
        creator = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]

        # insert data for a new event into db
        db.execute("INSERT INTO event (creator, date, time, game, numberPlayers, players) VALUES (:creator, :date, :time, :game, :numberPlayers, :players)",
                   creator=creator, date=date, time=time, game=game, numberPlayers=numberPlayers, players=creator)

        return redirect("/")

    else:
        event = db.execute("SELECT * FROM event")
        playerLoggedIn = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]
        return render_template("hub.html", playerLoggedIn=playerLoggedIn, event=event)

@app.route("/contact", methods=["GET", "POST"])
def contact():

    error = None

    if request.method == "POST":

        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        email = request.form.get("email")
        subject = request.form.get("subject")

        if not firstname or not lastname or not email or not subject:
            error = "provide data"
            return render_template("contact.html", error=error)

    else:
        return render_template("contact.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    error = None

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "provide username"
            return render_template("login.html", error = error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "must provide password"
            return render_template("login.html", error = error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "invalid username and/or password"
            return render_template("login.html", error = error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        flash("Login successful!")

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
    error = None
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            error = "provide username"
            return render_template("register.html", error = error)

        # ensure password was submitted
        elif not request.form.get("password"):
            error = "provide password"
            return render_template("register.html", error = error)

        # ensure password was confirmed
        elif not request.form.get("confirmation"):
            error = "confirm password"
            return render_template("register.html", error = error)

        # ensure password and confirm password do match
        elif request.form.get("password") != request.form.get("confirmation"):
            error = "passwords do not match"
            return render_template("register.html", error = error)

        # ensure username is not already taken
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) == 1:
            error = "username is already taken"
            return render_template("register.html", error=error)

        # insert user to database and log him into session
        session["user_id"] = db.execute("INSERT INTO users (username, hash) VALUES(:username, :hash)", username=request.form.get
                                        ("username"), hash=generate_password_hash(request.form.get("password")))

        # return to homepage
        flash("registered succesfully")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html", error = error)

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)


# listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
