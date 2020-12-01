import os
import datetime

from flask import redirect, render_template, request, session, url_for
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.
    
    Documentation here:
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for('/login', next=request.url))
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
        if session.get("role") is not "admin":
            error=True
            flash("Not enough previleges")
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def nextSat():
    """Calculate next Saturday from today"""
    today = datetime.date.today()
    if today.weekday() == 5:
        return today
    else:
        saturday = today + datetime.timedelta( (5-today.weekday()) % 7 )
        return saturday