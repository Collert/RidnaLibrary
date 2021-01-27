# Built-in libraries
import os
from tempfile import mkdtemp
import datetime
import time

# Downloaded libraries
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from google.oauth2 import id_token
from google.auth.transport import requests
import psycopg2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from googletrans import Translator
from flask_talisman import Talisman
import cloudinary as Cloud

# Custom libraries
from functions import login_required, admin_required, nextSat
from models import *

# Configure app
translator = Translator()
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Session(app)
Cloud.config.update = ({
    'cloud_name':os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'api_key': os.environ.get('CLOUDINARY_API_KEY'),
    'api_secret': os.environ.get('CLOUDINARY_API_SECRET')
})

# Initialise database
db.init_app(app)

# Get Google client ID for sign in button
gclient_id = os.environ.get("GOOGLE_CLIENT_ID")

@app.route("/profile")
@login_required
def profileown():
    """Display user's profile"""
    return render_template("profile.html", user=session, person=session, books=None)

@app.route("/profile/<int:id>")
@admin_required
@login_required
def profile(id):
    """Display other's profile"""
    person = User.query.filter_by(school_id=id).first()
    books = Book.query.filter_by(borrowed_by=id).all()
    return render_template("profile.html", user=session, person=person, books=books)

@app.route("/search")
def searchredir():
    return redirect("/search/1")

@app.route("/search/<int:pagenum>", methods=["GET", "POST"])
@login_required
def search(pagenum):
    """Lookup a book by criteria"""
    session["error"]=False
    if request.method == "POST":
        if request.form.get("query"):
            query = request.form.get("query")
            query = translator.translate(query, dest="uk")
            query = query.text
            query = "%{}%".format(query)
            query.strip()
            books = Book.query.filter(Book.author.ilike(query)).all()
            byname = Book.query.filter(Book.name.ilike(query)).all()
            for book in byname:
                books.append(book)
            qty = int(len(books)/15)+1
            curpage = books[((pagenum-1)*15):((pagenum*15)-1)]
        else:
            number = int(request.form.get("number"))
            return redirect(f"/book/{number}")
        if not books:
            session["error"]=True
            flash("Couldn't find the book")
            qty = 1
            return render_template("search.html", error=session.get("error"), user=session)
        return render_template("search.html", user=session, books=curpage, qty=qty, pagenum=pagenum, error=session.get("error"))
    else:
        books = Book.query.all()
        qty = int(len(books)/15)+1
        curpage = Book.query.offset((pagenum-1) * 15).limit(15)
    return render_template("search.html", error=session.get("error"), user=session, books=curpage, qty=qty, pagenum=pagenum)

@app.route("/board")
@admin_required
@login_required
def board():
    """Show the library dashboard"""
    dash = db.session.query(Book, User).outerjoin(Book, Book.borrowed_by == User.school_id).filter_by(borrowed=True).all()
    today, later, soon, over, prep = ([] for i in range(5))
    for book in dash:
        if book[0].borrow_end == datetime.date.today():
            today.append(book)
        elif book[0].borrow_end > datetime.date.today() + datetime.timedelta(days=3):
            later.append(book)
        elif book[0].borrow_end < datetime.date.today():
            over.append(book)
        elif book[0].borrow_start == datetime.date.today():
            prep.append(book)
        else:
            soon.append(book)
    return render_template("dashboard.html", error=session.get("error"), user=session, today=today, later=later, soon=soon, over=over, prep=prep)

@app.route("/borrow/<int:id>", methods=["GET", "POST"])
@login_required
def borrow(id):
    """Borrow a book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    if not book:
        session["error"]=True
        flash("No such book id")
        return render_template("search.html", error=session.get("error"))
    if request.method == "POST":
        if book.borrowed == True:
            session["error"] = True
            flash("There was an error")
            return redirect(f"/book/{id}")
        book.borrowed = True
        book.borrowed_by = session["user_id"]
        book.borrow_start = nextSat()
        if session["role"] == "student":
            book.borrow_end = book.borrow_start + datetime.timedelta(days=14)
        else:
            book.borrow_end = "2069-04-20"
        db.session.commit()
        return render_template("borrowed.html", user=session, book=book)
    return render_template("borrowed.html", user=session, error=session.get("error"), book=book)

@app.route("/book/<int:id>")
@login_required
def book(id):
    """Display a book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    if not book:
        session["error"]=True
        flash("No such book")
        return render_template("search.html", error=session.get("error"))
    if book.borrowed_by:
        borrower = User.query.filter_by(school_id=Book.borrowed_by).first()
    else:
        borrower=None
    return render_template("book.html", user=session, error=session.get("error"), book=book, borrower=borrower)    

