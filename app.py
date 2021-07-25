# Built-in libraries
import os
from tempfile import mkdtemp
import datetime

# Downloaded libraries
from sqlalchemy import create_engine, or_, and_, sql
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify, make_response, send_from_directory, url_for
from flask_session import Session
from sqlalchemy.sql.functions import user
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
BORROW_PERIOD = 21 # Borrow period in days
BOOKS_PER_PAGE = 15 # Books per page in pagination

# Initialise database
db.init_app(app)

# Get Google client ID for sign in button
gclient_id = os.environ.get("GOOGLE_CLIENT_ID")

@app.before_request
def before_request():
    if request.url.startswith('http://'):
        url = request.url.replace('http://', 'https://', 1)
        code = 301
        return redirect(url, code=code)

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

@app.route("/profile/<int:id>")
@admin_required
@login_required
def profile(id):
    """Display other's profile"""
    session["error"]=False
    person = User.query.filter_by(school_id=id).first()
    books = Book.query.filter_by(borrowed_by=id).all()
    return render_template("profile.html", user=session, person=person, books=books)

@app.route("/profile/<int:id>/edit", methods=["GET", "POST"])
@admin_required
@login_required
def person_edit(id):
    """Edit some information about profile in the database"""
    session["error"]=False
    person = User.query.filter_by(school_id=id).first()
    if request.method == "POST":
        person.first = request.form.get("first")
        person.last = request.form.get("last")
        person.role = request.form.get("role")
        db.session.commit()
        flash("Редагування успішне")
        return redirect(f"/profile/{id}")
    return render_template("edit_person.html", error=session.get("error"), user=session, person=person)

@app.route("/search", methods=["GET", "POST"])
def search():
    """Lookup a book by criteria"""
    session["error"]=False
    if request.method == "POST":
        if request.form.get("number"):
            number = int(request.form.get("number"))
            return redirect(f"/book/{number}")
        else:
            query = request.form.get("query")
            age = request.form.getlist("age-group")
            if query:
                if translator.detect(query).lang == "en":
                    query = translator.translate(query, dest="uk")
                    query = query.text
                query = "%{}%".format(query)
                query.strip()
            return redirect(url_for("search", q=query, age=age))
    else:
        page = request.args.get('page', 1, type=int)
        query = request.args.get("q")
        age = request.args.getlist("age")
        if query and age:
            books = db.session.query(Book).filter(or_(Book.author.ilike(query), Book.name.ilike(query), Book.description.ilike(query)), Book.age_group.in_(age)).order_by(Book.borrowed).paginate(page=page, per_page=BOOKS_PER_PAGE)
        elif age:
            books = db.session.query(Book).filter(Book.age_group.in_(age)).order_by(Book.borrowed).paginate(page=page, per_page=BOOKS_PER_PAGE)
        else:
            books = db.session.query(Book).order_by(Book.borrowed).paginate(page=page, per_page=BOOKS_PER_PAGE)
        if not books.items:
            session["error"]=True
            flash("Нічого не знайдено")
            return render_template("search.html", error=session.get("error"), user=session)
        book_ids = []
        for book in books.items:
            book_ids.append(book.id)
        scores = {}
        for book in books.items:
            avg_score = db.session.query(sql.func.avg(Review.rating)).filter(Review.book_id == book.id).first()
            print(avg_score)
            scores[book.id] = avg_score
        return render_template("search.html", user=session, books=books, error=session.get("error"), query=query, age=age, scores=scores)

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
        if session["role"] == "adult" or session["role"] == "child":
            book.borrow_end = book.borrow_start + datetime.timedelta(days=BORROW_PERIOD)
        else:
            book.borrow_end = "2069-04-20"
        db.session.commit()
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=session["email"],
            subject='Ми готуємо ваші книги!',
            html_content=render_template("emails_borrow.html", book=book, person=session))
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)
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
    reviews = Review.query.filter_by(book_id=id).all()
    reviewed = False
    for review in reviews:
        if review.by_id == session["school_id"]:
            reviewed = review
    if reviews:
        avg_score = (sum(review.rating for review in reviews) / len(reviews))
    else:
        avg_score = None
    if book.borrowed_by:
        borrower = User.query.filter_by(school_id=book.borrowed_by).first()
    else:
        borrower=None
    return render_template("book.html", user=session, error=session.get("error"), book=book, borrower=borrower, today=datetime.date.today(), score=avg_score, reviews=reviews, reviewed=reviewed)

