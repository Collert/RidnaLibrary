from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__="users"
    school_id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String, nullable=False)
    last = db.Column(db.String, nullable=False)
    email = db.Column(db.String, nullable=False)
    google_id = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False, default="student")
    picture = db.Column(db.String, nullable=False, default="/static/nopic.jpg")

class Book(db.Model):
    __tablename__="inventory"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    age_group = db.Column(db.string, nullable=False)
    borrowed = db.Column(db.Boolean, nullable=False, default=False)
    borrowed_by = db.Column(db.Integer, db.ForeignKey("users.school_id"), nullable=True, default=None)
    borrow_start = db.Column(db.Date, nullable=True, default=None)
    borrow_end = db.Column(db.Date, nullable=True, default=None)