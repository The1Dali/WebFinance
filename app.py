import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apg, login_required, usd

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
    return apology("TODO", 500)
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


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("Please specify the symbol", 400)
        elif not request.form.get("shares"):
            return apology("Please specify the number of shares to buy", 400)
        elif lookup(request.form.get("symbol")) == None:
            return apology("Invalid symbol", 400)
        try:
            shares = int(request.form.get("shares"))
            if shares <= 0:
                return apology("Number of shares must be a positive integer", 400)
        except (ValueError, TypeError):
            return apology("Number of shares must be a positive integer", 400)

        user_id = session["user_id"]
        share = lookup(request.form.get("symbol"))
        price = shares * share["price"]
        balance = db.execute("SELECT cash FROM users WHERE id = ?", user_id)[0]["cash"]
        if balance < price:
            return apology("Can't afford", 400)
        else:
            newbalance = balance - price

        try:
            db.execute("UPDATE users SET cash = ? WHERE id = ?", newbalance, user_id)
            db.execute("INSERT INTO transactions (user_id, symbol, shares, price, type) VALUES (?, ?, ?, ?, ?)", user_id, share["symbol"], shares, share["price"], "BUY")
            flash("Bought!", "success")
        except Exception:
            return apology("Transaction Failed", 500)
        
        return redirect("/")
    
    else:
        return render_template("buy.html")


@app.route("/history")
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
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        if not request.form.get("symbol"):
            return apology("must provide stock symbol")
        
        quoted = lookup(request.form.get("symbol"))
        if not quoted:
            return apology("invalid symbol", 400)
        else:
            quoted["price"] = usd(quoted["price"])
            return render_template("quoted.html", quoted=quoted)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords do not match", 400)

        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get("username"), generate_password_hash(request.form.get("password")))
            return redirect("/")
        except ValueError:
            return apology("Username already exists", 400)
    else:
        return render_template("register.html")
    


@app.route("/sell", methods=["GET", "POST"])
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
