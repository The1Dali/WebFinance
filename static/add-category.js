// Predefined color palettes
const INCOME_COLORS = [
    '#28a745', // Green
    '#20c997', // Teal
    '#17a2b8', // Cyan
    '#00d084', // Emerald
    '#4caf50', // Light Green
    '#66bb6a', // Lime
    '#81c784', // Pale Green
    '#00bfa5', // Turquoise
];

const EXPENSE_COLORS = [
    '#dc3545', // Red
    '#e74c3c', // Crimson
    '#c82333', // Dark Red
    '#ff6b6b', // Light Red
    '#f44336', // Material Red
    '#ef5350', // Pink Red
    '#e57373', // Rose
    '#ff5252', // Bright Red
];

let colorIndex = { INCOME: 0, EXPENSE: 0 };

// Get next color from palette
function getNextColor(type) {
    if (type === 'INCOME') {
        const color = INCOME_COLORS[colorIndex.INCOME % INCOME_COLORS.length];
        colorIndex.INCOME++;
        return color;
    } else {
        const color = EXPENSE_COLORS[colorIndex.EXPENSE % EXPENSE_COLORS.length];
        colorIndex.EXPENSE++;
        return color;
    }
}

// Reset to default color based on type
function resetDefaultColor() {
    const type = document.getElementById('categoryType').value;
    if (type) {
        document.getElementById('categoryColor').value = getNextColor(type);
    } else {
        alert('Please select a transaction type first');
    }
}

// Update color when type changes
document.getElementById('categoryType').addEventListener('change', function() {
    resetDefaultColor();
});

// Load categories on page load
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
});

// Load all categories
async function loadCategories() {
    try {
        const response = await fetch('/api/categories');
        const categories = await response.json();
        
        const expenseDiv = document.getElementById('expenseCategories');
        const incomeDiv = document.getElementById('incomeCategories');
        
        const expenseCategories = categories.filter(c => c.type === 'EXPENSE');
        const incomeCategories = categories.filter(c => c.type === 'INCOME');
        
        // Update color indices based on existing categories
        colorIndex.EXPENSE = expenseCategories.length;
        colorIndex.INCOME = incomeCategories.length;
        
        // Update counts
        document.getElementById('expenseCount').textContent = expenseCategories.length;
        document.getElementById('incomeCount').textContent = incomeCategories.length;
        
        // Render expense categories
        if (expenseCategories.length === 0) {
            expenseDiv.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>No expense categories yet</p>
                </div>
            `;
        } else {
            expenseDiv.innerHTML = expenseCategories.map(cat => renderCategory(cat)).join('');
        }
        
        // Render income categories
        if (incomeCategories.length === 0) {
            incomeDiv.innerHTML = `
                <div class="empty-state">
                    <i class="bi bi-inbox"></i>
                    <p>No income categories yet</p>
                </div>
            `;
        } else {
            incomeDiv.innerHTML = incomeCategories.map(cat => renderCategory(cat)).join('');
        }
        
    } catch (error) {
        console.error('Error loading categories:', error);
        alert('Failed to load categories');
    }
}

// Render a single category
function renderCategory(category) {
    const color = category.color || '#6c757d';
    return `
        <div class="category-item">
            <div class="d-flex align-items-center">
                <span class="category-color-dot" style="background-color: ${color}"></span>
                <strong>${escapeHtml(category.name)}</strong>
            </div>
            <div class="category-actions">
                <button class="btn btn-sm btn-outline-primary" 
                        onclick="openEditModal(${category.id}, '${escapeHtml(category.name)}', '${category.type}', '${color}')">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger" 
                        onclick="openDeleteModal(${category.id}, '${escapeHtml(category.name)}')">
                    <i class="bi bi-trash"></i>
                </button>
            </div>
        </div>
    `;
}

// Add new category
async function addCategory(event) {
    event.preventDefault();
    
    const name = document.getElementById('categoryName').value.trim();
    const type = document.getElementById('categoryType').value;
    const color = document.getElementById('categoryColor').value;
    
    if (!name || !type) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/categories/add', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, type, color })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Reset form
            document.getElementById('addCategoryForm').reset();
            document.getElementById('categoryColor').value = '#6c757d';
            
            // Reload categories
            loadCategories();
            
            // Show success message
            showToast('Category added successfully!', 'success');
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error adding category:', error);
        alert('Failed to add category');
    }
}

// Open edit modal
function openEditModal(id, name, type, color) {
    document.getElementById('editCategoryId').value = id;
    document.getElementById('editCategoryName').value = name;
    document.getElementById('editCategoryType').value = type;
    document.getElementById('editCategoryColor').value = color;
    
    const modal = new bootstrap.Modal(document.getElementById('editCategoryModal'));
    modal.show();
}

// Save edited category
async function saveEditCategory(event) {
    event.preventDefault();
    
    const id = document.getElementById('editCategoryId').value;
    const name = document.getElementById('editCategoryName').value.trim();
    const color = document.getElementById('editCategoryColor').value;
    
    try {
        const response = await fetch('/api/categories/edit', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id, name, color })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('editCategoryModal')).hide();
            
            // Reload categories
            loadCategories();
            
            showToast('Category updated successfully!', 'success');
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error updating category:', error);
        alert('Failed to update category');
    }
}

// Open delete modal
async function openDeleteModal(id, name) {
    document.getElementById('deleteCategoryId').value = id;
    document.getElementById('deleteCategoryName').textContent = name;
    
    // Check if category has transactions
    try {
        const response = await fetch(`/api/categories/${id}/count`);
        const result = await response.json();
        
        if (result.count > 0) {
            document.getElementById('deleteWarning').style.display = 'block';
            document.getElementById('transactionCount').textContent = result.count;
        } else {
            document.getElementById('deleteWarning').style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking category usage:', error);
    }
    
    const modal = new bootstrap.Modal(document.getElementById('deleteCategoryModal'));
    modal.show();
}

// Confirm delete category
async function confirmDeleteCategory() {
    const id = document.getElementById('deleteCategoryId').value;
    
    try {
        const response = await fetch('/api/categories/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ id })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('deleteCategoryModal')).hide();
            
            // Reload categories
            loadCategories();
            
            showToast('Category deleted successfully!', 'success');
        } else {
            alert('Error: ' + result.error);
        }
    } catch (error) {
        console.error('Error deleting category:', error);
        alert('Failed to delete category');
    }
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Utility: Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} position-fixed top-0 start-50 translate-middle-x mt-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <i class="bi bi-check-circle me-2"></i>${message}
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}