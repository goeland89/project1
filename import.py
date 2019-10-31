import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL")) # database engine object from SQLAlchemy that manages connections to the database
                                                # DATABASE_URL is an environment variable that indicates where the database lives
db = scoped_session(sessionmaker(bind=engine))    # create a 'scoped session' that ensures different users' interactions with the
                                                # database are kept separate

db.execute('CREATE TABLE USERS ( \
    "Name" VARCHAR NOT NULL PRIMARY KEY, \
    "Password" VARCHAR NOT NULL)')
db.commit()

db.execute('CREATE TABLE BOOKS ( \
    "isbn" VARCHAR NOT NULL PRIMARY KEY, \
    "title" VARCHAR NOT NULL, \
    "author" VARCHAR NOT NULL, \
    "year" VARCHAR NOT NULL)')
db.commit()

db.execute('CREATE TABLE REVIEWS ( \
    "id" SERIAL PRIMARY KEY, \
    "isbn" VARCHAR NOT NULL REFERENCES BOOKS, \
    "Name" VARCHAR NOT NULL REFERENCES USERS, \
    "Review" VARCHAR NOT NULL, \
    "Rating" INTEGER NOT NULL)')
db.commit()



f = open("./books.csv")
reader = csv.reader(f)
for isbn, title, author, year in reader: # loop gives each column a name
    try:
        year = int(year)
        db.execute('INSERT INTO "books" ("isbn", "title", "author", "year") VALUES (:isbn, :title, :author, :year)', {"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added book {title} written in {year} by {author} which ISBN is {isbn}.")
    except ValueError:
        pass
db.commit() # transactions are assumed, so close the transaction finished
