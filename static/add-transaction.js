// Initialize page
document.addEventListener('DOMContentLoaded', function() {
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('date').value = today;
    
    // Initialize category visibility - show expense, hide income by default
    const expenseCat = document.getElementById('expenseCategories');
    const incomeCat = document.getElementById('incomeCategories');
    expenseCat.removeAttribute('style');
    incomeCat.setAttribute('style', 'display: none;');
    
    // Initialize category preview
    updateCategoryPreview();
});

// Transaction type toggle
document.querySelectorAll('input[name="type"]').forEach(radio => {
    radio.addEventListener('change', function() {
        const expenseCat = document.getElementById('expenseCategories');
        const incomeCat = document.getElementById('incomeCategories');
        const categorySelect = document.getElementById('category');
        
        console.log('Transaction type changed to:', this.value);
        console.log('Expense optgroup:', expenseCat);
        console.log('Income optgroup:', incomeCat);
        
        if (this.value === 'EXPENSE') {
            expenseCat.removeAttribute('style');
            incomeCat.setAttribute('style', 'display: none;');
            console.log('Showing expense categories');
        } else {
            expenseCat.setAttribute('style', 'display: none;');
            incomeCat.removeAttribute('style');
            console.log('Showing income categories');
            console.log('Income options count:', incomeCat.querySelectorAll('option').length);
        }
        categorySelect.value = '';
        updateCategoryPreview();
    });
});

// Category selection preview
document.getElementById('category').addEventListener('change', function() {
    updateCategoryPreview();
});

function updateCategoryPreview() {
    const categorySelect = document.getElementById('category');
    const preview = document.getElementById('categoryPreview');
    const badge = document.getElementById('categoryBadge');
    const dot = document.getElementById('categoryColorDot');
    const name = document.getElementById('categoryPreviewName');
    
    if (categorySelect.value) {
        const selectedOption = categorySelect.options[categorySelect.selectedIndex];
        const color = selectedOption.getAttribute('data-color') || '#6c757d';
        const categoryName = selectedOption.value;
        
        // Show preview
        preview.style.display = 'block';
        badge.style.backgroundColor = color + '20'; // 20% opacity
        badge.style.borderColor = color;
        badge.style.border = `2px solid ${color}`;
        dot.style.backgroundColor = color;
        name.textContent = categoryName;
        name.style.color = color;
    } else {
        preview.style.display = 'none';
    }
}

// Recurring toggle
document.getElementById('isRecurring').addEventListener('change', function() {
    document.getElementById('recurringOptions').style.display = this.checked ? 'block' : 'none';
    if (!this.checked) {
        document.getElementById('recurringFrequency').value = '';
        document.getElementById('recurringEndDate').value = '';
    }
});

// Receipt preview
document.getElementById('receipt').addEventListener('change', function(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('receiptPreview');
    
    if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = `<img src="${e.target.result}" class="img-thumbnail mt-2" style="max-width: 200px;" alt="Receipt Preview">`;
        };
        reader.readAsDataURL(file);
    } else if (file) {
        preview.innerHTML = `<p class="text-muted mt-2"><i class="bi bi-file-earmark-pdf"></i> ${file.name}</p>`;
    } else {
        preview.innerHTML = '';
    }
});

// Quick amount setter
function setQuickAmount(amount) {
    document.getElementById('amount').value = amount;
}

// Template filler
function fillTemplate(name, category, amount) {
    document.getElementById('name').value = name;
    document.getElementById('category').value = category;
    document.getElementById('amount').value = amount;
    updateCategoryPreview();
}

// Calculator functions
let calcValue = '0';
let calcOperator = '';
let calcPrevValue = '';

function openCalculator() {
    const modal = new bootstrap.Modal(document.getElementById('calculatorModal'));
    calcValue = '0';
    calcOperator = '';
    calcPrevValue = '';
    document.getElementById('calcDisplay').value = calcValue;
    modal.show();
}

function calcInput(val) {
    if (['+', '-', '*', '/'].includes(val)) {
        if (calcValue !== '0') {
            calcOperator = val;
            calcPrevValue = calcValue;
            calcValue = '0';
        }
    } else {
        calcValue = calcValue === '0' ? val : calcValue + val;
    }
    document.getElementById('calcDisplay').value = calcValue;
}

function calcClear() {
    calcValue = '0';
    calcOperator = '';
    calcPrevValue = '';
    document.getElementById('calcDisplay').value = calcValue;
}

function calcEquals() {
    if (calcOperator && calcPrevValue) {
        const a = parseFloat(calcPrevValue);
        const b = parseFloat(calcValue);
        let result = 0;
        
        switch(calcOperator) {
            case '+': result = a + b; break;
            case '-': result = a - b; break;
            case '*': result = a * b; break;
            case '/': result = b !== 0 ? a / b : 0; break;
        }
        
        document.getElementById('amount').value = result.toFixed(2);
        bootstrap.Modal.getInstance(document.getElementById('calculatorModal')).hide();
    }
}