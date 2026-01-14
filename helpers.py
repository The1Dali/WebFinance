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

def get_spending_trends(user_id, start_date, end_date):
    """Get daily spending trends for line chart"""
    trends = db.execute("""
        SELECT 
            DATE(time) as date,
            SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END) as expenses,
            SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END) as income
        FROM transactions
        WHERE user_id = ? AND time >= ? AND time <= ?
        GROUP BY DATE(time)
        ORDER BY date
    """, user_id, start_date, end_date)

    # Fill in missing dates with 0
    all_dates = []
    current = start_date
    while current <= end_date:
        all_dates.append(current.strftime('%Y-%m-%d'))
        current += timedelta(days=1)

    trend_map = {t['date']: t for t in trends}

    return {
        'labels': all_dates,
        'income': [float(trend_map.get(d, {}).get('income', 0)) for d in all_dates],
        'expenses': [float(trend_map.get(d, {}).get('expenses', 0)) for d in all_dates]
    }


def get_category_analysis(user_id, start_date, end_date):
    """Detailed category breakdown with trends"""
    categories = db.execute("""
        SELECT 
            category,
            SUM(amount) as total,
            COUNT(*) as transaction_count,
            AVG(amount) as avg_amount,
            MAX(amount) as max_amount,
            MIN(amount) as min_amount
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ? AND time <= ?
        GROUP BY category
        ORDER BY total DESC
    """, user_id, start_date, end_date)
    
    total_spending = sum(c['total'] for c in categories)
    
    for cat in categories:
        cat['percentage'] = (cat['total'] / total_spending * 100) if total_spending > 0 else 0
        cat['total'] = float(cat['total'])
        cat['avg_amount'] = float(cat['avg_amount'])
        cat['max_amount'] = float(cat['max_amount'])
        cat['min_amount'] = float(cat['min_amount'])
    
    return categories


def get_period_comparison(user_id, start_date, end_date):
    """Compare current period with previous period"""
    period_length = (end_date - start_date).days
    prev_start = start_date - timedelta(days=period_length)
    prev_end = start_date - timedelta(days=1)
    
    # Current period
    current = db.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as expense
        FROM transactions
        WHERE user_id = ? AND time >= ? AND time <= ?
    """, user_id, start_date, end_date)[0]
    
    # Previous period
    previous = db.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as expense
        FROM transactions
        WHERE user_id = ? AND time >= ? AND time <= ?
    """, user_id, prev_start, prev_end)[0]
    
    # Calculate changes
    income_change = ((current['income'] - previous['income']) / previous['income'] * 100) if previous['income'] > 0 else 0
    expense_change = ((current['expense'] - previous['expense']) / previous['expense'] * 100) if previous['expense'] > 0 else 0
    
    return {
        'current_income': float(current['income']),
        'current_expense': float(current['expense']),
        'previous_income': float(previous['income']),
        'previous_expense': float(previous['expense']),
        'income_change': round(income_change, 1),
        'expense_change': round(expense_change, 1)
    }


def get_time_analysis(user_id, start_date, end_date):
    """Analyze spending patterns by day of week and time of day"""
    
    # By day of week
    by_weekday = db.execute("""
        SELECT 
            CASE CAST(strftime('%w', time) AS INTEGER)
                WHEN 0 THEN 'Sunday'
                WHEN 1 THEN 'Monday'
                WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday'
                WHEN 4 THEN 'Thursday'
                WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END as weekday,
            CAST(strftime('%w', time) AS INTEGER) as day_num,
            COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ? AND time <= ?
        GROUP BY day_num
        ORDER BY day_num
    """, user_id, start_date, end_date)
    
    weekday_map = {day['weekday']: float(day['total']) for day in by_weekday}
    weekdays = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    return {
        'weekday_labels': weekdays,
        'weekday_data': [weekday_map.get(day, 0) for day in weekdays]
    }


