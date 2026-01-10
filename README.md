# Financial Tracker

#### Video Demo: <url>

#### Description: 
The financial tracker is my first ever web project.I used everything i learned in CS50x to create it and im very proud to present it in its full form and glory. It's a comprehensive web-based personal finance management application. Track your income, expenses, budgets, and gain insights into your financial health with beautiful visualizations and powerful analytics.

#### Idea:
As they say:"Need is the mother of invention".
I'm a student so managing my finances is one of the highest priorities of mine.
When it comes to economy driven apps and websites there's a few options but most of the good ones are paid or have ads in them and i wanted to create a trailing website whereby i would use my knowledge to create, not only to incorporate what i learned into reality but to also satisfy my need for having an app that helps me and other students (in the future) manage incomes/expenses and have a very detailed explanation of where each cent is going.


## 📋 Table of Contents

- [Features](#-features)
- [Demo Screenshots](#-demo-screenshots)
- [Tech Stack](#-tech-stack)
- [Usage](#-usage)
- [Database Schema](#-database-schema)
- [File Structure](#-file-structure)
- [Features Deep Dive](#-features-deep-dive)
- [Security Considerations](#-security-considerations)
- [Roadmap](#-roadmap)
- [Acknowledgments](#-acknowledgments)

---

## Features

### Core Functionality
- **Transaction Management**
  - Add, edit, and delete income/expense transactions
  - Categorize transactions with custom categories
  - Attach receipts (JPG, PNG, PDF)
  - Add detailed notes to transactions
  - Backdate transactions for accurate history

- **Recurring Transactions**
  - Set up automatic recurring income/expenses
  - Multiple frequencies: Daily, Weekly, Monthly, Yearly
  - Pause/resume recurring transactions
  - Preview upcoming recurring transactions
  - Automatic transaction creation

- **Budget Management**
  - Set weekly, monthly, or yearly budgets
  - Real-time budget tracking with visual progress bars
  - Budget alerts at 75%, 90%, and 100%
  - Historical budget tracking
  - Budget vs actual comparison

### Analytics & Insights
- **Statistics Dashboard**
  - Income vs expenses bar charts
  - Category breakdown pie charts
  - Monthly trend indicators
  - Top spending categories
  - Savings rate calculator

- **Advanced Analytics**
  - Financial health score (0-100)
  - Period comparison (current vs previous)
  - Daily spending trends
  - Spending by day of week
  - Top 10 expenses and income sources
  - Recurring transaction analysis

- **Visualizations**
  - Interactive Chart.js graphs
  - Doughnut charts for categories
  - Line charts for trends
  - Bar charts for comparisons

### User Experience
- **Secure Authentication**
  - User registration and login
  - Password hashing with Werkzeug
  - Session management
  - Secure password requirements

- **Modern UI/UX**
  - Dark theme by default
  - Light/dark theme toggle
  - Responsive design (mobile, tablet, desktop)
  - Glass morphism effects
  - Smooth animations
  - Bootstrap 5.3 components

- **Advanced Filtering**
  - Filter transactions by type, category, date range
  - Search transactions by name or notes
  - Sort by date or amount
  - Pagination (20 items per page)
  - Clear filters option

### Data Management
- **Export Options**
  - Export transactions to CSV
  - Date range selection
  - All transaction details included

- **Receipt Management**
  - Secure receipt storage
  - Image preview
  - PDF viewing
  - Download receipts
  - Automatic cleanup on deletion

---

## Demo Screenshots

### Dashboard
![Dashboard](docs/screenshots/dashboard.png)
*Main dashboard showing balance, income, expenses, and budget progress*

### Transactions
![Transactions](docs/screenshots/transactions.png)
*Transaction list with filtering, search, and pagination*

### Statistics
![Statistics](docs/screenshots/statistics.png)
*Interactive charts showing spending trends and category breakdown*

### Analytics
![Analytics](docs/screenshots/analytics.png)
*Detailed financial health score and insights*

### Recurring Transactions
![Recurring](docs/screenshots/recurring.png)
*Manage subscriptions and recurring payments*

---

## Tech Stack

### Backend
- **Framework**: Flask 2.3+
- **Database**: SQLite 3
- **Authentication**: Werkzeug Security
- **Session Management**: Flask-Session
- **File Upload**: Werkzeug Utils

### Frontend
- **CSS Framework**: Bootstrap 5.3
- **Icons**: Bootstrap Icons 1.11
- **Charts**: Chart.js 4.x
- **JavaScript**: Vanilla ES6+
- **Template Engine**: Jinja2

### Development Tools
- **Python**: 3.8+
- **Package Manager**: pip
- **Version Control**: Git

---


## Usage

### First Time Setup

1. **Register an Account**
   - Navigate to `/register`
   - Enter a unique username
   - Choose a secure password (min 8 characters)
   - Confirm password
   - Click "Create Account"

2. **Log In**
   - Go to `/login`
   - Enter your credentials

3. **Set Up Your Budget** (Optional)
   - Click on your profile icon
   - Select "Budget Settings"
   - Enter your monthly budget amount
   - Set category limits (optional)
   - Enable budget alerts

### Adding Transactions

#### Manual Entry
1. Click the **"+ Add Transaction"** button (or floating action button)
2. Select transaction type (Income/Expense)
3. Enter transaction parameters:
   - Name
   - Amount 
   - Category 
   - Date (defaults to current date)
   - Notes (optional)
4. Attach receipt (optional)
5. For recurring: Toggle "Recurring Transaction" and set frequency and end_date (optional)
6. Click "Add Transaction"

#### Quick Add
- Use quick amount buttons ($5, $10, $20, $50, $100)
- Use built-in calculator for complex calculations
- Use quick templates (Groceries, Gas, Coffee) (will be extended in the future)

### Managing Recurring Transactions

#### Create Recurring Transaction
1. When adding a transaction, toggle "Recurring Transaction"
2. Select frequency (Daily, Weekly, Monthly, Yearly)
3. Optionally set an end date
4. The system will automatically create transactions based on the schedule

#### View Recurring Transactions
- Navigate to `/recurring`
- See all active and paused recurring transactions
- View next occurrence date
- See countdown to next transaction

#### Edit Recurring Transaction
1. Go to `/recurring`
2. Click the three-dot menu on a recurring transaction
3. Select "Edit"
4. Modify details (name, amount, category, frequency, end date, notes)
5. Click "Save Changes"

#### Pause/Resume Recurring Transaction
1. Click the three-dot menu on a recurring transaction
2. Select "Pause" or "Activate"
3. Paused transactions won't create new transactions automatically
4. Resume anytime to continue the schedule

#### Preview Upcoming Transactions
1. Click the "Preview" button on `/recurring` page
2. Select time range (1, 3, 6, or 12 months)
3. View timeline of all upcoming recurring transactions
4. See monthly projections with income/expense totals

### Viewing Statistics

#### Quick Statistics (`/statistics`)
- View income vs expenses by period (daily, weekly, monthly, annual)
- See category breakdowns with pie charts
- Check monthly trends
- View top spending categories
- Monitor savings rate

#### Advanced Analytics (`/analytics`)
- Check your financial health score
- Compare current period vs previous period
- View daily spending trends
- Analyze spending by day of week
- See top 10 expenses and income
- Track recurring transaction impact

### Filtering and Searching

#### Transaction Filters
- **Type**: All, Income, or Expenses only
- **Category**: Filter by specific category
- **Date Range**: Last 7/30/90/365 days or all time
- **Sort**: By date (newest/oldest) or amount (highest/lowest)
- **Search**: Search by transaction name or notes

#### Using Search
1. Type in the search box
2. Search automatically submits after you stop typing
3. Results update in real-time
4. Search looks through transaction names and notes

### Exporting Data

#### Export to CSV
1. Go to `/analytics`
2. Select your date range
3. Click "Export to CSV"
4. File downloads with format: `transactions_YYYY-MM-DD_to_YYYY-MM-DD.csv`
5. Open in Excel, Google Sheets, or any spreadsheet software

#### CSV Format
```csv
Date,Name,Type,Category,Amount,Notes
2026-01-09,Groceries,EXPENSE,Food,85.50,Weekly shopping
2026-01-08,Salary,INCOME,Salary,5000.00,Monthly paycheck
```

### Managing Receipts

#### Upload Receipt
- When adding/editing a transaction, click "Choose File"
- Select JPG, PNG, or PDF (max 5MB)
- Preview appears before saving
- Receipt is stored securely

#### View Receipt
- In transaction list, click the paperclip icon
- Receipt opens in new tab
- For images: full resolution display
- For PDFs: browser PDF viewer

#### Download Receipt
- Click receipt link
- Use browser's save/download option
- Original filename is preserved

---

## Database Schema

### Users Table
```sql
CREATE TABLE users 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX username ON users (username);
```

**Purpose**: Store user account information
**Fields**:
- `id`: Unique identifier for each user
- `username`: Unique username for login
- `hash`: Hashed password (never stored in plain text)
- `created_at`: Account creation timestamp

### Categories Table
```sql
CREATE TABLE categories 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK(type IN ('EXPENSE', 'INCOME')),
    icon TEXT,
    color TEXT
);
```

**Purpose**: Store transaction categories with visual properties
**Fields**:
- `id`: Unique identifier
- `name`: Category name (e.g., "Food", "Salary")
- `type`: Either 'EXPENSE' or 'INCOME'
- `icon`: Bootstrap icon class (e.g., "bi-cart")
- `color`: Hex color for charts (e.g., "#FF6384")

### Transactions Table
```sql
CREATE TABLE transactions 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    amount NUMERIC NOT NULL CHECK(amount > 0),
    type TEXT NOT NULL CHECK(type IN ('EXPENSE', 'INCOME')),
    category TEXT NOT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    receipt_path VARCHAR(255),
    is_recurring INTEGER DEFAULT 0 CHECK(is_recurring IN (0, 1)),
    recurring_template_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(recurring_template_id) REFERENCES recurring_transactions(id)
);

-- Indexes for performance
CREATE INDEX idx_user_transactions ON transactions(user_id, time DESC);
CREATE INDEX idx_transaction_type ON transactions(user_id, type);
CREATE INDEX idx_transaction_category ON transactions(user_id, category);
CREATE INDEX idx_recurring_template ON transactions(recurring_template_id);
```

**Purpose**: Store all financial transactions
**Fields**:
- `id`: Unique transaction ID
- `user_id`: Links to users table
- `name`: Transaction description
- `amount`: Transaction amount (always positive)
- `type`: 'INCOME' or 'EXPENSE'
- `category`: Transaction category
- `time`: Transaction date/time
- `notes`: Optional notes
- `receipt_path`: Path to receipt file
- `is_recurring`: Flag for recurring transactions
- `recurring_template_id`: Links to recurring template if auto-generated

### Recurring Transactions Table
```sql
CREATE TABLE recurring_transactions 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    amount NUMERIC NOT NULL CHECK(amount > 0),
    type TEXT NOT NULL CHECK(type IN ('EXPENSE', 'INCOME')),
    category TEXT NOT NULL,
    frequency TEXT NOT NULL CHECK(frequency IN ('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'YEARLY')),
    start_date DATE NOT NULL,
    end_date DATE,
    next_occurrence DATE NOT NULL,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX idx_recurring_active ON recurring_transactions(is_active, next_occurrence);
CREATE INDEX idx_user_recurring ON recurring_transactions(user_id);
```

**Purpose**: Store recurring transaction templates
**Fields**:
- `id`: Unique template ID
- `user_id`: Links to users table
- `name`: Transaction name
- `amount`: Transaction amount
- `type`: 'INCOME' or 'EXPENSE'
- `category`: Transaction category
- `frequency`: How often it recurs
- `start_date`: When recurring started
- `end_date`: When to stop (null = indefinite)
- `next_occurrence`: Next date to create transaction
- `is_active`: Whether actively creating transactions
- `notes`: Optional notes
- `created_at`: Template creation date

### Budgets Table
```sql
CREATE TABLE budgets 
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount NUMERIC NOT NULL CHECK(amount > 0),
    period TEXT NOT NULL CHECK(period IN ('WEEKLY', 'MONTHLY', 'YEARLY')),
    start_date DATE NOT NULL,
    end_date DATE,
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

-- Only allow one active budget per user per period
CREATE UNIQUE INDEX idx_active_budget 
ON budgets(user_id, period) 
WHERE is_active = 1;

CREATE INDEX idx_user_budgets ON budgets(user_id);
```

**Purpose**: Store user budget settings
**Fields**:
- `id`: Unique budget ID
- `user_id`: Links to users table
- `amount`: Budget amount
- `period`: 'WEEKLY', 'MONTHLY', or 'YEARLY'
- `start_date`: When budget became active
- `end_date`: When budget ended (null = current)
- `is_active`: Whether this is the active budget
- `created_at`: Budget creation date

---


## File Structure

```
finance-tracker/
│
├── app.py                      # Main Flask application
├── helpers.py                  # Helper functions (login_required, usd, etc...)
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (create manually)
├── .gitignore                # Git ignore rules
├── README.md                 # This file
│
├── Database/
│   ├── Receipts/             # Uploaded receipt files
│   └── finance.db            # SQLite database
│
├── Static/
│   ├── analytics.js           # Javascript file for the analytics page
│   ├── favicon.jpg            # Favicon for the website
│   ├── mysterious.jpg         # Default profile picture
│   ├── profile.js             # Javascript file for the profile section
│   ├── statistics.jpg         # Javascript file for the statistics page
│   └── styles.css             # CSS file with all the styling of the website
│
├── templates/
│   ├── layout.html           # Base template with navigation
│   ├── index.html            # Dashboard
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── forgot-password.html  # Password reset
│   ├── add-transaction.html  # Add transaction form
│   ├── transactions.html     # Transaction list
│   ├── edit_transaction.html # Edit transaction form
│   ├── recurring.html        # Recurring transactions list
│   ├── edit_recurring.html   # Edit recurring form
│   ├── recurring_preview.html # Recurring preview timeline
│   ├── statistics.html       # Statistics dashboard
│   ├── analytics.html        # Analytics page
│   └── apology.html          # Error page
│
├── flask_session/            # Session files (auto-generated)
│
└── docs/
    └── screenshots/          # Documentation screenshots
```

---

## Features Deep Dive

### Financial Health Score

The financial health score is calculated based on three components:

#### 1. Savings Rate (40 points max)
```python
savings_rate = (income - expenses) / income
savings_points = min(savings_rate * 100, 40)
```
- Measures how much of your income you're saving
- 20%+ savings rate = 40 points (excellent)
- 10% savings rate = 20 points (good)
- 0% savings rate = 0 points (needs improvement)

#### 2. Budget Adherence (30 points max)
```python
adherence = 1 - abs(actual_spending - budget) / budget
budget_points = max(adherence * 30, 0)
```
- Measures how well you stick to your budget
- Spending exactly at budget = 30 points
- Spending 10% over/under = 27 points
- Spending 50% over/under = 15 points

#### 3. Income Consistency (30 points max)
- 3+ income transactions = 30 points
- 2 income transactions = 20 points
- 1 income transaction = 10 points
- 0 income transactions = 0 points

**Total Score Interpretation**:
- 80-100: Excellent financial health
- 60-79: Good financial health
- 40-59: Fair financial health
- 0-39: Needs improvement

---

### Recurring Transaction System

The recurring transaction system consists of two parts:

#### 1. Recurring Templates
Stored in `recurring_transactions` table with:
- Transaction details (name, amount, category)
- Schedule (frequency, start date, end date)
- Status (active/paused)
- Next occurrence date

#### 2. Automatic Transaction Creation
```python
def process_recurring_transactions():
    # Runs daily to create due transactions
    # 1. Find all active recurring with next_occurrence <= today
    # 2. Create actual transaction
    # 3. Calculate and update next_occurrence
    # 4. Repeat until end_date (if set)
```

**Scheduling Options**:
- **On App Startup**: Runs once when Flask starts
- **APScheduler**: Runs daily at midnight automatically
- **Manual**: Visit `/recurring/process` endpoint
- **Cron Job**: Set up system cron for production

---

### Budget Alert System

Alerts trigger at three thresholds:

```python
if percentage >= 100:
    flash("🚨 Budget Alert: You've exceeded your budget!", "danger")
elif percentage >= 90:
    flash("⚠️ Budget Warning: You've used 90% of your budget!", "warning")
elif percentage >= 75:
    flash("💡 Budget Notice: You've used 75% of your budget.", "info")
```

**Alert Display**:
- Shown as flash messages at top of page
- Color-coded by severity
- Shows exact amount over/under
- Appears immediately after adding transaction

---

### Search and Filter System

#### Transaction Filtering
Filters are applied server-side using SQL WHERE clauses:

```python
where_clauses = ["user_id = ?"]
params = [user_id]

if type_filter != 'all':
    where_clauses.append("type = ?")
    params.append(type_filter)

if category_filter != 'all':
    where_clauses.append("category = ?")
    params.append(category_filter)

# ... more filters

where_clause = " AND ".join(where_clauses)
query = f"SELECT * FROM transactions WHERE {where_clause}"
```

#### Search Implementation
Uses SQL LIKE for fuzzy matching:

```python
if search_term:
    where_clauses.append("(name LIKE ? OR notes LIKE ?)")
    params.extend([f"%{search_term}%", f"%{search_term}%"])
```

**Client-side**: Auto-submits form after typing stops (500ms delay)

---

### Receipt Management

#### Upload Process
1. Validate file type and size
2. Generate unique filename: `{user_id}_{timestamp}_{original_name}`
3. Save to `Database/Receipts/`
4. Store path in database

#### Security Measures
- Only image/PDF files allowed
- 5MB file size limit
- Unique filenames prevent overwriting
- User ownership verified before viewing
- Secure filename generation with `secure_filename()`

#### Viewing Receipts
```python
@app.route("/receipt/<transaction_id>")
@login_required
def view_receipt(transaction_id):
    # 1. Verify user owns transaction
    # 2. Get receipt path from database
    # 3. Check file exists
    # 4. Serve file with send_file()
```

---

## Security Considerations

### Password Security
- **Hashing**: Uses Werkzeug's `generate_password_hash` with SHA-256
- **Salting**: Automatic unique salt per password
- **Verification**: Constant-time comparison with `check_password_hash`
- **Never Stored**: Plain text passwords never saved to database

### SQL Injection Prevention
- **Parameterized Queries**: All database queries use `?` placeholders
- **CS50 Library**: Automatic escaping of user input
- **No String Concatenation**: Never build SQL with string formatting

### File Upload Security
- **Type Validation**: Only allows specific file extensions
- **Size Limits**: Maximum 5MB per file
- **Secure Filenames**: Uses `secure_filename()` to prevent directory traversal
- **Unique Names**: Timestamp and user ID prevent filename collisions
- **Ownership Verification**: Users can only access their own receipts

---


## Roadmap

### Version 2.0 (Planned)
- [ ] **Multi-currency Support**
  - Add multiple currencies
  - Real-time exchange rates
  - Currency conversion in reports

- [ ] **Goals & Savings**
  - Set savings goals
  - Track progress
  - Goal completion celebrations

### Version 2.1 (Future)
- [ ] **Mobile App**
  - iOS app
  - Android app
  - Receipt OCR scanning

- [ ] **Advanced Reports**
  - PDF report generation
  - Scheduled email reports
  - Tax reporting features

- [ ] **AI Insights**
  - Spending predictions
  - Anomaly detection
  - Personalized recommendations

### Version 3.0 (Long-term)
- [ ] **Investment Tracking**
  - Track stocks/crypto
  - Portfolio analysis
  - Performance metrics

- [ ] **Business Features**
  - Invoice generation
  - Expense categorization for taxes
  - Multi-user business accounts

---

## Acknowledgments

### Technologies
- **Flask** - Web framework
- **Bootstrap** - UI framework
- **Chart.js** - Data visualization
- **SQLite** - Database engine
- **CS50** - SQL library

### Resources
- Flask documentation
- Bootstrap documentation
- Chart.js documentation
- Stack Overflow community

### CS50 Team
- Special thanks to prof. David J. Malan and all the CS50 team for delivering a very memorable course full of information and enthusiasm which in turn helped extend my knowledge and create this app.

---

**Made with love by Dali**