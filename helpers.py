import requests
from datetime import datetime, timedelta

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
    user_id = session["user_id"]
    monthly_budget = db.execute("""
        SELECT amount, period, start_date
        FROM budgets
        WHERE user_id = ?
        AND period = 'MONTHLY'
        AND is_active = 1
    """, user_id)
    
    if monthly_budget:
        budget_amount = monthly_budget[0]['amount']
        
        current_spending = db.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ?
            AND type = 'EXPENSE'
            AND strftime('%Y-%m', time) = strftime('%Y-%m', 'now')
        """, user_id)
        
        total = current_spending[0]['total'] + amount
        percentage = (total / budget_amount) * 100
        remaining = budget_amount - total
        
        if percentage >= 100:
            flash(f"🚨 Budget Alert: You've exceeded your monthly budget by ${abs(remaining):.2f}!", "danger")
        elif percentage >= 90:
            flash(f"⚠️ Budget Warning: You've used {percentage:.0f}% of your monthly budget. Only ${remaining:.2f} remaining!", "warning")
        elif percentage >= 75:
            flash(f"💡 Budget Notice: You've used {percentage:.0f}% of your monthly budget (${remaining:.2f} left).", "info")
        
        return
    
    weekly_budget = db.execute("""
        SELECT amount, period
        FROM budgets
        WHERE user_id = ?
        AND period = 'WEEKLY'
        AND is_active = 1
    """, user_id)
    
    if weekly_budget:
        budget_amount = weekly_budget[0]['amount']
        
        current_spending = db.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ?
            AND type = 'EXPENSE'
            AND strftime('%Y-%W', time) = strftime('%Y-%W', 'now')
        """, user_id)
        
        total = current_spending[0]['total'] + amount
        percentage = (total / budget_amount) * 100
        remaining = budget_amount - total
        
        if percentage >= 100:
            flash(f"🚨 Budget Alert: You've exceeded your weekly budget by ${abs(remaining):.2f}!", "danger")
        elif percentage >= 90:
            flash(f"⚠️ Budget Warning: You've used {percentage:.0f}% of your weekly budget. Only ${remaining:.2f} remaining!", "warning")
        elif percentage >= 75:
            flash(f"💡 Budget Notice: You've used {percentage:.0f}% of your weekly budget (${remaining:.2f} left).", "info")
        
        return
    
    yearly_budget = db.execute("""
        SELECT amount, period
        FROM budgets
        WHERE user_id = ?
        AND period = 'YEARLY'
        AND is_active = 1
    """, user_id)
    
    if yearly_budget:
        budget_amount = yearly_budget[0]['amount']
        
        current_spending = db.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM transactions
            WHERE user_id = ?
            AND type = 'EXPENSE'
            AND strftime('%Y', time) = strftime('%Y', 'now')
        """, user_id)
        
        total = current_spending[0]['total'] + amount
        percentage = (total / budget_amount) * 100
        remaining = budget_amount - total
        
        if percentage >= 100:
            flash(f"🚨 Budget Alert: You've exceeded your yearly budget by ${abs(remaining):.2f}!", "danger")
        elif percentage >= 90:
            flash(f"⚠️ Budget Warning: You've used {percentage:.0f}% of your yearly budget. Only ${remaining:.2f} remaining!", "warning")
        elif percentage >= 75:
            flash(f"💡 Budget Notice: You've used {percentage:.0f}% of your yearly budget (${remaining:.2f} left).", "info")


def get_histogram_data(user_id, view, start_date, end_date, labels):
    """Generate histogram data based on view type"""
    user_id = session["user_id"]
    
    if view == 'daily':
        income_data = []
        expense_data = []
        current = start_date
        
        for label in labels:
            day_end = current + timedelta(days=1)
            
            income = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'INCOME'
                AND time >= ? AND time < ?
            """, user_id, current, day_end)[0]['total']
            
            expense = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'EXPENSE'
                AND time >= ? AND time < ?
            """, user_id, current, day_end)[0]['total']
            
            income_data.append(float(income))
            expense_data.append(float(expense))
            current = day_end
            
    elif view == 'weekly':
        income_data = []
        expense_data = []
        
        for week_num in range(len(labels)):
            week_start = start_date + timedelta(weeks=week_num)
            week_end = week_start + timedelta(days=7)
            
            income = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'INCOME'
                AND time >= ? AND time < ?
            """, user_id, week_start, week_end)[0]['total']
            
            expense = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'EXPENSE'
                AND time >= ? AND time < ?
            """, user_id, week_start, week_end)[0]['total']
            
            income_data.append(float(income))
            expense_data.append(float(expense))
            
    elif view == 'monthly':
        income_data = []
        expense_data = []
        
        for month in range(1, 13):
            month_start = start_date.replace(month=month, day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            income = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'INCOME'
                AND strftime('%Y-%m', time) = ?
            """, user_id, month_start.strftime('%Y-%m'))[0]['total']
            
            expense = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'EXPENSE'
                AND strftime('%Y-%m', time) = ?
            """, user_id, month_start.strftime('%Y-%m'))[0]['total']
            
            income_data.append(float(income))
            expense_data.append(float(expense))
            
    else:  # annual
        income_data = []
        expense_data = []
        
        for year_label in labels:
            income = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'INCOME'
                AND strftime('%Y', time) = ?
            """, user_id, year_label)[0]['total']
            
            expense = db.execute("""
                SELECT COALESCE(SUM(amount), 0) as total
                FROM transactions
                WHERE user_id = ? AND type = 'EXPENSE'
                AND strftime('%Y', time) = ?
            """, user_id, year_label)[0]['total']
            
            income_data.append(float(income))
            expense_data.append(float(expense))
    
    return {
        'labels': labels,
        'income': income_data,
        'expenses': expense_data
    }


def calculate_trends(user_id):
    """Calculate spending trends"""
    # Compare this month vs last month
    today = datetime.now()
    this_month_start = today.replace(day=1)
    last_month_end = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)
    
    this_month = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
    """, user_id, this_month_start)[0]['total']
    
    last_month = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ? AND time < ?
    """, user_id, last_month_start, this_month_start)[0]['total']
    
    if last_month > 0:
        change = ((this_month - last_month) / last_month) * 100
    else:
        change = 0 if this_month == 0 else 100
    
    # Top spending category
    top_category = db.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
        GROUP BY category
        ORDER BY total DESC
        LIMIT 1
    """, user_id, this_month_start)
    
    return {
        'monthly_change': round(change, 1),
        'top_category': top_category[0] if top_category else None
    }
