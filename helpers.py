import requests

from cs50 import SQL
from flask import redirect, render_template, session
from functools import wraps

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

db = SQL("sqlite:///Database/finance.db")


def apg(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def check_budget_warning(category, amount):
    """Check if transaction exceeds budget and send warning"""
    current_spending = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ?
        AND type = 'EXPENSE'
        AND strftime('%Y-%m', time) = strftime('%Y-%m', 'now')
    """, session["user_id"])[0]['total']
    
    current_spending += amount
    
    budget = db.execute("""
        SELECT amount
        FROM budgets
        WHERE user_id = ?
        AND period = 'MONTHLY'
        AND is_active = 1
    """, session["user_id"])
    
    if budget:
        budget_amount = budget[0]['amount']
        percentage = (current_spending / budget_amount) * 100
        
        if percentage >= 100:
            flash(f"⚠️ Warning: You've exceeded your budget by ${current_spending - budget_amount:.2f}!", "warning")
        elif percentage >= 80:
            flash(f"⚠️ Warning: You've used {percentage:.0f}% of your budget!", "warning")