@app.route("/book/<int:id>/review", methods=["GET", "POST"])
@login_required
def review(id):
    """write a book review"""
    session["error"]=False
    book = Book.query.filter_by(id=id).first()
    review = Review.query.filter_by(book_id=id, by_id=session["school_id"]).first()
    if request.method == "POST":
        if not review:
            review = Review()
            db.session.add(review)
        if request.form.get("anon"):
            review.by_id = None
            review.by_name = None
            review.by_pic = None
        else:
            review.by_id = session["school_id"]
            review.by_name = session["first"] + " " + session["last"]
            review.by_pic = session["picture"]
        review.book_id = id
        review.date = datetime.date.today()
        review.title = request.form.get("title")
        review.rating = request.form.get("rating")
        review.body = request.form.get("body")
        record = Record.query.filter((Record.borrowed_by == session["school_id"]), (Record.book_id == id)).order_by(Record.returned_on.desc()).first()
        if record:
            if request.form.get("finished") == "True":
                record.finished = True
            else:
                record.finished = False
        db.session.commit()
        return redirect(f"/book/{id}")
    return render_template("review.html", user=session, error=session.get("error"), book=book, review=review)

@app.route("/deletereview/<int:id>")
@admin_required
@login_required
def del_rev(id):
    """Delete a problematic review"""
    session["error"]=False
    reports = Report.query.filter_by(review_id=id).all()
    for report in reports:
        db.session.delete(report)
    review = Review.query.get(id)
    review.title = None
    review.body = None
    db.session.commit()
    flash("Відгук видалено")
    return redirect("/mod")

@app.route("/deletereport/<int:id>")
@admin_required
@login_required
def del_rep(id):
    """Delete a report"""
    session["error"]=False
    report = Report.query.get(id)
    db.session.delete(report)
    db.session.commit()
    flash("Скаргу видалено")
    return redirect("/mod")

@app.route("/mod")
@admin_required
@login_required
def mod():
    """Moderation page"""
    reports = db.session.query(Report, Review).join(Review, Review.id == Report.review_id).all()
    return render_template("moderation.html", reports=reports, user=session)

@app.route("/report/<int:id>")
@login_required
def report(id):
    """Report a review"""
    session["error"]=False
    review = Review.query.get(id)
    report = Report(review_id=id, by=session["school_id"])
    db.session.add(report)
    db.session.commit()
    flash("Дякуємо за ваше повідомлення!")
    return redirect(f"/book/{review.book_id}")

@app.route("/markout", methods=["GET", "POST"])
@admin_required
@login_required
def markout():
    """Mark out a book under someone's name"""
    session["error"]=False
    if request.method == "POST":
        person = User.query.filter_by(school_id=request.form.get("person")).first()
        if not person:
            session["error"] = True
            flash("Не дійсний ID клієнта")
            return render_template("markout.html", user=session, error=session.get("error"))
        book = Book.query.filter_by(id=(request.form.get("book"))).first()
        if not book:
            session["error"] = True
            flash("Не дійсний ID книги")
            return render_template("markout.html", user=session, error=session.get("error"))
        if book.borrowed:
            session["error"] = True
            flash("Книга вже позичина")
            return render_template("markout.html", user=session, error=session.get("error"))
        book.borrowed = True
        book.borrowed_by = person.school_id
        book.borrow_start = datetime.date.fromisoformat(request.form.get("start"))
        if person.role == "adult" or person.role == "child":
            book.borrow_end = book.borrow_start + datetime.timedelta(days=BORROW_PERIOD)
        else:
            book.borrow_end = "2069-04-20"
        db.session.commit()
        message = Mail(
            from_email=FROM_EMAIL,
            to_emails=person.email,
            subject='Ви позичили книгу',
            html_content=render_template("emails_markout.html", book=book, admin=session["first"], person=person))
        try:
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)
        return render_template("borrowed.html", book=book, user=session, error=session.get("error"), origin="markout")
    return render_template("markout.html", user=session, error=session.get("error"))

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
    """Display user's homepage with all their borrowed books.
    If user was redirected through login page, and they have associated children to their account, lets user select whose account to use.
    """
    if session["kid_select"]:
        # This reads whether we need to select a clild acount or proceed as usual. Value is passed from "/login".
        session["kid_select"] = False
        user = user = User.query.filter_by(google_id=session["googleinfo"]["sub"]).first()
        kids = User.query.filter_by(google_id=f"child_of:{session['school_id']}").all()
        family = [user]
        session["allowed_ids"] = [user.school_id]
        for kid in kids:
            family.append(kid)
            session["allowed_ids"].append(kid.school_id)
        return render_template("user_select.html", family=family)
    # From here, normal operation of the route
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
    """Log user in using Google sign-in"""
    session["error"] = False
    if request.method == "POST":
        token = request.form["idtoken"]
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), gclient_id)

            # ID token is valid. Get the user's Google Account ID from the decoded token.
            session["googleinfo"] = idinfo
            guserid = session["googleinfo"]["sub"]
        except ValueError:
            # Invalid token
            pass
        user = User.query.filter_by(google_id=guserid).first()
        if not user:
            user = User(first=session["googleinfo"]["given_name"], last=session["googleinfo"]["family_name"], email=session["googleinfo"]["email"], google_id=guserid, picture=session["googleinfo"]["picture"])
            db.session.add(user)
            db.session.commit()
            user = User.query.filter_by(google_id=guserid).first()
        else:
            # Update existing info
            #user.first = idinfo["given_name"] # Probably will leave name editing up to staff
            #user.last=idinfo["family_name"]
            user.picture=session["googleinfo"]["picture"]
            db.session.commit()
        kids = User.query.filter_by(google_id=f"child_of:{user.school_id}").first()
        if not kids:
            session["school_id"] = user.school_id
            session["first"] = user.first
            session["last"] = user.last
            session["email"] = user.email
            session["role"] = user.role
            session["picture"] = user.picture
            session["kid_select"] = False
            return # Return nothing because this POST request is processed in the background and is not visual (JS will redirect)
        else:
            session["kid_select"] = True
            return # Return nothing because this POST request is processed in the background and is not visual (JS will redirect)
    return render_template("login.html", error=session.get("error"), google_signin_client_id=gclient_id, user=session)

