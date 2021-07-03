import os
import datetime

from flask import redirect, render_template, request, session, url_for, flash
from functools import wraps
from google.auth.transport.requests import Request
#import pickle
#from google_auth_oauthlib.flow import Flow, InstalledAppFlow
#from googleapiclient.discovery import build
#from google.oauth2.credentials import Credentials
#from dotenv import load_dotenv

#load_dotenv()
#SCOPES = ['https://www.googleapis.com/auth/calendar.events']

def login_required(f):
    """
    Decorate routes to require login.
    
    Documentation here:
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("school_id") is None:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Decorate routes to require admin previleges.
    Documentation here:
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("role") != "admin":
            session["error"]=True
            flash("Not enough previleges")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def nextSat():
    """Calculate next Saturday from today"""
    today = datetime.date.today()
    if today.weekday() == 5 and datetime.datetime.now().time().hour < 16:
        return today
    else:
        saturday = today + datetime.timedelta( (5-today.weekday()) % 7 )
        return saturday

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#def get_calendar_service():
#    """
#    Gets Google calendar's "service"
#    """
#    creds = None
#    # The file token.json stores the user's access and refresh tokens, and is
#    # created automatically when the authorization flow completes for the first
#    # time.
#    if os.path.exists('token.json'):
#        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#    # If there are no (valid) credentials available, let the user log in.
#    if not creds or not creds.valid:
#        if creds and creds.expired and creds.refresh_token:
#            creds.refresh(Request())
#        else:
#            flow = InstalledAppFlow.from_client_secrets_file(
#                'credentials.json', SCOPES)
#            creds = flow.run_local_server(port=0)
#        # Save the credentials for the next run
#        with open('token.json', 'w') as token:
#            token.write(creds.to_json())
#
#    service = build('calendar', 'v3', credentials=creds)
#    return service
