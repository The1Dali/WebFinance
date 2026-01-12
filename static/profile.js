//AI inspired
// Theme toggle function
function toggletheme(e) {
    if (e) e.preventDefault();
    var html = document.documentElement;
    var currentTheme = html.getAttribute('data-bs-theme');
    var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-bs-theme', newTheme);
    
    var themeIcon = document.getElementById('themeIcon');
    var themeText = document.getElementById('themeText');
    if (themeIcon && themeText) {
        if (newTheme === 'dark') {
            themeIcon.className = 'bi bi-moon-stars';
            themeText.textContent = 'Dark Theme';
        } else {
            themeIcon.className = 'bi bi-sun';
            themeText.textContent = 'Light Theme';
        }
    }
    localStorage.setItem('theme', newTheme);
}

// Open Profile Settings Modal
function openProfileSettings(e) {
    e.preventDefault();
    var modal = new bootstrap.Modal(document.getElementById('profileModal'));
    
    var savedName = localStorage.getItem('userName') || '';
    var savedEmail = localStorage.getItem('userEmail') || '';
    var savedCurrency = localStorage.getItem('userCurrency') || 'USD';
    
    document.getElementById('userName').value = savedName;
    document.getElementById('userEmail').value = savedEmail;
    document.getElementById('userCurrency').value = savedCurrency;
    
    modal.show();
}

// Save Profile Settings
function saveProfileSettings() {
    var name = document.getElementById('userName').value;
    var email = document.getElementById('userEmail').value;
    var currency = document.getElementById('userCurrency').value;
    
    localStorage.setItem('userName', name);
    localStorage.setItem('userEmail', email);
    localStorage.setItem('userCurrency', currency);
    
    var modal = bootstrap.Modal.getInstance(document.getElementById('profileModal'));
    modal.hide();
    
    alert('Profile settings saved successfully!');
}

function openBudgetSettings(event) {
    event.preventDefault();
    
    // Show the modal first
    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    modal.show();
    
    // Load current budget data and status
    Promise.all([
        fetch('/budget/get').then(r => r.json()),
        fetch('/budget/status').then(r => r.json())
    ])
    .then(([budgetData, statusData]) => {
        // Populate main budget
        if (budgetData.monthlyBudget) {
            document.getElementById('monthlyBudget').value = budgetData.monthlyBudget;
            
            // Show delete button if budget exists
            const actionsDiv = document.getElementById('budgetActions');
            if (actionsDiv) {
                actionsDiv.style.display = 'block';
            }
        }
        
        // Populate category limits
        if (budgetData.categories) {
            if (budgetData.categories['Food']) {
                document.getElementById('foodLimit').value = budgetData.categories['Food'];
            }
            if (budgetData.categories['Bills']) {
                document.getElementById('billsLimit').value = budgetData.categories['Bills'];
            }
            if (budgetData.categories['Transport']) {
                document.getElementById('transportLimit').value = budgetData.categories['Transport'];
            }
            if (budgetData.categories['Entertainment']) {
                document.getElementById('entertainmentLimit').value = budgetData.categories['Entertainment'];
            }
        }
        
        // Show current status if budget exists
        if (statusData.hasBudget) {
            const statusDiv = document.getElementById('currentBudgetStatus');
            if (statusDiv) {
                statusDiv.classList.remove('d-none');
                
                document.getElementById('statusSpent').textContent = `$${statusData.spent.toFixed(2)}`;
                document.getElementById('statusRemaining').textContent = `$${statusData.remaining.toFixed(2)}`;
                
                const progressBar = document.getElementById('statusProgress');
                progressBar.style.width = `${Math.min(statusData.percentage, 100)}%`;
                
                // Update progress bar color
                progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');
                if (statusData.percentage < 70) {
                    progressBar.classList.add('bg-success');
                } else if (statusData.percentage < 90) {
                    progressBar.classList.add('bg-warning');
                } else {
                    progressBar.classList.add('bg-danger');
                }
                
                // Update remaining text color
                const remainingEl = document.getElementById('statusRemaining');
                remainingEl.classList.remove('text-success', 'text-danger');
                remainingEl.classList.add(statusData.remaining >= 0 ? 'text-success' : 'text-danger');
                
                // Display category breakdowns
                if (statusData.categories && statusData.categories.length > 0) {
                    displayCategoryBreakdown(statusData.categories);
                }
            }
        }
    })
    .catch(error => {
        console.error('Error loading budget:', error);
    });
}

