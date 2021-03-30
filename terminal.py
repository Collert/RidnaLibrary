# Built-in libraries
import os
from tempfile import mkdtemp
import datetime

# Downloaded libraries
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from google.oauth2 import id_token
from google.auth.transport import requests
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from googletrans import Translator
import cloudinary
import cloudinary.uploader
import cloudinary.api

# Custom libraries
from functions import *
from models import *
import app as web

# Configure app
translator = Translator()
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_BINDS"] ={
    "basic_data": os.getenv("DATABASE_URL"),
    "big_data": os.getenv("HEROKU_POSTGRESQL_GRAY_URL"),
    "reviews": os.getenv("HEROKU_POSTGRESQL_AMBER_URL")
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
Session(app)
cloudinary.config( 
  cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.getenv("CLOUDINARY_API_KEY"), 
  api_secret = os.getenv("CLOUDINARY_API_SECRET") 
)

# Configure variables
FROM_EMAIL = 'library@ridneslovo.ca'
SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY') #SendGrid API key

# Initialise database
db.init_app(app)

@app.route("/privacy")
def privacy():
    """Show privacy policy"""
    return render_template("privacy.html", user=session)

@app.route("/terms")
def terms():
    """Show terms of service"""
    return render_template("terms.html", user=session)

@app.route("/profile")
@login_required
def profileown():
    """Display user's profile"""
    return render_template("profile.html", user=session, person=session, books=None)

@app.route("/search", methods=["GET", "POST"])
@login_required
def terminal_search():
    web.search()
    

@app.route("/borrow/<int:id>", methods=["GET", "POST"])
@login_required
def terminal_borrow(id):
    web.borrow(id)
    

@app.route("/book/<int:id>")
@login_required
def terminal_book(id):
    web.book(id)
    

@app.route("/return/<int:id>")
@admin_required
@login_required
def back(id):
    """Submit return to database"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    if not book.borrowed:
        flash("Книга не позичина")
        session["error"]=True
        return render_template("dashboard.html", error=session.get("error"), user=session)
    record = Record(book_id=book.id, borrowed_by=book.borrowed_by, borrowed_on=book.borrow_start, returned_on=datetime.date.today())
    if not book:
        flash("Не існує книги з таким id")
        session["error"]=True
        return render_template("dashboard.html", error=session.get("error"), user=session)
    person = User.query.get(book.borrowed_by)
    message = Mail(
        from_email=FROM_EMAIL,
        to_emails=person.email,
        subject='Книгу повернено',
        html_content=render_template("emails_return.html", book=book, person=person))
    book.borrowed = False
    book.borrowed_by = None
    book.borrow_start = None
    book.borrow_end = None
    db.session.add(record)
    db.session.commit()
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
    flash("Книгу повернено")
    return redirect("/board")

@app.route("/cancel/<int:id>")
@login_required
def terminal_cancel(id):
    web.cancel(id)
    
@app.route("/")
@login_required
def terminal_home():
    web.index()
    

@app.route("/login", methods=["GET", "POST"])
def terminal_login():
    """Log user in using library card"""
    session["error"] = False
    if request.method == "POST":
        
        #####################
        # Get QR code value #
        guserid = None
        #####################

        user = User.query.filter_by(google_id=guserid).first()
        if not user:
            session["error"] = True
            flash("Користувача не знайдено. Проскануйте код знову.")
            return render_template("terminal-login.html", error=session.get("error"))
        kids = User.query.filter_by(google_id=f"child_of:{user.school_id}").all()
        if not kids:
            session["school_id"] = user.school_id
            session["first"] = user.first
            session["last"] = user.last
            session["email"] = user.email
            session["role"] = user.role
            session["picture"] = user.picture
            session["terminal"] = True
            return redirect("/")
        else:
            family = [user]
            for kid in kids:
                family.append(kid)
            return render_template("user_select.html", family=family)
    return render_template("terminal-login.html", error=session.get("error"))
    

@app.route("/user_select/<int:id>", methods=["POST"])
def terminal_user_select(id):
    web.user_select(id)

@app.route("/logout")
@login_required
def terminal_logout():
    web.logout()

# PWA routes

@app.route('/<path:text>')
def sw(text):
    if text.endswith("service-worker.js"):
        return app.send_static_file('service-worker.js')

if __name__ == "__main__":
    with app.app_context():
        app.run()