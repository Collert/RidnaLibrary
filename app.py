# Built-in libraries
import os
from tempfile import mkdtemp

# Downloaded libraries
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from google.oauth2 import id_token
from google.auth.transport import requests

# Custom libraries
from functions import login_required
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

@app.route("/")
def index():
    return render_template("home.html")

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
            db.sesssion.commit()
            user = User.query.filter_by(google_id=guserid).first()
        session["user_id"] = user.school_id
        session["first"] = user.first
        session["last"] = user.last
        session["email"] = user.email
        session["role"] = user.role
        session["pfp"] = user.picture
        return redirect("/")
    return render_template("login.html", error=error, google_signin_client_id=gclient_id)

if __name__ == "__main__":
    with app.app_context():
        app.run()