@app.route("/markout", methods=["GET", "POST"])
@admin_required
@login_required
def markout():
    """Mark out a book under someone's name"""
    session["error"]=False
    if request.method == "POST":
        person = request.form.get("person")
        book = Book.query.filter_by(id=(request.form.get("book"))).first()
        book.borrowed = True
        book.borrowed_by = person
        book.borrow_start = request.form.get("start")
        if session["role"] == "student":
            book.borrow_end = book.borrow_start + 14
        else:
            book.borrow_end = "2069-04-20"
        db.session.commit()
        return render_template("borrowed.html", book=book, user=session, error=session.get("error"), origin="markout")
    return render_template("markout.html", user=session, error=session.get("error"))

@app.route("/return/<int:id>")
@admin_required
@login_required
def back(id):
    """Submit return to database"""
    session["error"]=False
    if not id:
        flash("No book id found")
        session["error"]=True
        return render_template("search.html", error=session.get("error"), user=session)
    book = Book.query.filter_by(id=id).first()
    book.borrowed = False
    book.borrowed_by = None
    book.borrow_start = None
    book.borrow_end = None
    db.session.commit()
    flash("Return susesful")
    return redirect("/board")

@app.route("/db")
@admin_required
@login_required
def database():
    """Route admin to database directly"""
    return render_template("database.html", user=session)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
@login_required
def edit(id):
    """Edit book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    if request.method == "POST":
        book.name = request.form.get("name")
        book.author = request.form.get("author")
        book.description = request.form.get("description")
        book.age_group = request.form.get("age_group")
        db.session.commit()
        flash("Edit susesful")
        return redirect(f"/edit/{id}")
    return render_template("edit.html", error=session.get("error"), user=session, book=book)

@app.route("/delete/<int:id>")
@admin_required
@login_required
def delete(id):
    """Delete book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    db.session.delete(book)
    return redirect("/search")

@app.route("/students", methods=["GET", "POST"])
@admin_required
@login_required
def students():
    """Lookup student info"""
    session["error"]=False
    if request.method == "POST":
        if request.form.get("first"):
            first = request.form.get("first")
            first.strip()
            last = request.form.get("last")
            last.strip()
            people = User.query.filter((User.first.ilike(first)), (User.last.ilike(last))).all()
        elif request.form.get("email"):
            email = request.form.get("email")
            email.strip()
            people = User.query.filter(User.email.ilike(email)).all()
        else:
            id = int(request.form.get("id"))
            return redirect(f"/profile/{id}")
        if not people:
            session["error"]=True
            flash("Couldn't find the person")
            return render_template("students.html", error=session.get("error"), user=session)
        return render_template("students.html", user=session, people=people, error=session.get("error"))
    else:
        people = None
    return render_template("students.html", error=session.get("error"), user=session, people=people)

@app.route("/")
@login_required
def index():
    today = datetime.date.today()
    inventory = Book.query.filter_by(borrowed_by=session["user_id"]).all()
    upcoming = []
    borrowed = []
    for book in inventory:
        if book.borrow_start > today:
            upcoming.append(book)
        else:
            borrowed.append(book)
    return render_template("home.html", user=session, borrowed=borrowed, error=session.get("error"), upcoming=upcoming)

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    session["error"] = False
    if request.method == "POST":
        token = request.form["idtoken"]
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), gclient_id)

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            guserid = idinfo['sub']
        except ValueError:
            # Invalid token
            pass
        user = User.query.filter_by(google_id=guserid).first()
        if not user:
            user = User(first=idinfo["given_name"], last=idinfo["family_name"], email=idinfo["email"], google_id=guserid, picture=idinfo["picture"])
            db.session.add(user)
            db.session.commit()
            user = User.query.filter_by(google_id=guserid).first()
        session["user_id"] = user.school_id
        session["first"] = user.first
        session["last"] = user.last
        session["email"] = user.email
        session["role"] = user.role
        session["picture"] = user.picture
        return redirect("/")
    return render_template("login.html", error=session.get("error"), google_signin_client_id=gclient_id, user=session)

@app.route("/logout")
@login_required
def logout():
    """Logout user"""
    flash("Logged out")
    session.clear()
    time.sleep(2)
    return redirect("/login")

# PWA routes

@app.route('/<path:text>')
def sw(text):
    if text.endswith("service-worker.js"):
        return app.send_static_file('service-worker.js')

if __name__ == "__main__":
    with app.app_context():
        app.run()