function displayCategoryBreakdown(categories) {
    const breakdownDiv = document.getElementById('categoryBreakdown');
    if (!breakdownDiv) return;
    
    let html = '<h6 class="mb-3">Category Breakdown</h6>';
    
    categories.forEach(cat => {
        if (cat.limit > 0) {
            const percentage = Math.min(cat.percentage, 100);
            let colorClass = 'success';
            if (cat.percentage >= 90) colorClass = 'danger';
            else if (cat.percentage >= 70) colorClass = 'warning';
            
            html += `
                <div class="mb-3">
                    <div class="d-flex justify-content-between mb-1">
                        <small class="fw-bold">${cat.name}</small>
                        <small>$${cat.spent.toFixed(2)} / $${cat.limit.toFixed(2)}</small>
                    </div>
                    <div class="progress" style="height: 6px;">
                        <div class="progress-bar bg-${colorClass}" 
                             role="progressbar" 
                             style="width: ${percentage}%">
                        </div>
                    </div>
                </div>
            `;
        }
    });
    
    breakdownDiv.innerHTML = html;
}

function saveBudgetSettings() {
    const monthlyBudget = document.getElementById('monthlyBudget').value;
    const budgetAlerts = document.getElementById('budgetAlerts').checked;
    
    // Get category limits
    const categoryLimits = {};
    const foodLimit = document.getElementById('foodLimit').value;
    const billsLimit = document.getElementById('billsLimit').value;
    const transportLimit = document.getElementById('transportLimit').value;
    const entertainmentLimit = document.getElementById('entertainmentLimit').value;
    
    if (foodLimit && parseFloat(foodLimit) > 0) categoryLimits['Food'] = parseFloat(foodLimit);
    if (billsLimit && parseFloat(billsLimit) > 0) categoryLimits['Bills'] = parseFloat(billsLimit);
    if (transportLimit && parseFloat(transportLimit) > 0) categoryLimits['Transport'] = parseFloat(transportLimit);
    if (entertainmentLimit && parseFloat(entertainmentLimit) > 0) categoryLimits['Entertainment'] = parseFloat(entertainmentLimit);
    
    // Validate input
    if (!monthlyBudget || parseFloat(monthlyBudget) <= 0) {
        showAlert('Please enter a valid budget amount', 'danger');
        return;
    }
    
    // Check that category limits don't exceed total budget
    const totalCategoryLimits = Object.values(categoryLimits).reduce((a, b) => a + b, 0);
    const totalBudget = parseFloat(monthlyBudget);
    
    if (totalCategoryLimits > totalBudget) {
        showAlert(`Category limits ($${totalCategoryLimits.toFixed(2)}) exceed total budget ($${totalBudget.toFixed(2)})`, 'danger');
        return;
    }
    
    // Prepare data
    const budgetData = {
        monthlyBudget: totalBudget,
        budgetAlerts: budgetAlerts,
        categoryLimits: categoryLimits
    };
    
    // Save to server
    fetch('/budget/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(budgetData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Budget settings saved successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('budgetModal'));
            modal.hide();
            
            // Reload page to show updated budget
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.error || 'Failed to save budget settings', 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving budget:', error);
        showAlert('Failed to save budget settings', 'danger');
    });
}

function deleteBudget() {
    if (!confirm('Are you sure you want to remove your budget? This will also remove all category limits. This action cannot be undone.')) {
        return;
    }
    
    fetch('/budget/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Budget removed successfully!', 'success');
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } else {
            showAlert(data.error || 'Failed to remove budget', 'danger');
        }
    })
    .catch(error => {
        console.error('Error removing budget:', error);
        showAlert('Failed to remove budget', 'danger');
    });
}

// Helper function to show alerts
function showAlert(message, type) {
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        <i class="bi bi-info-circle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Find or create flash container
    let flashContainer = document.querySelector('.flash-container');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-container';
        const main = document.querySelector('main');
        main.parentNode.insertBefore(flashContainer, main);
    }
    
    // Clear existing alerts and add new one
    flashContainer.innerHTML = '';
    flashContainer.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, 5000);
}

// Load budget status on page load (for dashboard)
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a page that needs budget status
    const budgetWidget = document.getElementById('budgetWidget');
    if (budgetWidget) {
        loadBudgetStatus();
    }
});

function loadBudgetStatus() {
    fetch('/budget/status')
        .then(response => response.json())
        .then(data => {
            if (data.hasBudget) {
                updateBudgetWidget(data);
            }
        })
        .catch(error => {
            console.error('Error loading budget status:', error);
        });
}

