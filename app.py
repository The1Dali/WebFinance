import json
import os
from datetime import datetime, timedelta

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apg, login_required, usd, check_budget_warning, allowed_file

UPLOAD_FOLDER = "Database/Receipts"
MAX_FILE_SIZE = 5 * 1024 * 1024 

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///Database/finance.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    """Show dashboard"""
    user_id = session["user_id"]

    today = datetime.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)
    
    weekly_income = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        AND time >= ?
    """, user_id, week_ago)[0]['total']
    
    weekly_expense = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
    """, user_id, week_ago)[0]['total']
    
    monthly_income = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        AND time >= ?
    """, user_id, month_ago)[0]['total']
    
    monthly_expense = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
    """, user_id, month_ago)[0]['total']
    
    yearly_income = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        AND time >= ?
    """, user_id, year_ago)[0]['total']
    
    yearly_expense = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
    """, user_id, year_ago)[0]['total']
    
    income_by_category = db.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        GROUP BY category
        ORDER BY total DESC
    """, user_id)
    
    # Prepare data for Chart.js
    income_labels = [row['category'] for row in income_by_category]
    income_values = [float(row['total']) for row in income_by_category]
    
    expense_by_category = db.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        GROUP BY category
        ORDER BY total DESC
    """, user_id)
    
    # Prepare data for Chart.js
    expense_labels = [row['category'] for row in expense_by_category]
    expense_values = [float(row['total']) for row in expense_by_category]
    

    recent_transactions = db.execute("""
        SELECT id, name, amount, type, category, time, receipt_path
        FROM transactions
        WHERE user_id = ?
        ORDER BY time DESC
        LIMIT 10
    """, user_id)
    
    for transaction in recent_transactions:
        transaction['formatted_amount'] = f"${transaction['amount']:.2f}"
        transaction['formatted_date'] = datetime.fromisoformat(str(transaction['time'])).strftime('%Y-%m-%d')
        

    budget = db.execute("""
        SELECT amount FROM budgets
        WHERE user_id = ? AND period = 'MONTHLY' AND is_active = 1
    """, user_id)
    
    budget_data = None
    if budget:
        budget_amount = budget[0]['amount']
        spent = monthly_expense
        remaining = budget_amount - spent
        percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
        
        budget_data = {
            'total': budget_amount,
            'spent': spent,
            'remaining': remaining,
            'percentage': round(percentage, 1)
        }

    total_balance = yearly_income - yearly_expense
    
    summary = {
        'balance': total_balance,
        'monthly_income': monthly_income,
        'monthly_expense': monthly_expense,
        'weekly_income': weekly_income,
        'weekly_expense': weekly_expense
    }

    return render_template("index.html",
        histogram_data=json.dumps
        ({
            'labels': ['Weekly', 'Monthly', 'Yearly'],
            'income': [float(weekly_income), float(monthly_income), float(yearly_income)],
            'expenses': [float(weekly_expense), float(monthly_expense), float(yearly_expense)]
        }),
        income_chart_data=json.dumps
        ({
            'labels': income_labels,
            'values': income_values
        }),
        expense_chart_data=json.dumps
        ({
            'labels': expense_labels,
            'values': expense_values
        }),
        transactions=recent_transactions,
        summary=summary,
        budget=budget_data)



