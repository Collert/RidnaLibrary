# Built-in libraries
import os
from tempfile import mkdtemp

# Downloaded libraries
from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from google.oauth2 import id_token
from google.auth.transport import requests

# Custom libraries
from functions import login_required, admin_required, nextSat
from models import *

# Configure app
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Session(app)

# Initialise database
db.init_app(app)

# Get Google client ID for sign in button
gclient_id = os.environ.get("GOOGLE_CLIENT_ID")

@app.route("/profile")
@login_required
def profile():
    """Display user's profile"""
    return render_template("profile.html", user=session)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Lookup a book by criteria"""
    session["error"]=False
    if request.method == "POST":
        query = "%%" + request.form.get("query") + "%%"
        number = int(request.form.get("number"))
        book = Book.query.filter((author == query) | (name == query) | (id == number))
        if not book:
            session["error"]=True
            flash("Couldn't find the book")
            return render_template("search.html", error=session.get("error"), user=session)
        return render_template("book.html", user=session, book=book, error=session.get("error"))
    return render_template("search.html", error=session.get("error"), user=session)

@app.route("/board")
@admin_required
@login_required
def board():
    """Show the library dashboard"""
    dash = Book.query.filter_by(borrowed=True).all()
    return render_template("dashboard.html", error=session.get("error"), user=session, board=dash)

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
        return redirect(f"/borrowed/{id}")
    return render_template("borrow.html", user=session, error=session.get("error"), book=book)

@app.route("/borrowed/<int:id>", methods=["POST"])
def borrowed(id):
    """Register book borrowing. Display borrowed message"""
    book = Book.query.filter_by(id=id).first()
    book.borrowed = True
    book.borrowed_by = session["school_id"]
    book.borrowed_start = nextSat()
    if session["role"] == "student":
        book.borrowed_end = book.borrowed_start + 14
    else:
        book.borrowed_end = "2069-04-20"
    db.session.commit()
    return render_template("borrowed.html", user=session)

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
        book.borrowed_start = nextSat()
        if session["role"] == "student":
            book.borrowed_end = book.borrowed_start + 14
        else:
            book.borrowed_end = "2069-04-20"
        db.session.commit()
        return render_template("borrowed.html", user=session, error=session.get("error"))
    return render_template("markout.html", user=session, error=session.get("error"))

@app.route("/return", methods=["GET", "POST"])
@admin_required
@login_required
def back():
    session["error"]=False
    if request.method == "POST":
        book = request.form.get("book")
        return redirect(f"/return/{book}")
    return render_template("return.html", user=session, error=session.get("error"))

@app.route("/return/<int:id>", methods=["POST"])
@admin_required
@login_required
def back_conf(id):
    """Submit return to database"""
    session["error"]=False
    if not id:
        flash("No book id found")
        session["error"]=True
        return render_template("return.html", error=session.get("error"), user=session)
    book = Book.query.filter_by(id=id).first()
    book.borrowed = False
    book.borrowed_by = None
    book.borrow_start = None
    book.borrow_end = None
    db.session.commit()
    flash("Return susesful")
    return redirect("/return", error=session.get("error"))

@app.route("/db")
@admin_required
@login_required
def database():
    """Route admin to database directly"""
    return render_template("database.html", user=session)

@app.route("/students", methods=["GET", "POST"])
@admin_required
@login_required
def students():
    """Lookup student info"""
    session["error"]=False
    if request.method == "POST":
        id = int(request.form.get("id"))
        first = request.form.get("first")
        last = request.form.get("last")
        email = request.form.get("email")
        if id:
            student = User.query.filter_by(school_id=id).first()
        elif first and last:
            student = User.query.filter((first == first), (last == last)).all()
        elif email:
            student = User.query.filter_by(email=email).first()
        if not student:
            session["error"]=True
            flash("No such student found")
            return render_template("students.html", user=session, error=session.get("error"))
        return render_template("student.html", user=session, error=session.get("error"), student=student)
    return render_template("students.html", user=session, error=session.get("error"))

@app.route("/")
@login_required
def index():
    inventory = Book.query.filter_by(borrowed_by=session["user_id"]).all()
    return render_template("home.html", user=session, inventory=inventory, error=session.get("error"))

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    error = False
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
        session["pfp"] = user.picture
        return redirect("/")
    return render_template("login.html", error=error, google_signin_client_id=gclient_id, user=session)

@app.route("/logout")
@login_required
def logout():
    """Logout user"""
    flash("Logged out")
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        app.run()