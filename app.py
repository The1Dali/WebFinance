from cs50 import SQL
from datetime import datetime, timedelta
from faster_whisper import WhisperModel
from flask import Flask, flash, redirect, render_template, request, session, send_file, abort, jsonify
from flask_session import Session
from functools import wraps
from io import StringIO, BytesIO
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from helpers import apg, usd, login_required, allowed_file, check_budget_warning, get_histogram_data, calculate_trends, get_spending_trends, get_category_analysis, get_period_comparison, get_time_analysis, calculate_financial_health, get_recurring_analysis, calculate_next_date, process_recurring_transactions, load_whisper_model, get_user_financial_data, create_financial_prompt

import calendar
import csv
import calendar
import json
import os
import requests
import tempfile
import tempfile



UPLOAD_FOLDER = "Database/Receipts"
MAX_FILE_SIZE = 5 * 1024 * 1024 

WHISPER_MODEL = "base" 
USE_FASTER_WHISPER = True

conversation_history = {}

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"

whisper_model = None

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

@app.before_request
def before_first_request():
    """Run recurring transactions processor on app startup"""
    if not hasattr(app, 'recurring_processed'):
        process_recurring_transactions()
        app.recurring_processed = True


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
                today = datetime.now().date()
                
                recurring_id = db.execute("""INSERT INTO recurring_transactions 
                    (user_id, name, amount, type, category, frequency, start_date, end_date, next_occurrence, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    recurring_frequency,
                    today,  
                    recurring_end_date if recurring_end_date else None,
                    today, 
                    notes)
                
                db.execute("""INSERT INTO transactions 
                    (user_id, name, amount, type, category, notes, receipt_path, is_recurring, recurring_template_id, time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", 
                    user_id, 
                    name, 
                    amount, 
                    transaction_type, 
                    category, 
                    notes, 
                    receipt_path,
                    1,
                    recurring_id,
                    today)
                
                next_date = calculate_next_date(today, recurring_frequency)
                db.execute("""
                    UPDATE recurring_transactions
                    SET next_occurrence = ?
                    WHERE id = ?
                """, next_date, recurring_id)
                
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
    

    return render_template("add-transaction.html", categories=categories)

@app.route("/analytics")
def analytics():
    """Detailed analytics and insights"""
    user_id = session["user_id"]
    
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')
    
    if not start_date_str or not end_date_str:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
    else:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    
    spending_trends = get_spending_trends(user_id, start_date, end_date)
    
    category_analysis = get_category_analysis(user_id, start_date, end_date)
    
    comparison = get_period_comparison(user_id, start_date, end_date)
    
    time_analysis = get_time_analysis(user_id, start_date, end_date)
    
    health_score = calculate_financial_health(user_id, start_date, end_date)
    
    top_expenses = db.execute("""
        SELECT name, amount, category, time
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ? AND time <= ?
        ORDER BY amount DESC
        LIMIT 10
    """, user_id, start_date, end_date)
    
    top_income = db.execute("""
        SELECT name, amount, category, time
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        AND time >= ? AND time <= ?
        ORDER BY amount DESC
        LIMIT 10
    """, user_id, start_date, end_date)
    
    for t in top_expenses + top_income:
        t['formatted_date'] = datetime.fromisoformat(str(t['time'])).strftime('%b %d, %Y')
    
    recurring_stats = get_recurring_analysis(user_id)
    
    return render_template("analytics.html",
        spending_trends=json.dumps(spending_trends),
        category_analysis=category_analysis,
        comparison=comparison,
        time_analysis=json.dumps(time_analysis),
        health_score=health_score,
        top_expenses=top_expenses,
        top_income=top_income,
        recurring_stats=recurring_stats,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d')
    )

@app.route("/analytics/export/csv")
@login_required
def export_csv():
    """Export transactions to CSV"""
    user_id = session["user_id"]
    
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    
    transactions = db.execute("""
        SELECT name, amount, type, category, time, notes
        FROM transactions
        WHERE user_id = ?
        AND time >= ? AND time <= ?
        ORDER BY time DESC
    """, user_id, start_date, end_date)
    
    # Create CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Name', 'Type', 'Category', 'Amount', 'Notes'])
    
    for t in transactions:
        writer.writerow([
            t['time'],
            t['name'],
            t['type'],
            t['category'],
            t['amount'],
            t['notes'] or ''
        ])
    
    output.seek(0)
    return send_file(
        BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'transactions_{start_date}_to_{end_date}.csv'
    )

@app.route('/api/speech-to-text', methods=['POST'])
@login_required
def speech_to_text():
    """Convert speech audio to text using Whisper"""
    try:
        from helpers import whisper_model as loaded_model
        
        if loaded_model is None:
            print("Whisper model is None!")
            return jsonify({
                'error': 'Speech recognition not available',
                'message': 'Whisper model not loaded. Please restart the server.'
            }), 503

        
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        print(f"Received audio file: {audio_file.filename}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_audio:
            audio_file.save(temp_audio.name)
            temp_path = temp_audio.name
        
        print(f"Saved to: {temp_path}")
        
        try:
            print("Starting transcription...")
            
            segments, info = loaded_model.transcribe(  # Use loaded_model instead
                temp_path,
                language="en",
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            transcription = " ".join([segment.text for segment in segments]).strip()
            
            os.unlink(temp_path)
            
            print(f"Transcription: '{transcription}'")
            
            if not transcription:
                return jsonify({
                    'error': 'No speech detected',
                    'message': 'Could not detect any speech. Please try again.'
                }), 400
            
            return jsonify({
                'transcription': transcription,
                'success': True
            })
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise e
            
    except Exception as e:
        print(f"Speech-to-text error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to transcribe audio',
            'message': str(e)
        }), 500

@app.route('/api/ai-chat', methods=['POST'])
@login_required
def ai_chat():
    """
    Handle AI chat requests with financial context
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required'}), 400
        
        user_id = session['user_id']
        
        print(f"User {user_id} asked: {user_message}")
        
        if user_id not in conversation_history:
            conversation_history[user_id] = []
        
        financial_context = get_user_financial_data(user_id)
        
        prompt = create_financial_prompt(user_message, financial_context)
        
        print("Sending to Model...")
        
        ollama_response = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 200
                }
            },
            timeout=30
        )
        
        if ollama_response.status_code != 200:
            print(f"Ollama error: {ollama_response.status_code}")
            return jsonify({
                'error': 'AI service unavailable',
                'response': 'Sorry, I\'m having trouble connecting to the AI service. Please try again.'
            }), 500
        
        ai_response = ollama_response.json().get('response', '').strip()
        
        print(f"AI Response: {ai_response[:100]}...")
        
        conversation_history[user_id].append({
            'user': user_message,
            'assistant': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(conversation_history[user_id]) > 10:
            conversation_history[user_id] = conversation_history[user_id][-10:]
        
        return jsonify({
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
        
    except requests.Timeout:
        return jsonify({
            'error': 'Request timeout',
            'response': 'The AI took too long to respond. Please try a simpler question.'
        }), 504
        
    except Exception as e:
        print(f"AI Chat Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'response': 'Sorry, something went wrong. Please try again.'
        }), 500

@app.route("/budget/get", methods=["GET"])
@login_required
def get_budget():
    """Get current budget settings for the user"""
    user_id = session["user_id"]

    budget = db.execute("""
        SELECT amount, start_date, end_date
        FROM budgets
        WHERE user_id = ? AND is_active = 1
        LIMIT 1
    """, user_id)
    
    category_limits = db.execute("""
        SELECT category, limit_amount
        FROM category_budgets
        WHERE user_id = ? AND is_active = 1
    """, user_id)
    
    budget_data = {
        'monthlyBudget': float(budget[0]['amount']) if budget else None,
        'start_date': budget[0]['start_date'] if budget else None,
        'end_date': budget[0]['end_date'] if budget else None,
        'categories': {}
    }
    
    for cat in category_limits:
        budget_data['categories'][cat['category']] = float(cat['limit_amount'])
    
    return json.dumps(budget_data)


@app.route("/budget/save", methods=["POST"])
@login_required
def save_budget():
    """Save or update the single budget with category limits"""
    user_id = session["user_id"]
    
    try:
        data = request.get_json()
        monthly_budget = data.get('monthlyBudget')
        category_limits = data.get('categoryLimits', {})
        
        if not monthly_budget or float(monthly_budget) <= 0:
            return json.dumps({'success': False, 'error': 'Invalid budget amount'}), 400
        
        monthly_budget = float(monthly_budget)
        
        total_category_limits = sum(float(v) for v in category_limits.values() if v)
        if total_category_limits > monthly_budget:
            return json.dumps({
                'success': False, 
                'error': f'Category limits (${total_category_limits:.2f}) exceed total budget (${monthly_budget:.2f})'
            }), 400
        
        db.execute("""
            UPDATE budgets 
            SET is_active = 0, end_date = DATE('now')
            WHERE user_id = ? AND is_active = 1
        """, user_id)
        
        db.execute("""
            UPDATE category_budgets
            SET is_active = 0
            WHERE user_id = ? AND is_active = 1
        """, user_id)
        
        today = datetime.now().date()
        db.execute("""
            INSERT INTO budgets (user_id, amount, period, start_date, is_active)
            VALUES (?, ?, 'MONTHLY', ?, 1)
        """, user_id, monthly_budget, today)
        
        for category, limit in category_limits.items():
            if limit and float(limit) > 0:
                db.execute("""
                    INSERT INTO category_budgets (user_id, category, limit_amount, is_active)
                    VALUES (?, ?, ?, 1)
                """, user_id, category, float(limit))
        
        return json.dumps({'success': True, 'message': 'Budget saved successfully'})
        
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)}), 500


@app.route("/budget/status", methods=["GET"])
@login_required
def budget_status():
    """Get current budget status and spending"""
    user_id = session["user_id"]
    
    budget = db.execute("""
        SELECT amount, start_date FROM budgets
        WHERE user_id = ? AND is_active = 1
        LIMIT 1
    """, user_id)
    
    if not budget:
        return json.dumps({'hasBudget': False})
    
    budget_amount = float(budget[0]['amount'])
    start_date = budget[0]['start_date']
    
    today = datetime.now()
    month_start = today.replace(day=1)
    
    monthly_expense = db.execute("""
        SELECT COALESCE(SUM(amount), 0) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
    """, user_id, month_start)[0]['total']
    
    spent = float(monthly_expense)
    remaining = budget_amount - spent
    percentage = (spent / budget_amount * 100) if budget_amount > 0 else 0
    
    category_limits = db.execute("""
        SELECT category, limit_amount
        FROM category_budgets
        WHERE user_id = ? AND is_active = 1
    """, user_id)
    
    category_spending = db.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        AND time >= ?
        GROUP BY category
        ORDER BY total DESC
    """, user_id, month_start)
    
    limits_map = {cat['category']: float(cat['limit_amount']) for cat in category_limits}
    
    categories = []
    for cat in category_spending:
        cat_spent = float(cat['total'])
        cat_limit = limits_map.get(cat['category'], 0)
        cat_percentage = (cat_spent / cat_limit * 100) if cat_limit > 0 else 0
        
        categories.append({
            'name': cat['category'],
            'spent': cat_spent,
            'limit': cat_limit,
            'percentage': round(cat_percentage, 1),
            'isOverBudget': cat_spent > cat_limit if cat_limit > 0 else False
        })
    
    return json.dumps({
        'hasBudget': True,
        'total': budget_amount,
        'spent': spent,
        'remaining': remaining,
        'percentage': round(percentage, 1),
        'categories': categories,
        'isOverBudget': spent > budget_amount
    })


@app.route("/budget/delete", methods=["POST"])
@login_required
def delete_budget():
    """Delete/deactivate current budget and all category budgets"""
    user_id = session["user_id"]
    
    try:
        db.execute("""
            UPDATE budgets 
            SET is_active = 0, end_date = DATE('now')
            WHERE user_id = ? AND is_active = 1
        """, user_id)
        
        db.execute("""
            UPDATE category_budgets
            SET is_active = 0
            WHERE user_id = ? AND is_active = 1
        """, user_id)
        
        return json.dumps({'success': True, 'message': 'Budget removed successfully'})
        
    except Exception as e:
        return json.dumps({'success': False, 'error': str(e)}), 500

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
    
    # Verify user owns this transaction
    transaction = db.execute("""SELECT receipt_path FROM transactions WHERE id = ? AND user_id = ?""", transaction_id, session["user_id"])
    
    if not transaction or not transaction[0]['receipt_path']:
        abort(404)
    
    receipt_path = transaction[0]['receipt_path']
    
    if not os.path.exists(receipt_path):
        abort(404)
    
    return send_file(receipt_path)

@app.route("/recurring")
@login_required
def recurring():
    """View and manage recurring transactions"""
    user_id = session["user_id"]
    
    status_filter = request.args.get('status', 'active')
    type_filter = request.args.get('type', 'all') 
    
    where_clauses = ["user_id = ?"]
    params = [user_id]
    
    if status_filter == 'active':
        where_clauses.append("is_active = 1")
    elif status_filter == 'paused':
        where_clauses.append("is_active = 0")
    
    if type_filter != 'all':
        where_clauses.append("type = ?")
        params.append(type_filter)
    
    where_clause = " AND ".join(where_clauses)
    
    recurring_transactions = db.execute(f"""
        SELECT id, name, amount, type, category, frequency, 
               start_date, end_date, next_occurrence, is_active, notes
        FROM recurring_transactions
        WHERE {where_clause}
        ORDER BY is_active DESC, next_occurrence ASC
    """, *params)
    
    for rt in recurring_transactions:
        rt['formatted_start'] = datetime.fromisoformat(str(rt['start_date'])).strftime('%b %d, %Y')
        if rt['end_date']:
            rt['formatted_end'] = datetime.fromisoformat(str(rt['end_date'])).strftime('%b %d, %Y')
        else:
            rt['formatted_end'] = 'Indefinite'
        
        if rt['next_occurrence']:
            rt['formatted_next'] = datetime.fromisoformat(str(rt['next_occurrence'])).strftime('%b %d, %Y')
            next_date = datetime.fromisoformat(str(rt['next_occurrence'])).date()
            today = datetime.now().date()
            days_until = (next_date - today).days
            rt['days_until'] = days_until
            rt['is_due_soon'] = 0 <= days_until <= 7
    
    active_income = db.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM recurring_transactions
        WHERE user_id = ? AND type = 'INCOME' AND is_active = 1
    """, user_id)[0]
    
    active_expense = db.execute("""
        SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
        FROM recurring_transactions
        WHERE user_id = ? AND type = 'EXPENSE' AND is_active = 1
    """, user_id)[0]
    
    summary = {
        'income_count': active_income['count'],
        'income_total': float(active_income['total']),
        'expense_count': active_expense['count'],
        'expense_total': float(active_expense['total']),
        'net': float(active_income['total'] - active_expense['total'])
    }
    
    categories = db.execute("SELECT * FROM categories ORDER BY type, name")
    
    return render_template("recurring.html",
        recurring_transactions=recurring_transactions,
        summary=summary,
        categories=categories,
        status_filter=status_filter,
        type_filter=type_filter
    )


@app.route("/recurring/toggle/<int:recurring_id>", methods=["POST"])
@login_required
def toggle_recurring(recurring_id):
    """Pause or activate a recurring transaction"""
    user_id = session["user_id"]
    
    recurring = db.execute(
        "SELECT * FROM recurring_transactions WHERE id = ? AND user_id = ?",
        recurring_id, user_id
    )
    
    if not recurring:
        flash("Recurring transaction not found", "error")
        return redirect("/recurring")
    
    new_status = 0 if recurring[0]['is_active'] == 1 else 1
    db.execute(
        "UPDATE recurring_transactions SET is_active = ? WHERE id = ?",
        new_status, recurring_id
    )
    
    status_text = "activated" if new_status == 1 else "paused"
    flash(f"Recurring transaction {status_text} successfully", "success")
    return redirect("/recurring")


@app.route("/recurring/delete/<int:recurring_id>", methods=["POST"])
@login_required
def delete_recurring(recurring_id):
    """Delete a recurring transaction"""
    user_id = session["user_id"]
    
    recurring = db.execute(
        "SELECT * FROM recurring_transactions WHERE id = ? AND user_id = ?",
        recurring_id, user_id
    )
    
    if not recurring:
        flash("Recurring transaction not found", "error")
        return redirect("/recurring")
    
    db.execute("DELETE FROM recurring_transactions WHERE id = ?", recurring_id)
    
    flash("Recurring transaction deleted successfully", "success")
    return redirect("/recurring")


@app.route("/recurring/edit/<int:recurring_id>", methods=["GET", "POST"])
@login_required
def edit_recurring(recurring_id):
    """Edit a recurring transaction"""
    user_id = session["user_id"]
    
    recurring = db.execute(
        "SELECT * FROM recurring_transactions WHERE id = ? AND user_id = ?",
        recurring_id, user_id
    )
    
    if not recurring:
        flash("Recurring transaction not found", "error")
        return redirect("/recurring")
    
    recurring = recurring[0]
    
    if request.method == "POST":
        name = request.form.get("name")
        amount = request.form.get("amount")
        category = request.form.get("category")
        frequency = request.form.get("frequency")
        end_date = request.form.get("end_date")
        notes = request.form.get("notes")
        
        if not name or not amount or not category or not frequency:
            flash("All required fields must be filled", "error")
            return redirect(f"/recurring/edit/{recurring_id}")
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Invalid amount", "error")
            return redirect(f"/recurring/edit/{recurring_id}")
        
        if frequency not in ['DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'YEARLY']:
            flash("Invalid frequency", "error")
            return redirect(f"/recurring/edit/{recurring_id}")
        
        db.execute("""
            UPDATE recurring_transactions
            SET name = ?, amount = ?, category = ?, frequency = ?, 
                end_date = ?, notes = ?
            WHERE id = ?
        """, name, amount, category, frequency, 
            end_date if end_date else None, notes, recurring_id)
        
        flash("Recurring transaction updated successfully", "success")
        return redirect("/recurring")
    
    categories = db.execute(
        "SELECT * FROM categories WHERE type = ? ORDER BY name",
        recurring['type']
    )
    return render_template("edit-recurring.html", 
                          recurring=recurring, 
                          categories=categories)


@app.route("/recurring/preview")
@login_required
def preview_recurring():
    """Preview upcoming recurring transactions"""
    user_id = session["user_id"]
    months = int(request.args.get('months', 3))
    
    # Get all active recurring transactions
    recurring_list = db.execute("""
        SELECT id, name, amount, type, category, frequency, next_occurrence, end_date
        FROM recurring_transactions
        WHERE user_id = ? AND is_active = 1
    """, user_id)
    
    # Generate preview for next N months
    preview = []
    today = datetime.now().date()
    end_preview = today + timedelta(days=months * 30)
    
    for rt in recurring_list:
        current_date = datetime.fromisoformat(str(rt['next_occurrence'])).date()
        end_date = datetime.fromisoformat(str(rt['end_date'])).date() if rt['end_date'] else None
        
        while current_date <= end_preview:
            if end_date and current_date > end_date:
                break
            
            preview.append({
                'name': rt['name'],
                'amount': float(rt['amount']),
                'type': rt['type'],
                'category': rt['category'],
                'date': current_date,
                'formatted_date': current_date.strftime('%b %d, %Y')
            })
            
            # Calculate next occurrence - FIXED
            current_date = calculate_next_date(current_date, rt['frequency'])
    
    # Sort by date
    preview.sort(key=lambda x: x['date'])
    
    # Calculate monthly totals
    monthly_totals = {}
    for item in preview:
        month_key = item['date'].strftime('%Y-%m')
        if month_key not in monthly_totals:
            monthly_totals[month_key] = {'income': 0, 'expense': 0}
        
        if item['type'] == 'INCOME':
            monthly_totals[month_key]['income'] += item['amount']
        else:
            monthly_totals[month_key]['expense'] += item['amount']
    
    return render_template("recurring_preview.html",
        preview=preview,
        monthly_totals=monthly_totals,
        months=months
    )


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
    """Interactive statistics and visualizations"""
    user_id = session["user_id"]

    view = request.args.get('view', 'weekly')  # daily, weekly, monthly, annual
    period = request.args.get('period', 'current')
    
    today = datetime.now()
    
    if view == 'daily':
        if period == 'current':
            start_date = today - timedelta(days=today.weekday())
            end_date = today
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        elif period == 'last':
            start_date = today - timedelta(days=today.weekday() + 7)
            end_date = today - timedelta(days=today.weekday() + 1)
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        else:
            start_date = today - timedelta(days=today.weekday() + 14)
            end_date = today - timedelta(days=today.weekday() + 8)
            labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            
    elif view == 'weekly':
        if period == 'current':
            start_date = today.replace(day=1)
            end_date = today
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']
        elif period == 'last':
            last_month = today.replace(day=1) - timedelta(days=1)
            start_date = last_month.replace(day=1)
            end_date = last_month
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']
        else: 
            two_months_ago = (today.replace(day=1) - timedelta(days=1)).replace(day=1) - timedelta(days=1)
            start_date = two_months_ago.replace(day=1)
            end_date = two_months_ago
            labels = ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5']
            
    elif view == 'monthly':
        if period == 'current':
            start_date = today.replace(month=1, day=1)
            end_date = today
        elif period == 'last':
            start_date = (today.replace(month=1, day=1) - timedelta(days=1)).replace(month=1, day=1)
            end_date = today.replace(month=1, day=1) - timedelta(days=1)
        else: 
            start_date = (today.replace(year=today.year - 2, month=1, day=1))
            end_date = today.replace(year=today.year - 2, month=12, day=31)
        labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
    else: 
        if period == 'last5':
            start_date = today.replace(year=today.year - 5, month=1, day=1)
            end_date = today
            labels = [str(today.year - i) for i in range(5, -1, -1)]
        elif period == 'last10':
            start_date = today.replace(year=today.year - 10, month=1, day=1)
            end_date = today
            labels = [str(today.year - i) for i in range(10, -1, -1)]
        else:
            # Get earliest transaction year
            earliest = db.execute("""
                SELECT MIN(time) as first_transaction 
                FROM transactions 
                WHERE user_id = ?
            """, user_id)
            if earliest and earliest[0]['first_transaction']:
                first_year = datetime.fromisoformat(str(earliest[0]['first_transaction'])).year
                start_date = datetime(first_year, 1, 1)
                end_date = today
                labels = [str(y) for y in range(first_year, today.year + 1)]
            else:
                start_date = today.replace(year=today.year - 5, month=1, day=1)
                end_date = today
                labels = [str(today.year - i) for i in range(5, -1, -1)]
    
    histogram_data = get_histogram_data(user_id, view, start_date, end_date, labels)
    

    income_by_category = db.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'INCOME'
        GROUP BY category
        ORDER BY total DESC
    """, user_id)
    
    expense_by_category = db.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE user_id = ? AND type = 'EXPENSE'
        GROUP BY category
        ORDER BY total DESC
    """, user_id)
    
    categories_info = db.execute("SELECT name, color FROM categories")
    color_map = {cat['name']: cat['color'] for cat in categories_info if cat['color']}
    
    income_chart = {
        'labels': [row['category'] for row in income_by_category],
        'values': [float(row['total']) for row in income_by_category],
        'colors': [color_map.get(row['category'], '#6c757d') for row in income_by_category]
    }
    
    expense_chart = {
        'labels': [row['category'] for row in expense_by_category],
        'values': [float(row['total']) for row in expense_by_category],
        'colors': [color_map.get(row['category'], '#6c757d') for row in expense_by_category]
    }
    

    trends = calculate_trends(user_id)

    
    return render_template("statistics.html",
        histogram_data=json.dumps(histogram_data),
        income_chart=json.dumps(income_chart),
        expense_chart=json.dumps(expense_chart),
        trends=trends,
        current_view=view,
        current_period=period
    )


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
    
    return render_template("transactions.html",
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
    return render_template("edit-transaction.html", transaction=transaction, categories=categories)

if __name__ == '__main__':
    print("="*60)
    print("Financial Tracker Starting...")
    print("="*60)
    
    whisper_model = load_whisper_model()
    
    if whisper_model:
        print("Voice recognition ready!")
    else:
        print("Voice recognition disabled")
    
    print("\nWarming up AI model...")
    try:
        warmup = requests.post(
            OLLAMA_API_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": "Hello",
                "stream": False,
                "options": {"num_predict": 10}
            },
            timeout=60
        )
        if warmup.status_code == 200:
            print("AI model ready!")
    except:
        print("Could not warm up model")
    
    print("="*60)
    print("Starting Flask...")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)