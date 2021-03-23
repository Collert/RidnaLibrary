import datetime

from flask import redirect, session, flash
from functools import wraps

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

def create_card(user_id):
    """Generate library card (QR code) from user's id"""
    return f"https://chart.googleapis.com/chart?chs=200x200&cht=qr&chl={user_id}"
    

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