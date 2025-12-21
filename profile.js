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

// Open Budget Settings Modal
function openBudgetSettings(e) {
    e.preventDefault();
    var modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    
    document.getElementById('monthlyBudget').value = localStorage.getItem('monthlyBudget') || '';
    document.getElementById('foodLimit').value = localStorage.getItem('foodLimit') || '';
    document.getElementById('billsLimit').value = localStorage.getItem('billsLimit') || '';
    document.getElementById('transportLimit').value = localStorage.getItem('transportLimit') || '';
    document.getElementById('entertainmentLimit').value = localStorage.getItem('entertainmentLimit') || '';
    document.getElementById('budgetAlerts').checked = localStorage.getItem('budgetAlerts') !== 'false';
    
    modal.show();
}

// Save Budget Settings
function saveBudgetSettings() {
    localStorage.setItem('monthlyBudget', document.getElementById('monthlyBudget').value);
    localStorage.setItem('foodLimit', document.getElementById('foodLimit').value);
    localStorage.setItem('billsLimit', document.getElementById('billsLimit').value);
    localStorage.setItem('transportLimit', document.getElementById('transportLimit').value);
    localStorage.setItem('entertainmentLimit', document.getElementById('entertainmentLimit').value);
    localStorage.setItem('budgetAlerts', document.getElementById('budgetAlerts').checked);
    
    var modal = bootstrap.Modal.getInstance(document.getElementById('budgetModal'));
    modal.hide();
    
    alert('Budget settings saved successfully!');
}

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
        budget: {
            monthly: localStorage.getItem('monthlyBudget') || '',
            limits: {
                food: localStorage.getItem('foodLimit') || '',
                bills: localStorage.getItem('billsLimit') || '',
                transport: localStorage.getItem('transportLimit') || '',
                entertainment: localStorage.getItem('entertainmentLimit') || ''
            }
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
        alert('Logout functionality would redirect to login page');
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