import os
import requests
import json
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
            nbofusers = db.execute('SELECT "Name" FROM "users" WHERE "Name"=:name', {"name": name}).rowcount
            if nbofusers == 0:
                password = request.form.get("password")
                db.execute('INSERT INTO "users" ("Name", "Password") values (:name, :password)', {"name": name, "password": password})
                db.commit()
                session["users"].append(name)
                return redirect("/search")
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
            nbofusers = db.execute('SELECT "Name" FROM "users" WHERE "Name"=:name AND "Password"=:password', {"name": name, "password": password}).rowcount
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
                books = db.execute('SELECT * FROM "books" WHERE \
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
    books = {}
    reviews = {}
    show = False
    show_review = False
    if session.get("users") == []:
        headline = "You are not connected"
    else:
        headline = "Please go to the search page."
    return render_template("book.html", headline=headline, books=books, reviews=reviews, show=show, show_review=show_review)

@app.route("/book/<string:isbn>", methods=["POST", "GET"])
def book(isbn):
    rating = request.form.get("rating")
    review = request.form.get("review")
    books = {}
    reviews = {}
    show = True
    show_review = False
    goodread_avg_rating = 0.0
    goodread_rating_count = 0
    try:
        name = session.get("users")[0]
    except IndexError:
        pass
    warning_review = ""
    if session.get("users") == []:
        headline = "You are not connected. Please login or register."
        show = False
    else:
        review_count = db.execute('SELECT * FROM "reviews" WHERE "isbn"= :ISBN_number AND "Name"= :name', {"ISBN_number": isbn, "name": name}).rowcount
        if review_count == 1:
            warning_review = "You have already submitted a review. If you submit again, it will replace your preview review."
        if request.method == "POST":
            if review_count == 0:
                db.execute('INSERT INTO "reviews" ("isbn", "Name", "Review", "Rating") \
                values (:isbn, :name, :Review, :Rating)', \
                {"isbn": isbn, "name": name, "Review": review, "Rating": rating})
                db.commit()
            else:
                db.execute('UPDATE "reviews" \
                            SET "Review"= :review, "Rating"= :rating \
                            WHERE "isbn"= :isbn AND "Name"= :name', \
                            {"review": review, "rating": rating, "isbn": isbn, "name": name})
                db.commit()
        headline = "Review of the book selected:"
        books = db.execute('SELECT * FROM "books" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
        reviews = db.execute('SELECT * FROM "reviews" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
        goodread = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "mihosn08BKf9oblUkFtoxA", "isbns": isbn}).json()
        goodread_avg_rating = goodread["books"][0]["average_rating"]
        goodread_rating_count = goodread["books"][0]["work_ratings_count"]
        show_review = (len(reviews) > 0)
    return render_template("book.html", headline=headline, books=books, reviews=reviews, show=show, show_review=show_review, warning_review=warning_review, goodread_avg_rating=goodread_avg_rating, goodread_rating_count=goodread_rating_count)

@app.route("/api/<string:isbn>")
def api(isbn):
    books = {}
    reviews = {}
    review_count = 0
    average_score = 0.0
    connected = True
    response = {}
    if session.get("users") == []:
        connected = False
    else:
        headline = ""
        books = db.execute('SELECT * FROM "books" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
        if len(books) == 0:
            return render_template("404.html")
        else:
            reviews = db.execute('SELECT * FROM "reviews" WHERE "isbn"= :ISBN_number', {"ISBN_number": isbn}).fetchall()
            review_count = len(reviews)
            for review in reviews:
                average_score += review[4]
            average_score = average_score / review_count
            response["title"] = books[0][1]
            response["author"] = books[0][2]
            response["year"] = books[0][3]
            response["isbn"] = books[0][0]
            response["review_count"] = review_count
            response["average_score"] = average_score
    return json.dumps(response)
