import os

from flask import Flask, session, render_template, request
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
    return "PROJECT TO DO"

@app.route("/hello", methods=["POST"])
def hello():
    name = request.form.get("name")
    if name == "":
        headline = "Empty name not accepted."
        return render_template("registration.html", headline=headline)
    nbofusers = db.execute('SELECT "Name" FROM "USERS"').rowcount
    if nbofusers == 1:
        password = request.form.get("password")
        db.execute('INSERT INTO "USERS" ("Name", "Password") values (123, 345)')
        db.commit()
        headline = "You are registered"
        return render_template("hello.html", name=name, headline=headline)
    else:
        headline = "Name already used. Please select another name."
        return render_template("registration.html", headline=headline)

@app.route("/registration")
def registration():
    headline = "Welcome to My Books application. Please register:"
    return render_template("registration.html", headline=headline)

@app.route("/login")
def login():
    headline = "Please login"
    return render_template("login.html", headline=headline)