def calculate_financial_health(user_id, start_date, end_date):
    """Calculate overall financial health score (0-100)"""
    
    stats = db.execute("""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as income,
            COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as expense
        FROM transactions
        WHERE user_id = ? AND time >= ? AND time <= ?
    """, user_id, start_date, end_date)[0]
    
    income = float(stats['income'])
    expense = float(stats['expense'])
    
    # Score components (out of 100)
    score = 0
    breakdown = {}
    
    # 1. Savings Rate (40 points max)
    if income > 0:
        savings_rate = (income - expense) / income
        savings_points = min(savings_rate * 100, 40)  # Cap at 40
        score += savings_points
        breakdown['savings'] = round(savings_points, 1)
    else:
        breakdown['savings'] = 0
    
    # 2. Budget Adherence (30 points max)
    budget = db.execute("""
        SELECT amount FROM budgets
        WHERE user_id = ? AND period = 'MONTHLY' AND is_active = 1
    """, user_id)
    
    if budget:
        budget_amount = budget[0]['amount']
        monthly_expense = expense / ((end_date - start_date).days / 30)
        adherence = 1 - abs(monthly_expense - budget_amount) / budget_amount
        budget_points = max(adherence * 30, 0)
        score += budget_points
        breakdown['budget'] = round(budget_points, 1)
    else:
        breakdown['budget'] = 0
    
    # 3. Income Consistency (30 points max)
    income_transactions = db.execute("""
        SELECT COUNT(*) as count
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        AND time >= ? AND time <= ?
    """, user_id, start_date, end_date)[0]['count']
    
    if income_transactions >= 3:
        consistency_points = 30
    elif income_transactions >= 1:
        consistency_points = income_transactions * 10
    else:
        consistency_points = 0
    
    score += consistency_points
    breakdown['consistency'] = consistency_points
    
    return {
        'score': round(score, 1),
        'breakdown': breakdown,
        'rating': 'Excellent' if score >= 80 else 'Good' if score >= 60 else 'Fair' if score >= 40 else 'Needs Improvement'
    }


