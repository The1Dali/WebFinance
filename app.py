import os
from datetime import datetime

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
    return apg("TODO", 500)
    """
    user_id = session["user_id"]
    cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
    data = db.execute(SELECT symbol, SUM(CASE WHEN type = 'BUY' THEN shares ELSE -shares END) as total_shares
        FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0, user_id)
    total = cash
    for holding in data:
        holding["price"] = lookup(holding["symbol"])["price"]
        holding["total"] = holding["price"] * holding["total_shares"]
        total += holding["total"]
        holding["price"] = usd(holding["price"])
        holding["total"] = usd(holding["total"])

    render_template("index.html", cash=usd(cash), data=data, total=usd(total))
    """


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
                unique_filename = f"{session['user_id']}_{timestamp}_{filename}"
                
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(filepath)
                receipt_path = f"Database/Receipts/{unique_filename}"
        
        try:
            if is_recurring:
                next_occurrence = datetime.now().date()
                
                recurring_id = db.execute("""INSERT INTO recurring_transactions 
                    (user_id, name, amount, type, category, frequency, start_date, end_date, next_occurrence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    recurring_frequency,
                    datetime.now().date(),
                    recurring_end_date if recurring_end_date else None,
                    next_occurrence,
                    notes)
                
                db.execute("""INSERT INTO transactions 
                    (user_id, name, amount, type, category, notes, receipt_path, recurring_template_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    notes, 
                    receipt_path,
                    recurring_id)
                
                flash(f"Recurring {transaction_type.lower()} added successfully!", "success")
            else:

                db.execute("""INSERT INTO transactions 
                    (user_id, name, amount, type, category, notes, receipt_path, is_recurring)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""", 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    notes, 
                    receipt_path,
                    0
                )
                flash(f"{transaction_type.capitalize()} added successfully!", "success")
            
            if transaction_type == "EXPENSE":
                check_budget_warning(category, amount)
            
            return redirect("/")
            
        except Exception as e:
            # Clean up uploaded file if database insert fails
            if receipt_path and os.path.exists(os.path.join('static', receipt_path)):
                os.remove(os.path.join('static', receipt_path))
            
            flash(f"Error adding transaction: {str(e)}", "error")
            return render_template("addt.html", categories=categories)
    

    return render_template("addt.html", categories=categories)


@app.route("/statistic")
@login_required
def history():
    """Show history of transactions"""
    SORTS = ["symbol", "shares", "price", "time", "type"]
    user_id = session["user_id"]
    sort_by = request.args.get("sort", "time")
    order = request.args.get("order", "desc")
    if sort_by not in SORTS:
        sort_by = "time"
    if order not in ["asc", "desc"]:
        order = "desc"
    query = f"""SELECT symbol, shares, price, type, time FROM transactions WHERE user_id = ? ORDER BY {sort_by} {order.upper()}"""
    data = db.execute(query, user_id)
    for holding in data:
        holding["price"] = usd(holding["price"])

    return render_template("history.html", data=data, sort_by=sort_by, order=order)


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
    


@app.route("/transaction", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    user_id = session["user_id"]
    data = db.execute("""SELECT symbol, SUM(CASE WHEN type = 'BUY' THEN shares ELSE -shares END) as total_shares
                      FROM transactions WHERE user_id = ? GROUP BY symbol HAVING total_shares > 0""", user_id)
    symbols = [ d["symbol"] for d in data]
    shares = [ d["total_shares"] for d in data]
    if request.method == "POST":
        if not request.form.get("symbol") or request.form.get("symbol")=="Symbol":
            return apology("Please choose a symbol to sell", 400)
        elif not request.form.get("shares"):
            return apology("Please input the amount of shares to sell", 400)
        try:
            share = int(request.form.get("shares"))
            if share <= 0:
                return apology("Shares need to be a positive integer", 400)
            symbol = request.form.get("symbol")
        except(TypeError, ValueError):
            return apology("Shares need to be a positive integer", 400)
        owned_shares = next((d["total_shares"] for d in data if d["symbol"] == symbol), 0)

        if symbol in symbols:
            if share <= owned_shares:
                cash = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
                price = lookup(symbol)["price"]
                newbalance = cash + price * share
                try:
                    db.execute("UPDATE users SET cash = ? WHERE id = ?", newbalance, user_id)
                    db.execute("INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?)", user_id, symbol, share, price, "SELL")
                    flash("Sold!", "success")
                    return redirect("/")
                except Exception:
                    return apology("Transaction Failed", 500)
            else:
                return apology("Don't own specified shares", 400)
                
        else:
            return apology("Invalid Symbol", 400)

    else:
        return render_template("sell.html", symbols=symbols)
