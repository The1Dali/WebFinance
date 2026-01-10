// Function that receives data from inline script
function initializeCharts(histogramData, incomeChartData, expenseChartData) {
    // Histogram Chart
    const ctx = document.getElementById('histogramChart').getContext('2d');
    const histogramChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: histogramData.labels,
            datasets: [{
                label: 'Income',
                data: histogramData.income,
                backgroundColor: '#28a745',
                borderColor: '#1e7e34',
                borderWidth: 1
            }, {
                label: 'Expenses',
                data: histogramData.expenses,
                backgroundColor: '#dc3545',
                borderColor: '#c82333',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                legend: { position: 'bottom' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                        }
                    }
                }
            }
        }
    });
    
    // Income Pie Chart
    if (incomeChartData.labels.length > 0) {
        const incomeCtx = document.getElementById('incomePieChart').getContext('2d');
        new Chart(incomeCtx, {
            type: 'doughnut',
            data: {
                labels: incomeChartData.labels,
                datasets: [{
                    data: incomeChartData.values,
                    backgroundColor: incomeChartData.colors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = '$' + context.parsed.toLocaleString();
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    } else {
        document.getElementById('incomePieChart').style.display = 'none';
        document.getElementById('incomeEmpty').style.display = 'block';
    }
    
    // Expense Pie Chart
    if (expenseChartData.labels.length > 0) {
        const expensesCtx = document.getElementById('expensesPieChart').getContext('2d');
        new Chart(expensesCtx, {
            type: 'doughnut',
            data: {
                labels: expenseChartData.labels,
                datasets: [{
                    data: expenseChartData.values,
                    backgroundColor: expenseChartData.colors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { position: 'right' },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = '$' + context.parsed.toLocaleString();
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return label + ': ' + value + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    } else {
        document.getElementById('expensesPieChart').style.display = 'none';
        document.getElementById('expenseEmpty').style.display = 'block';
    }
}

function initializeFilters(currentView, currentPeriod) {
    updatePeriodOptions(currentView, currentPeriod);
    
    document.getElementById('timeView').addEventListener('change', function(e) {
        const view = e.target.value;
        const period = document.getElementById('timePeriod').value;
        window.location.href = `/statistics?view=${view}&period=${period}`;
    });
    
    document.getElementById('timePeriod').addEventListener('change', function(e) {
        const view = document.getElementById('timeView').value;
        const period = e.target.value;
        window.location.href = `/statistics?view=${view}&period=${period}`;
    });
}

function updatePeriodOptions(view, currentPeriod) {
    const periodSelect = document.getElementById('timePeriod');
    periodSelect.innerHTML = '';
    
    let options = [];
    switch(view) {
        case 'daily':
            options = [
                { value: 'current', label: 'Current Week' },
                { value: 'last', label: 'Last Week' },
                { value: 'twoWeeks', label: '2 Weeks Ago' }
            ];
            break;
        case 'weekly':
            options = [
                { value: 'current', label: 'Current Month' },
                { value: 'last', label: 'Last Month' },
                { value: 'twoMonths', label: '2 Months Ago' }
            ];
            break;
        case 'monthly':
            options = [
                { value: 'current', label: 'Current Year' },
                { value: 'last', label: 'Last Year' },
                { value: 'twoYears', label: '2 Years Ago' }
            ];
            break;
        case 'annual':
            options = [
                { value: 'all', label: 'All Years' },
                { value: 'last5', label: 'Last 5 Years' },
                { value: 'last10', label: 'Last 10 Years' }
            ];
            break;
    }
    
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.label;
        if (opt.value === currentPeriod) {
            option.selected = true;
        }
        periodSelect.appendChild(option);
    });
}