def get_recurring_analysis(user_id):
    """Analyze recurring transactions"""
    recurring = db.execute("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(amount), 0) as total,
            type
        FROM recurring_transactions
        WHERE user_id = ? AND is_active = 1
        GROUP BY type
    """, user_id)
    
    stats = {
        'income_count': 0,
        'income_total': 0,
        'expense_count': 0,
        'expense_total': 0
    }
    
    for r in recurring:
        if r['type'] == 'INCOME':
            stats['income_count'] = r['count']
            stats['income_total'] = float(r['total'])
        else:
            stats['expense_count'] = r['count']
            stats['expense_total'] = float(r['total'])
    
    return stats

def calculate_next_date(current_date, frequency):
    """Calculate the next occurrence date based on frequency"""
    
    if frequency == 'DAILY':
        return current_date + timedelta(days=1)
    elif frequency == 'WEEKLY':
        return current_date + timedelta(weeks=1)
    elif frequency == 'BIWEEKLY':
        return current_date + timedelta(weeks=2)
    elif frequency == 'MONTHLY':
        # Handle month-end edge cases
        month = current_date.month
        year = current_date.year
        day = current_date.day
        
        # Move to next month
        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
        
        # Handle day overflow (e.g., Jan 31 -> Feb 31 doesn't exist)
        import calendar
        max_day = calendar.monthrange(year, month)[1]
        day = min(day, max_day)
        
        return current_date.replace(year=year, month=month, day=day)
        
    elif frequency == 'YEARLY':
        # Handle leap year edge case (Feb 29)
        year = current_date.year + 1
        month = current_date.month
        day = current_date.day
        
        # Feb 29 in non-leap year becomes Feb 28
        if month == 2 and day == 29:
            import calendar
            if not calendar.isleap(year):
                day = 28
        
        return current_date.replace(year=year, month=month, day=day)
    else:
        return current_date + timedelta(days=30)

def process_recurring_transactions():
    """Create transactions from recurring templates that are due"""
    today = datetime.now().date()
    
    # Get all active recurring transactions that are due
    due_recurring = db.execute("""
        SELECT id, user_id, name, amount, type, category, notes, frequency, next_occurrence
        FROM recurring_transactions
        WHERE is_active = 1
        AND next_occurrence <= ?
    """, today)
    
    for rt in due_recurring:
        try:
            # Create the actual transaction
            db.execute("""
                INSERT INTO transactions 
                (user_id, name, amount, type, category, notes, is_recurring, recurring_template_id, time)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            """, 
                rt['user_id'],
                rt['name'],
                rt['amount'],
                rt['type'],
                rt['category'],
                rt['notes'],
                rt['id'],
                rt['next_occurrence']
            )
            
            # Calculate and update next occurrence
            current_date = datetime.strptime(str(rt['next_occurrence']), '%Y-%m-%d').date()
            next_date = calculate_next_date(current_date, rt['frequency'])
            
            db.execute("""
                UPDATE recurring_transactions
                SET next_occurrence = ?
                WHERE id = ?
            """, next_date.strftime('%Y-%m-%d'), rt['id'])
            
            print(f"Created recurring transaction: {rt['name']} for {rt['next_occurrence']}")
            
        except Exception as e:
            print(f"Error creating recurring transaction {rt['id']}: {e}")
            continue
    
    return len(due_recurring)

def load_whisper_model():
    """
    Load Whisper model at startup
    This runs once when Flask starts
    """
    global whisper_model
    
    try:
        print("Loading Whisper model... (this may take 10-30 seconds on first run)")
        
        if USE_FASTER_WHISPER:
            from faster_whisper import WhisperModel
            
            whisper_model = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type="int8", 
                num_workers=2 
            )
            print(f"Faster-Whisper '{WHISPER_MODEL}' model loaded successfully!")
        else:
            import whisper
            whisper_model = whisper.load_model(WHISPER_MODEL)
            print(f"Whisper '{WHISPER_MODEL}' model loaded successfully!")
        
        return True
            
    except ImportError as e:
        print(f"Whisper not installed. Run: pip install faster-whisper")
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Failed to load Whisper model: {e}")
        return False

def get_user_financial_data(user_id):
    """Fetch user's financial data from YOUR database"""
    
    try:
        now = datetime.now()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_week_start = now - timedelta(days=now.weekday())
        current_year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        active_budget = db.execute("""
            SELECT amount, period, start_date, end_date
            FROM budgets
            WHERE user_id = ? AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 1
        """, user_id)
        
        budget_info = None
        if active_budget:
            budget_info = {
                'total': active_budget[0]['amount'],
                'period': active_budget[0]['period'],
                'start_date': active_budget[0]['start_date'],
                'end_date': active_budget[0]['end_date']
            }
        
        category_budgets = db.execute("""
            SELECT category, limit_amount
            FROM category_budgets
            WHERE user_id = ? AND is_active = 1
        """, user_id)
        
        category_budget_dict = {cb['category']: cb['limit_amount'] for cb in category_budgets}
        
        monthly_stats = db.execute("""
            SELECT 
                type,
                category,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions
            WHERE user_id = ? AND time >= ?
            GROUP BY type, category
        """, user_id, current_month_start.strftime('%Y-%m-%d %H:%M:%S'))
        
        monthly_income = sum(s['total'] for s in monthly_stats if s['type'] == 'INCOME')
        monthly_expenses = sum(s['total'] for s in monthly_stats if s['type'] == 'EXPENSE')
        
        income_by_category = {s['category']: s['total'] for s in monthly_stats if s['type'] == 'INCOME'}
        expenses_by_category = {s['category']: s['total'] for s in monthly_stats if s['type'] == 'EXPENSE'}
        
        weekly_stats = db.execute("""
            SELECT 
                type,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ? AND time >= ?
            GROUP BY type
        """, user_id, current_week_start.strftime('%Y-%m-%d %H:%M:%S'))
        
        weekly_income = next((s['total'] for s in weekly_stats if s['type'] == 'INCOME'), 0)
        weekly_expenses = next((s['total'] for s in weekly_stats if s['type'] == 'EXPENSE'), 0)
        
        yearly_stats = db.execute("""
            SELECT 
                type,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ? AND time >= ?
            GROUP BY type
        """, user_id, current_year_start.strftime('%Y-%m-%d %H:%M:%S'))
        
        yearly_income = next((s['total'] for s in yearly_stats if s['type'] == 'INCOME'), 0)
        yearly_expenses = next((s['total'] for s in yearly_stats if s['type'] == 'EXPENSE'), 0)
        
        all_transactions = db.execute("""
            SELECT type, SUM(amount) as total
            FROM transactions
            WHERE user_id = ?
            GROUP BY type
        """, user_id)
        
        total_income = next((t['total'] for t in all_transactions if t['type'] == 'INCOME'), 0)
        total_expenses = next((t['total'] for t in all_transactions if t['type'] == 'EXPENSE'), 0)
        total_balance = total_income - total_expenses
        
        recent_transactions = db.execute("""
            SELECT name, amount, type, category, time
            FROM transactions
            WHERE user_id = ?
            ORDER BY time DESC
            LIMIT 10
        """, user_id)
        
        recurring = db.execute("""
            SELECT name, amount, type, category, frequency, next_occurrence
            FROM recurring_transactions
            WHERE user_id = ? AND is_active = 1
            ORDER BY next_occurrence ASC
        """, user_id)
        
        three_months_ago = (now - timedelta(days=90)).strftime('%Y-%m-%d %H:%M:%S')
        monthly_trend = db.execute("""
            SELECT 
                strftime('%Y-%m', time) as month,
                type,
                SUM(amount) as total
            FROM transactions
            WHERE user_id = ? AND time >= ?
            GROUP BY month, type
            ORDER BY month DESC
        """, user_id, three_months_ago)
        
        top_expenses = db.execute("""
            SELECT 
                category,
                SUM(amount) as total,
                COUNT(*) as count
            FROM transactions
            WHERE user_id = ? AND type = 'EXPENSE' AND time >= ?
            GROUP BY category
            ORDER BY total DESC
            LIMIT 5
        """, user_id, current_month_start.strftime('%Y-%m-%d %H:%M:%S'))
        
        budget_spent = monthly_expenses
        budget_status = None
        if budget_info and budget_info['period'] == 'MONTHLY':
            budget_remaining = budget_info['total'] - budget_spent
            budget_percentage = (budget_spent / budget_info['total'] * 100) if budget_info['total'] > 0 else 0
            budget_status = {
                'spent': budget_spent,
                'remaining': budget_remaining,
                'percentage': round(budget_percentage, 1),
                'is_over': budget_spent > budget_info['total']
            }
        
        category_budget_status = {}
        for category, limit in category_budget_dict.items():
            spent = expenses_by_category.get(category, 0)
            category_budget_status[category] = {
                'limit': limit,
                'spent': spent,
                'remaining': limit - spent,
                'percentage': round((spent / limit * 100) if limit > 0 else 0, 1),
                'is_over': spent > limit
            }
        
        return {
            'balance': {
                'total': total_balance,
                'total_income': total_income,
                'total_expenses': total_expenses
            },
            'monthly': {
                'income': monthly_income,
                'expenses': monthly_expenses,
                'net': monthly_income - monthly_expenses,
                'income_by_category': income_by_category,
                'expenses_by_category': expenses_by_category
            },
            'weekly': {
                'income': weekly_income,
                'expenses': weekly_expenses,
                'net': weekly_income - weekly_expenses
            },
            'yearly': {
                'income': yearly_income,
                'expenses': yearly_expenses,
                'net': yearly_income - yearly_expenses
            },
            'budget': budget_info,
            'budget_status': budget_status,
            'category_budgets': category_budget_dict,
            'category_budget_status': category_budget_status,
            'recent_transactions': [
                {
                    'name': t['name'],
                    'amount': t['amount'],
                    'type': t['type'],
                    'category': t['category'],
                    'date': t['time']
                } for t in recent_transactions
            ],
            'recurring_transactions': [
                {
                    'name': r['name'],
                    'amount': r['amount'],
                    'type': r['type'],
                    'category': r['category'],
                    'frequency': r['frequency'],
                    'next_date': r['next_occurrence']
                } for r in recurring
            ],
            'top_expense_categories': [
                {
                    'category': e['category'],
                    'total': e['total'],
                    'count': e['count']
                } for e in top_expenses
            ],
            'trends': {
                'monthly': monthly_trend
            },
            'timestamp': now.isoformat()
        }
        
    except Exception as e:
        print(f"Error gathering financial data: {e}")
        import traceback
        traceback.print_exc()
        return {}

def create_financial_prompt(user_message, financial_context):
    """ Create a detailed prompt for the AI model with financial context """
    
    budget_text = "No active budget set."
    if financial_context.get('budget_status'):
        bs = financial_context['budget_status']
        budget_text = f"""Active Monthly Budget: ${financial_context['budget']['total']:.2f}
    - Spent: ${bs['spent']:.2f} ({bs['percentage']}%)
    - Remaining: ${bs['remaining']:.2f}
    - Status: {'OVER BUDGET' if bs['is_over'] else 'Within budget'}"""
    
    category_budget_text = ""
    if financial_context.get('category_budget_status'):
        category_budget_text = "Category Budget Status:\n"
        for cat, status in financial_context['category_budget_status'].items():
            category_budget_text += f"- {cat}: ${status['spent']:.2f} / ${status['limit']:.2f} ({status['percentage']}%) "
            category_budget_text += f"{'⚠️ OVER' if status['is_over'] else '✓'}\n"
    
    top_expenses_text = ""
    if financial_context.get('top_expense_categories'):
        top_expenses_text = "Top Expense Categories This Month:\n"
        for exp in financial_context['top_expense_categories']:
            top_expenses_text += f"- {exp['category']}: ${exp['total']:.2f} ({exp['count']} transactions)\n"
    
    recent_trans_text = ""
    if financial_context.get('recent_transactions'):
        recent_trans_text = "Recent Transactions:\n"
        for trans in financial_context['recent_transactions'][:5]:
            sign = "+" if trans['type'] == 'INCOME' else "-"
            recent_trans_text += f"- {trans['name']}: {sign}${trans['amount']:.2f} ({trans['category']}) on {trans['date'][:10]}\n"
    
    recurring_text = ""
    if financial_context.get('recurring_transactions'):
        recurring_text = "Upcoming Recurring Transactions:\n"
        for rec in financial_context['recurring_transactions'][:3]:
            recurring_text += f"- {rec['name']}: ${rec['amount']:.2f} ({rec['frequency']}) - Next: {rec['next_date']}\n"
    
    prompt = f"""You are a knowledgeable and friendly personal financial advisor. You have access to the user's complete financial data and should provide helpful, actionable advice.

    USER QUESTION: {user_message}

    CURRENT FINANCIAL SNAPSHOT:
    ==========================

    Overall Balance: ${financial_context['balance']['total']:.2f}
    - Total Income: ${financial_context['balance']['total_income']:.2f}
    - Total Expenses: ${financial_context['balance']['total_expenses']:.2f}

    This Month:
    - Income: ${financial_context['monthly']['income']:.2f}
    - Expenses: ${financial_context['monthly']['expenses']:.2f}
    - Net: ${financial_context['monthly']['net']:.2f}

    This Week:
    - Income: ${financial_context['weekly']['income']:.2f}
    - Expenses: ${financial_context['weekly']['expenses']:.2f}
    - Net: ${financial_context['weekly']['net']:.2f}

    {budget_text}

    {category_budget_text}

    {top_expenses_text}

    {recent_trans_text}

    {recurring_text}

    INSTRUCTIONS:
    =============
    1. Answer the user's question directly and concisely
    2. Use the financial data provided to give specific, personalized advice
    3. If they ask "can I afford X?", check their current balance, monthly net income, and budget status
    4. If they're over budget or close to limits, provide gentle warnings and suggestions
    5. Be encouraging and supportive, not judgmental
    6. Provide specific numbers from their data when relevant
    7. Keep responses under 200 words unless more detail is needed
    8. If asked about trends, reference the data provided
    9. For affordability questions, consider both current balance AND monthly cash flow
    10. Suggest practical next steps when appropriate

    RESPONSE:"""

    return prompt