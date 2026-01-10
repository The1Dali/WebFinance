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

// ============================================================================
// BUDGET SETTINGS - Updated to use database instead of localStorage
// ============================================================================

// Open Budget Settings Modal
function openBudgetSettings(event) {
    event.preventDefault();
    
    // Load current budget from database
    fetch('/budget/get')
        .then(response => response.json())
        .then(data => {
            if (data.amount) {
                document.getElementById('monthlyBudget').value = data.amount;
            }
        })
        .catch(error => {
            console.error('Error loading budget:', error);
        });
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    modal.show();
}

// Save Budget Settings
function saveBudgetSettings() {
    const monthlyBudget = document.getElementById('monthlyBudget').value;
    
    // Validate
    if (!monthlyBudget || parseFloat(monthlyBudget) <= 0) {
        alert('Please enter a valid budget amount');
        return;
    }
    
    // Save to server
    fetch('/budget/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            monthlyBudget: parseFloat(monthlyBudget)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Budget saved successfully!');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('budgetModal'));
            modal.hide();
            
            // Reload page to show updated budget
            window.location.reload();
        } else {
            alert('Error: ' + (data.error || 'Failed to save budget'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to save budget');
    });
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