function updateBudgetWidget(data) {
    const budgetWidget = document.getElementById('budgetWidget');
    if (!budgetWidget) return;
    
    // Update progress bar
    const progressBar = budgetWidget.querySelector('.progress-bar');
    if (progressBar) {
        progressBar.style.width = `${Math.min(data.percentage, 100)}%`;
        
        // Change color based on percentage
        progressBar.classList.remove('bg-success', 'bg-warning', 'bg-danger');
        if (data.percentage < 70) {
            progressBar.classList.add('bg-success');
        } else if (data.percentage < 90) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-danger');
        }
    }
    
    // Update text
    const budgetText = budgetWidget.querySelector('.budget-text');
    if (budgetText) {
        budgetText.innerHTML = `
            <strong>$${data.spent.toFixed(2)}</strong> of 
            <strong>$${data.total.toFixed(2)}</strong> spent
            ${data.isOverBudget ? '<span class="text-danger ms-2">(Over Budget!)</span>' : ''}
        `;
    }
    
    // Update remaining amount
    const remainingText = budgetWidget.querySelector('.remaining-text');
    if (remainingText) {
        const remainingClass = data.remaining >= 0 ? 'text-success' : 'text-danger';
        remainingText.innerHTML = `
            <span class="${remainingClass}">
                ${data.remaining >= 0 ? '$' + data.remaining.toFixed(2) + ' remaining' : 'Over by $' + Math.abs(data.remaining).toFixed(2)}
            </span>
        `;
    }
}
// ============================================================================
// NOTIFICATION SETTINGS
// ============================================================================

// Open Notification Settings Modal
function openNotificationSettings(e) {
    e.preventDefault();
    var modal = new bootstrap.Modal(document.getElementById('notificationModal'));
    
    document.getElementById('emailNotifications').checked = localStorage.getItem('emailNotifications') !== 'false';
    document.getElementById('budgetWarnings').checked = localStorage.getItem('budgetWarnings') !== 'false';
    document.getElementById('weeklyReports').checked = localStorage.getItem('weeklyReports') === 'true';
    document.getElementById('monthlyReports').checked = localStorage.getItem('monthlyReports') !== 'false';
    
    modal.show();
}

// Save Notification Settings
function saveNotificationSettings() {
    localStorage.setItem('emailNotifications', document.getElementById('emailNotifications').checked);
    localStorage.setItem('budgetWarnings', document.getElementById('budgetWarnings').checked);
    localStorage.setItem('weeklyReports', document.getElementById('weeklyReports').checked);
    localStorage.setItem('monthlyReports', document.getElementById('monthlyReports').checked);
    
    var modal = bootstrap.Modal.getInstance(document.getElementById('notificationModal'));
    modal.hide();
    
    alert('Notification settings saved successfully!');
}

// Export Data
function exportData(e) {
    e.preventDefault();
    
    var data = {
        profile: {
            name: localStorage.getItem('userName') || '',
            email: localStorage.getItem('userEmail') || '',
            currency: localStorage.getItem('userCurrency') || 'USD'
        },
        settings: {
            theme: localStorage.getItem('theme') || 'dark',
            notifications: {
                email: localStorage.getItem('emailNotifications') !== 'false',
                budget: localStorage.getItem('budgetWarnings') !== 'false',
                weekly: localStorage.getItem('weeklyReports') === 'true',
                monthly: localStorage.getItem('monthlyReports') !== 'false'
            }
        },
        transactions: JSON.parse(localStorage.getItem('transactions') || '[]')
    };
    
    var dataStr = JSON.stringify(data, null, 2);
    var dataBlob = new Blob([dataStr], { type: 'application/json' });
    var url = URL.createObjectURL(dataBlob);
    var link = document.createElement('a');
    link.href = url;
    link.download = 'financial-tracker-data.json';
    link.click();
    URL.revokeObjectURL(url);
}

// Change Profile Picture
function changeProfilePicture() {
    alert('Profile picture upload would be implemented here with a file input');
}

// Handle Logout
function handleLogout(e) {
    e.preventDefault();
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}

// Load theme on page load
document.addEventListener('DOMContentLoaded', function() {
    var savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', savedTheme);
    
    var themeIcon = document.getElementById('themeIcon');
    var themeText = document.getElementById('themeText');
    
    if (themeIcon && themeText) {
        if (savedTheme === 'dark') {
            themeIcon.className = 'bi bi-moon-stars';
            themeText.textContent = 'Dark Theme';
        } else {
            themeIcon.className = 'bi bi-sun';
            themeText.textContent = 'Light Theme';
        }
    }
});