# Built-in libraries
import os
from tempfile import mkdtemp
import datetime
import time

# Downloaded libraries
from sqlalchemy import create_engine, or_, and_, func
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify, make_response, send_from_directory, url_for
from flask_session import Session
from werkzeug.utils import secure_filename
from google.oauth2 import id_token
from google.auth.transport import requests
import psycopg2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from googletrans import Translator
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Custom libraries
from functions import *
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
cloudinary.config( 
  cloud_name = "ridna-library", 
  api_key = "293991876227891", 
  api_secret = "J-JAEXn7Cnb7pk8E6BBq2XqtbeA" 
)

# Configure variables
BORROW_PERIOD = 21 # borrow period in days

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

@app.route("/search", methods=["GET", "POST"])
def search():
    """Lookup a book by criteria"""
    BOOKS_PER_PAGE = 15
    session["error"]=False
    if request.method == "POST":
        if request.form.get("number"):
            number = int(request.form.get("number"))
            return redirect(f"/book/{number}")
        else:
            page = request.args.get('page', 1, type=int)
            query = request.form.get("query")
            age = request.form.getlist("age-group")
            if query:
                query = translator.translate(query, dest="uk")
                query = query.text
                query = "%{}%".format(query)
                query.strip()
                books = Book.query.filter(or_(Book.author.ilike(query), Book.name.ilike(query), Book.description.ilike(query)), Book.age_group.in_(age)).paginate(page=page, per_page=BOOKS_PER_PAGE)
            else:
                books = Book.query.filter(Book.age_group.in_(age)).paginate(page=page, per_page=BOOKS_PER_PAGE)
        if not books.items:
            session["error"]=True
            flash("Нічого не знайдено")
            return render_template("search.html", error=session.get("error"), user=session)
        return render_template("search.html", user=session, books=books, error=session.get("error"))
    else:
        page = request.args.get('page', 1, type=int)
        books = Book.query.paginate(page=page, per_page=BOOKS_PER_PAGE)
    return render_template("search.html", error=session.get("error"), user=session, books=books)

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
        else:
            soon.append(book)
        if book[0].borrow_start == datetime.date.today():
            prep.append(book)
    return render_template("dashboard.html", error=session.get("error"), user=session, today=today, later=later, soon=soon, over=over, prep=prep)

@app.route("/borrow/<int:id>", methods=["GET", "POST"])
@login_required
def borrow(id):
    """Borrow a book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    if not book:
        session["error"]=True
        flash("Не існує книги з таким id")
        return render_template("search.html", error=session.get("error"))
    if request.method == "POST":
        if book.borrowed == True:
            session["error"] = True
            flash("Виникла помилка")
            return redirect(f"/book/{id}")
        book.borrowed = True
        book.borrowed_by = session["school_id"]
        book.borrow_start = nextSat()
        if session["role"] == "student":
            book.borrow_end = book.borrow_start + datetime.timedelta(days=BORROW_PERIOD)
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
        flash("Книги не знайдено")
        return render_template("search.html", error=session.get("error"), user=session)
    if book.borrowed_by:
        borrower = User.query.filter_by(school_id=book.borrowed_by).first()
    else:
        borrower=None
    return render_template("book.html", user=session, error=session.get("error"), book=book, borrower=borrower, today=datetime.date.today())    

@app.route("/markout", methods=["GET", "POST"])
@admin_required
@login_required
def markout():
    """Mark out a book under someone's name"""
    session["error"]=False
    if request.method == "POST":
        person = User.query.filter_by(school_id=request.form.get("person")).first()
        book = Book.query.filter_by(id=(request.form.get("book"))).first()
        book.borrowed = True
        book.borrowed_by = person.school_id
        book.borrow_start = request.form.get("start")
        if person.role == "student":
            book.borrow_end = book.borrow_start + BORROW_PERIOD
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
    book = Book.query.filter_by(id=id).first()
    if not book:
        flash("Не існує книги з таким id")
        session["error"]=True
        return render_template("dashboard.html", error=session.get("error"), user=session)
    book.borrowed = False
    book.borrowed_by = None
    book.borrow_start = None
    book.borrow_end = None
    db.session.commit()
    flash("Книгу повернено")
    return redirect("/board")

@app.route("/cancel/<int:id>")
@login_required
def cancel(id):
    """Cancel upcoming book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    if book.borrowed_by == session["school_id"] and book.borrow_start > datetime.date.today():
        book.borrowed = False
        book.borrowed_by = None
        book.borrow_start = None
        book.borrow_end = None
        db.session.commit()
        flash("Замовлення скасовано")
        return redirect("/")
    elif book.borrowed_by == session["school_id"] and book.borrow_start <= datetime.date.today():
        session["error"]=True
        flash("Ви можете скасувати тільки не видані книги")
        return redirect("/")
    else:
        session["error"]=True
        flash("Ви не позичали цю книгу")
        return redirect("/")

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
        flash("Редагування успішне")
        return redirect(f"/edit/{id}")
    return render_template("edit.html", error=session.get("error"), user=session, book=book)

@app.route("/add", methods=["GET", "POST"])
@admin_required
@login_required
def add():
    """Add book to the library"""
    session["error"]=False
    if request.method == "POST":
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_result = cloudinary.uploader.upload(file)
            pic = upload_result["url"]
        else:
            pic = None
        book = Book(name=request.form.get("name"), author=request.form.get("author"), description=request.form.get("description"), age_group=request.form.get("age_group"), image=pic)
        db.session.add(book)
        db.session.commit()
        newid = book.id
        flash("Книгу додано")
        return redirect(f"/book/{newid}")
    return render_template("add.html", error=session.get("error"), user=session)

@app.route("/delete/<int:id>")
@admin_required
@login_required
def delete(id):
    """Delete book"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    db.session.delete(book)
    db.session.commit()
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
            flash("Людини не знайдено")
            return render_template("students.html", error=session.get("error"), user=session)
        return render_template("students.html", user=session, people=people, error=session.get("error"))
    else:
        people = None
    return render_template("students.html", error=session.get("error"), user=session, people=people)

@app.route("/")
@login_required
def index():
    today = datetime.date.today()
    inventory = Book.query.filter_by(borrowed_by=session["school_id"]).all()
    upcoming = []
    borrowed = []
    for book in inventory:
        if book.borrow_start > today:
            upcoming.append(book)
        else:
            borrowed.append(book)
    return render_template("home.html", user=session, borrowed=borrowed, error=session.get("error"), upcoming=upcoming)

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
        session["school_id"] = user.school_id
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
    flash("Сессія завершена")
    session.clear()
    time.sleep(2)
    return redirect("/login")

# Commands
#@app.cli.command("return_reminder")
#def return_reminder():
#    books = Book.query.filter_by(borrow_end=(datetime.date.today() + datetime.timedelta(days=1))).all()
#    return

# PWA routes

@app.route('/<path:text>')
def sw(text):
    if text.endswith("service-worker.js"):
        return app.send_static_file('service-worker.js')

if __name__ == "__main__":
    with app.app_context():
        app.run()