@app.route("/add", methods=["GET", "POST"])
@login_required
def add_transaction():
    """add a transaction to the database"""
    user_id = session["user_id"]
    categories = db.execute("SELECT * FROM categories")
    if request.method == "POST":

        name = request.form.get("name")
        amount = request.form.get("amount")
        transaction_type = request.form.get("type")
        category = request.form.get("category")
        notes = request.form.get("notes")
        is_recurring = 1 if request.form.get("is_recurring") else 0
        recurring_frequency = request.form.get("recurring_frequency")
        recurring_end_date = request.form.get("recurring_end_date")
        transaction_date = request.form.get("date")
        
        if not name:
            flash("Transaction name is required", "error")
            return render_template("addt.html", categories=categories)
        
        if not amount:
            flash("Amount is required", "error")
            return render_template("addt.html", categories=categories)
        
        try:
            amount = float(amount)
            if amount <= 0:
                flash("Amount must be positive", "error")
                return render_template("addt.html", categories=categories)
        except ValueError:
            flash("Invalid amount", "error")
            return render_template("addt.html", categories=categories)
        
        if not transaction_type or transaction_type not in ['EXPENSE', 'INCOME']:
            flash("Invalid transaction type", "error")
            return render_template("addt.html", categories=categories)
        
        if not category:
            flash("Category is required", "error")
            return render_template("addt.html", categories=categories)

        valid_category = db.execute("SELECT * FROM categories WHERE name = ? AND type = ?", category, transaction_type)
        if not valid_category:
            flash("Invalid category for transaction type", "error")
            return render_template("addt.html", categories=categories)

        if not transaction_date:
            flash("Date is required", "error")
            return render_template("addt.html", categories=categories)
        
        if is_recurring:
            if not recurring_frequency or recurring_frequency not in ['DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY']:
                flash("Invalid recurring frequency", "error")
                return render_template("addt.html", categories=categories)
        
        
        receipt_path = None
        if 'receipt' in request.files:
            file = request.files['receipt']
            if file and file.filename and allowed_file(file.filename):
                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)
                
                if file_size > MAX_FILE_SIZE:
                    flash("File size must be less than 5MB", "error")
                    return render_template("addt.html", categories=categories)
                
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(file.filename)
                unique_filename = f"{user_id}_{timestamp}_{filename}"
                
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                
                receipt_path = filepath

                
        
        try:
            if is_recurring:
                next_occurrence = datetime.now().date()
                
                recurring_id = db.execute("""
                    INSERT INTO recurring_transactions 
                    (user_id, name, amount, type, category, frequency, start_date, end_date, next_occurrence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    recurring_frequency,
                    datetime.now().date(),
                    recurring_end_date if recurring_end_date else None,
                    next_occurrence,
                    notes
                )
                
                db.execute("""
                    INSERT INTO transactions 
                    (user_id, name, amount, type, category, notes, receipt_path, is_recurring, recurring_template_id, time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    notes, 
                    receipt_path,
                    1,
                    recurring_id,
                    transaction_date
                )
                
                flash(f"Recurring {transaction_type.lower()} added successfully!", "success")
            else:
                db.execute("""
                    INSERT INTO transactions 
                    (user_id, name, amount, type, category, notes, receipt_path, is_recurring, time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    notes, 
                    receipt_path,
                    0,
                    transaction_date
                )

                flash(f"{transaction_type.capitalize()} added successfully!", "success")
            
            if transaction_type == "EXPENSE":
                check_budget_warning(user_id, amount)
            
            return redirect("/")
            
        except Exception as e:
            # Clean up uploaded file if database insert fails
            if receipt_path and os.path.exists(receipt_path):
                os.remove(receipt_path)
            
            flash(f"Error adding transaction: {str(e)}", "error")
            return render_template("addt.html", categories=categories)
    

    return render_template("addt.html", categories=categories)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apg("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apg("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apg("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""
    # Forget any user_id
    session.clear()
    # Redirect user to login form
    return redirect("/")

@app.route("/receipt/<int:transaction_id>")
@login_required
def view_receipt(transaction_id):
    """Serve receipt file with authentication"""
    from flask import send_file, abort
    
    # Verify user owns this transaction
    transaction = db.execute("""SELECT receipt_path FROM transactions WHERE id = ? AND user_id = ?""", transaction_id, session["user_id"])
    
    if not transaction or not transaction[0]['receipt_path']:
        abort(404)
    
    receipt_path = transaction[0]['receipt_path']
    
    if not os.path.exists(receipt_path):
        abort(404)
    
    return send_file(receipt_path)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apg("must provide username", 400)
        elif not request.form.get("password"):
            return apg("must provide password", 400)
        elif len(request.form.get("password")) < 8:
            return apg("password must be atleast 8 characters long", 400)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apg("passwords do not match", 403)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
            return redirect("/")
        except ValueError:
            return apg("Username already exists", 400)
    else:
        return render_template("register.html")

@app.route("/statistics")
@login_required
def statistics():
    """Display extensive income/expense statistics"""
    return apg("TODO", 500)


@app.route("/transactions")
@login_required
def transactions():
    """Show all transactions"""
    user_id = session["user_id"]
    transaction_type = request.args.get('type', 'all') 
    category = request.args.get('category', 'all')
    date_range = request.args.get('range', '90')
    sort_by = request.args.get('sort', 'date-desc') 
    search = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = request.args.get("tppage", 20)
    
    where_clauses = ["user_id = ?"]
    params = [user_id]
    
    if transaction_type != 'all':
        where_clauses.append("type = ?")
        params.append(transaction_type)
    
    if category != 'all':
        where_clauses.append("category = ?")
        params.append(category)

    if date_range != 'all':
        days = int(date_range)
        date_limit = datetime.now() - timedelta(days=days)
        where_clauses.append("time >= ?")
        params.append(date_limit)
    
    if search:
        where_clauses.append("(name LIKE ? OR notes LIKE ?)")
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    where_clause = " AND ".join(where_clauses)
    
    if sort_by == 'date-desc':
        order_by = "time DESC"
    elif sort_by == 'date-asc':
        order_by = "time ASC"
    elif sort_by == 'amount-desc':
        order_by = "amount DESC"
    elif sort_by == 'amount-asc':
        order_by = "amount ASC"
    else:
        order_by = "time DESC"
    
    count_query = f"SELECT COUNT(*) as total FROM transactions WHERE {where_clause}"
    total_transactions = db.execute(count_query, *params)[0]['total']
    total_pages = (total_transactions + int(per_page) - 1) // int(per_page)
    
    offset = (page - 1) * int(per_page)
    query = f"""
        SELECT id, name, amount, type, category, time, notes, receipt_path, is_recurring
        FROM transactions
        WHERE {where_clause}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
    """
    
    transactions = db.execute(query, *params, int(per_page), offset)
    
    for transaction in transactions:
        transaction['formatted_amount'] = f"${transaction['amount']:.2f}"
        transaction['formatted_date'] = datetime.fromisoformat(str(transaction['time'])).strftime('%b %d, %Y')
        transaction['formatted_time'] = datetime.fromisoformat(str(transaction['time'])).strftime('%I:%M %p')
    
    categories = db.execute("SELECT DISTINCT name FROM categories ORDER BY name")
    
    summary_query = f"""
        SELECT 
            COALESCE(SUM(CASE WHEN type = 'INCOME' THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN type = 'EXPENSE' THEN amount ELSE 0 END), 0) as total_expense,
            COUNT(*) as count
        FROM transactions
        WHERE {where_clause}
    """
    summary = db.execute(summary_query, *params)[0]
    summary['net'] = summary['total_income'] - summary['total_expense']
    
    return render_template("transaction.html",
        transactions=transactions,
        categories=categories,
        summary=summary,
        filters={
            'type': transaction_type,
            'category': category,
            'range': date_range,
            'sort': sort_by,
            'search': search,
            'per_page' : per_page
        },
        pagination={
            'current': page,
            'total': total_pages,
            'total_items': total_transactions
        }
    )

@app.route("/transaction/delete/<int:transaction_id>", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    """Delete a transaction"""
    user_id = session["user_id"]
    
    transaction = db.execute(
        "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
        transaction_id, user_id
    )
    
    if not transaction:
        flash("Transaction not found", "error")
        return redirect("/transactions")
    
    if transaction[0]['receipt_path']:
        receipt_path = transaction[0]['receipt_path']
        if os.path.exists(receipt_path):
            os.remove(receipt_path)
    
    db.execute("DELETE FROM transactions WHERE id = ?", transaction_id)
    
    flash("Transaction deleted successfully", "success")
    return redirect("/transactions")

@app.route("/transaction/edit/<int:transaction_id>", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    """Edit a transaction"""
    user_id = session["user_id"]
    
    transaction = db.execute(
        "SELECT * FROM transactions WHERE id = ? AND user_id = ?",
        transaction_id, user_id
    )
    
    if not transaction:
        flash("Transaction not found", "error")
        return redirect("/transactions")
    
    transaction = transaction[0]
    
    if request.method == "POST":
        name = request.form.get("name")
        amount = request.form.get("amount")
        category = request.form.get("category")
        notes = request.form.get("notes")
        
        if not name or not amount or not category:
            flash("All fields are required", "error")
            return redirect(f"/transaction/edit/{transaction_id}")
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount", "error")
            return redirect(f"/transaction/edit/{transaction_id}")
        
        db.execute("""
            UPDATE transactions 
            SET name = ?, amount = ?, category = ?, notes = ?
            WHERE id = ?
        """, name, amount, category, notes, transaction_id)
        
        flash("Transaction updated successfully", "success")
        return redirect("/transactions")
    
    categories = db.execute("SELECT * FROM categories WHERE type = ?", transaction['type'])
    return render_template("editt.html", transaction=transaction, categories=categories)
