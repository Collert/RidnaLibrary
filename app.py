import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, flash, redirect, render_template, request, session, jsonify
from flask_session import Session
from tempfile import mkdtemp

from functions import login_required

# Configure app
app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialise database
#engine = create_engine(os.getenv("DB_URL")) # Push the database url to environment using [export DB_URL="the url"] on MAC/Linux or [set DB_URL="the url"] on Windows
#db = scoped_session(sessionmaker(bind=engine))
#if not os.environ.get("DB_URL"):
#    raise RuntimeError("DB_URL not set")

@app.route("/")
def index():
    return render_template("home.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    error = False
    #if request.method == "POST":

    return render_template("login.html")