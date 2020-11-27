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

# Configure app
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialise database
engine = create_engine(os.getenv("DATABASE_URL")) # Push the database url to environment using [export DATABASE_URL="the url"] on MAC/Linux or [set DATABASE_URL="the url"] on Windows
db = scoped_session(sessionmaker(bind=engine))
if not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL not set")

# Get Google client ID for sign in button
gclient_id = os.environ.get("GOOGLE_CLIENT_ID")
#if not gclient_id:
#    raise RuntimeError("GOOGLE_CLIENT_ID not set")

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
        user = db.execute("SELECT * FROM users WHERE google_id = (?)", guserid).fetchone()
        if not user:
            db.execute("INSERT INTO users (first, last, email, google_id) VALUES (?, ?, ?, ?)", idinfo["given_name"], idinfo["family_name"], idinfo["email"], guserid)
            db.commit()
            user = db.execute("SELECT * FROM users WHERE google_id = (?)", guserid).fetchone()
        session["user_id"] = user["school_id"]
        return redirect("/")
    return render_template("login.html", error=error, google_signin_client_id=gclient_id)