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