@app.route("/user_select/<int:id>", methods=["POST"])
def user_select(id):
    if not session["kid_select"]:
        # Check if user has permission to log in to kid accounts
        flash("kid_select flag not set")
        session["error"] = True
        return render_template("login.html", error=session.get("error"), google_signin_client_id=gclient_id, user=session)
    else:
        session["kid_select"] = False
    if id not in session["allowed_ids"]:
        # Check if passed id is in user's family
        flash("Passed user ID not in the family")
        session["error"] = True
        return render_template("login.html", error=session.get("error"), google_signin_client_id=gclient_id, user=session)
    user = User.query.get(id)
    session["school_id"] = user.school_id
    session["first"] = user.first
    session["last"] = user.last
    session["email"] = user.email
    session["role"] = user.role
    session["picture"] = user.picture
    return redirect("/")

@app.route("/add_child", methods=["GET", "POST"])
@login_required
def add_child():
    """Add a child account"""
    session["error"] = False
    if request.method == "GET":
        return render_template("add_child.html", error=session.get("error"), user=session)
    else:
        if 'pic-own' in request.files:
            file = request.files['pic-own']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_result = cloudinary.uploader.upload(file)
                pic = upload_result["url"]
        else:
            pic = request.form.get("default-pfp")
        first = request.form.get("first")
        last = request.form.get("last")
        email = request.form.get("email")
        if User.query.filter_by(email=email).first():
            session.error = True
            flash("Дитину з такою електронною адресою вже зареєстровано")
            return render_template("add_child.html", error=session.get("error"), user=session)
        child = User(first=first, last=last, email=email, pic=pic, google_id=f"child_of:{session.school_id}", role="child")
        db.session.add(child)
        db.session.commit()
        flash('Дитину зареєстровано. Натисніть "Вихід" у налаштуваннях щоб змінити профіль.')
        return redirect("/")

@app.route("/logout")
@login_required
def logout():
    """Logout user"""
    flash("Сессія завершена")
    session.clear()
    return redirect("/login")

# Commands

@app.cli.command("return_reminder")
def return_reminder():
    if datetime.datetime.today().weekday() == 5:
        books = db.session.query(Book).filter(Book.borrow_end <= datetime.date.today())
        borrowers = set()
        for book in books:
            borrowers.add(book.borrowed_by)
        violators = db.session.query(User).filter(User.school_id.in_(borrowers))
        for person in violators:
            owing = []
            for book in books:
                if book.borrowed_by == person.school_id:
                    owing.append(book)
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=person.email,
                subject='В вас наші книги',
                html_content=render_template("emails_late.html", owing=owing, person=person)
            )
            try:
                sg = SendGridAPIClient(SENDGRID_API_KEY)
                response = sg.send(message)
                print(response.status_code)
                print(response.body)
                print(response.headers)
            except Exception as e:
                print(e.message)
    return

# PWA routes

@app.route('/<path:text>')
def sw(text):
    if text.endswith("service-worker.js"):
        return app.send_static_file('service-worker.js')

if __name__ == "__main__":
    with app.app_context():
        app.run()