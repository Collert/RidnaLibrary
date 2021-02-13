from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __bind_key__="basic_data"
    __tablename__="users"
    school_id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String, nullable=False)
    last = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    google_id = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="student")
    picture = db.Column(db.String, nullable=False, default="/static/nopic.jpg")

class Book(db.Model):
    __bind_key__="basic_data"
    __tablename__="inventory"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    age_group = db.Column(db.String, nullable=False)
    borrowed = db.Column(db.Boolean, nullable=False, default=False)
    borrowed_by = db.Column(db.Integer, db.ForeignKey("users.school_id"), nullable=True, default=None)
    borrow_start = db.Column(db.Date, nullable=True, default=None)
    borrow_end = db.Column(db.Date, nullable=True, default=None)
    image = db.Column(db.String, nullable=True)

class Record(db.Model):
    __bind_key__="big_data"
    __tablename__="records"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    borrowed_by = db.Column(db.Integer, nullable=False)
    borrowed_on = db.Column(db.Date, nullable=False)
    returned_on = db.Column(db.Date, nullable=False)
    finished = db.Column(db.Boolean, nullable=False, default=True)

class Review(db.Model):
    __bind_key__="reviews"
    __tablename__="reviews"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, nullable=False)
    by_id = db.Column(db.Integer, nullable=True)
    date = db.Column(db.Date, nullable=False)
    title = db.Column(db.String, nullable=True)
    rating = db.Column(db.Integer, nullable=False)
    body = db.Column(db.String, nullable=True)
    by_name = db.Column(db.String, nullable=True)
    by_pic = db.Column(db.String, nullable=True)

class Report(db.Model):
    __bind_key__="reviews"
    __tablename__="reports"
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, nullable=False)
    by = db.Column(db.Integer, nullable=False)