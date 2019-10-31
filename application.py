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
    headline = "Welcome to My Books application."
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
                return redirect("/search")
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

@app.route("/search", methods=["POST", "GET"])
def search():
#search for a book according to name, author, year or ISBN
#partial search accepted
    connected = False
    results = False
    ISBN_number = request.form.get("ISBN_number")
    title = request.form.get("title")
    author = request.form.get("author")
    year = request.form.get("year")
    search_error = ""
    books={}
    if session.get("users") == []:
        headline = "You are not connected"
    else:
        connected = True
        headline = "You can search for books:"
        if request.method == "POST":
            if ISBN_number == "" and title == "" and author == "" and year == "":
                search_error = "At least 1 criterion must be filled"
            else:
                books = db.execute('SELECT * FROM "BOOKS" WHERE \
                    "author" LIKE :author AND \
                    "title" LIKE :title AND \
                    "isbn" LIKE :ISBN_number AND \
                    "year"  LIKE :year', \
                    {"author": "%"+author+"%", "title": "%"+title+"%", "ISBN_number": "%"+ISBN_number+"%", "year": "%"+year+"%"}).fetchall()
                if len(books) >0:
                    results = True
    return render_template("search.html", headline=headline, connected=connected, search_error=search_error, books=books, results=results)

@app.route("/book")
def books():
    if session.get("users") == []:
        headline = "You are not connected"
    else:
        headline = "Please go to the search page."
    return render_template("book.html", headline=headline)

@app.route("/book/<string:isbn>")
def book(isbn):
#display the average rating and number of ratings on goodread
#user should be able to submit its own review including a rating from 1 to 5 and a comment
#only 1 review per user
    books = {}
    reviews = {}
    if session.get("users") == []:
        headline = "You are not connected. Please login or register."
    else:
        headline = "Review of the book selected:"
        books = db.execute('SELECT * FROM "BOOKS" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
        reviews = db.execute('SELECT * FROM "REVIEWS" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
    return render_template("book.html", headline=headline, books=books, reviews=reviews)

@app.route("/api/<string:isbn>")
def api(isbn):
    books = {}
    reviews = {}
    review_count = 0
    average_score = 0.0
    connected = True
    if session.get("users") == []:
        connected = False
    else:
        headline = ""
        books = db.execute('SELECT * FROM "BOOKS" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
        if len(books) == 0:
            return render_template("404.html")
        else:
            reviews = db.execute('SELECT * FROM "REVIEWS" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
            review_count = len(reviews)
            for review in reviews:
                average_score += review[3]
            average_score = average_score / review_count
    return render_template("api.html", connected=connected, review_count=review_count, average_score=average_score, books=books)
