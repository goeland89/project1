import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("welcome.html", session=session.get("users"))

@app.route("/registration", methods=["POST", "GET"])
def registration():
    headline = "Welcome to My Books application. Please register:"
    name = request.form.get("name")
    user_error = ""
    user_session = (session.get("users") == [])
    if user_session:
        if request.method == "POST":
            nbofusers = db.execute('SELECT "Name" FROM "USERS" WHERE "Name"=:name', {"name": name}).rowcount
            if nbofusers == 0:
                password = request.form.get("password")
                db.execute('INSERT INTO "USERS" ("Name", "Password") values (:name, :password)', {"name": name, "password": password})
                db.commit()
                session["users"].append(name)
                return redirect("/")
            else:
                user_error = "Name already used. Please select another name."
    else:
        headline = "You are already connected"
    return render_template("registration.html", headline=headline, user_error=user_error, user_session=user_session)

@app.route("/login", methods=["POST", "GET"])
def login():
    headline = "Login page"
    name = request.form.get("name")
    password = request.form.get("password")
    user_error = ""
    user_session = (session.get("users") == [])
    if user_session:
        if request.method == "POST":
            nbofusers = db.execute('SELECT "Name" FROM "USERS" WHERE "Name"=:name AND "Password"=:password', {"name": name, "password": password}).rowcount
            if nbofusers == 0:
                user_error = "Login error. Please log in again."
            else:
                if session.get("users") is None:
                    session["users"] = []
                if request.method == "POST":
                    session["users"].append(name)
                return redirect("/")
    else:
        headline = "You are already logged in"
    return render_template("login.html", headline=headline, user_error=user_error, user_session=user_session)

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if session.get("users") != []:
        headline = "Please confirm that you want to log out"
        connected = True
        if request.method == "POST":
            headline = "You are disconnected"
            connected = False
            session["users"] = []
    else:
        headline = "You are not connected."
        connected = False
    return render_template("logout.html", headline=headline, connected=connected)
