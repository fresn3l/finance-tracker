// Main JavaScript for Finance Tracker Web App

let monthlyChart = null;
let categoryChart = null;
let topCategoriesChart = null;
let currentPage = 1;
const itemsPerPage = 50;

// Initialize app
document.addEventListener('DOMContentLoaded', async () => {
    setupTabs();
    setupFileUpload();
    await loadDashboard();
    await loadTransactions();
    await loadCategories();
});

// Tab Navigation
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            
            // Update active tab button
            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update active tab content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === targetTab) {
                    content.classList.add('active');
                }
            });
        });
    });
}

// File Upload Setup
function setupFileUpload() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.getElementById('file-upload-area');
    const fileName = document.getElementById('file-name');
    const importBtn = document.getElementById('import-btn');

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('dragover');
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('dragover');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect();
        }
    });

    fileInput.addEventListener('change', handleFileSelect);

    function handleFileSelect() {
        if (fileInput.files.length > 0) {
            fileName.textContent = fileInput.files[0].name;
            importBtn.disabled = false;
        } else {
            fileName.textContent = '';
            importBtn.disabled = true;
        }
    }
}

// Import CSV
async function importCSV() {
    const fileInput = document.getElementById('file-input');
    const autoCategorize = document.getElementById('auto-categorize').checked;
    const checkDuplicates = document.getElementById('check-duplicates').checked;
    const accountName = document.getElementById('account-name').value || null;
    const statusDiv = document.getElementById('import-status');

    if (!fileInput.files.length) {
        showStatus('Please select a file', 'error');
        return;
    }

    showLoading(true);
    statusDiv.style.display = 'none';

    try {
        // Use Eel's file dialog or get file path
        let filePath;
        try {
            // Try to get file path from Eel file dialog
            filePath = await eel.select_file()();
        } catch (e) {
            // Fallback: use file input
            const file = fileInput.files[0];
            // For Eel, we need the actual file path, not just the name
            // This will work if the file is in a known location
            filePath = file.name;
        }
        
        if (!filePath) {
            // If no file selected via dialog, use the file input
            const file = fileInput.files[0];
            filePath = file.name;
        }
        
        const result = await eel.import_csv_file(
            filePath,
            accountName,
            autoCategorize,
            false, // overwrite
            checkDuplicates,
            true  // skip duplicates
        )();

        if (result.success) {
            showStatus(`Successfully imported ${result.new_transactions} transactions!`, 'success');
            
            // Reset form
            fileInput.value = '';
            document.getElementById('file-name').textContent = '';
            document.getElementById('import-btn').disabled = true;
            
            // Reload data
            await loadDashboard();
            await loadTransactions();
            await loadCategories();
        } else {
            showStatus(`Error: ${result.error || 'Unknown error'}`, 'error');
        }
        
    } catch (error) {
        showStatus(`Error: ${error.message || error}`, 'error');
    } finally {
        showLoading(false);
    }
}

function showStatus(message, type) {
    const statusDiv = document.getElementById('import-status');
    statusDiv.textContent = message;
    statusDiv.className = type;
    statusDiv.style.display = 'block';
}

// Load Dashboard
async function loadDashboard() {
    try {
        const stats = await eel.get_overall_stats()();
        updateStats(stats);
        
        const summaries = await eel.get_monthly_summaries()();
        updateMonthlySummaries(summaries);
        updateMonthlyChart(summaries);
        
        const categoryBreakdown = await eel.get_category_breakdown()();
        updateCategoryChart(categoryBreakdown);
    } catch (error) {
        console.error('Error loading dashboard:', error);
    }
}

function updateStats(stats) {
    document.getElementById('total-income').textContent = formatCurrency(stats.total_income);
    document.getElementById('total-expenses').textContent = formatCurrency(stats.total_expenses);
    
    const netAmount = parseFloat(stats.net_amount);
    const netEl = document.getElementById('net-amount');
    netEl.textContent = formatCurrency(stats.net_amount);
    netEl.className = 'stat-value ' + (netAmount >= 0 ? 'positive' : 'negative');
    
    const savingsRate = stats.savings_rate || 0;
    document.getElementById('savings-rate').textContent = savingsRate.toFixed(1) + '%';
}

function updateMonthlyChart(summaries) {
    const ctx = document.getElementById('monthly-chart').getContext('2d');
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    const labels = summaries.map(s => `${s.year}-${String(s.month).padStart(2, '0')}`);
    const income = summaries.map(s => parseFloat(s.total_income));
    const expenses = summaries.map(s => parseFloat(s.total_expenses));
    
    monthlyChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Income',
                data: income,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4
            }, {
                label: 'Expenses',
                data: expenses,
                borderColor: '#ef4444',
                backgroundColor: 'rgba(239, 68, 68, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function updateCategoryChart(breakdown) {
    const ctx = document.getElementById('category-chart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    const categories = Object.keys(breakdown).slice(0, 10);
    const amounts = categories.map(cat => parseFloat(breakdown[cat]));
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories,
            datasets: [{
                data: amounts,
                backgroundColor: [
                    '#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.label + ': $' + context.parsed.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function updateMonthlySummaries(summaries) {
    const container = document.getElementById('monthly-summaries');
    container.innerHTML = '';
    
    summaries.slice(0, 6).forEach(summary => {
        const item = document.createElement('div');
        item.className = 'monthly-summary-item';
        item.innerHTML = `
            <div>
                <strong>${summary.year}-${String(summary.month).padStart(2, '0')}</strong>
                <div style="font-size: 12px; color: #64748b; margin-top: 5px;">
                    ${summary.transaction_count} transactions
                </div>
            </div>
            <div class="month-summary">
                <div>
                    <div class="month-summary-label">Income</div>
                    <div class="month-summary-value" style="color: #10b981">${formatCurrency(summary.total_income)}</div>
                </div>
                <div>
                    <div class="month-summary-label">Expenses</div>
                    <div class="month-summary-value" style="color: #ef4444">${formatCurrency(summary.total_expenses)}</div>
                </div>
                <div>
                    <div class="month-summary-label">Net</div>
                    <div class="month-summary-value" style="color: ${parseFloat(summary.net_amount) >= 0 ? '#10b981' : '#ef4444'}">
                        ${formatCurrency(summary.net_amount)}
                    </div>
                </div>
            </div>
        `;
        container.appendChild(item);
    });
}

// Load Transactions
async function loadTransactions(page = 1) {
    try {
        const transactions = await eel.get_transactions(page, itemsPerPage)();
        displayTransactions(transactions);
        updatePagination(transactions.length);
    } catch (error) {
        console.error('Error loading transactions:', error);
    }
}

function displayTransactions(transactions) {
    const tbody = document.getElementById('transactions-tbody');
    tbody.innerHTML = '';
    
    if (transactions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No transactions found.</td></tr>';
        return;
    }
    
    transactions.forEach(txn => {
        const row = document.createElement('tr');
        const amount = parseFloat(txn.amount);
        const isExpense = amount < 0;
        
        row.innerHTML = `
            <td>${txn.date}</td>
            <td>${txn.description}</td>
            <td>${txn.category ? txn.category.name : '<span style="color: #94a3b8">Uncategorized</span>'}</td>
            <td style="color: ${isExpense ? '#ef4444' : '#10b981'}; font-weight: 600">
                ${isExpense ? '-' : '+'}${formatCurrency(Math.abs(amount))}
            </td>
            <td><span class="badge">${txn.transaction_type}</span></td>
        `;
        tbody.appendChild(row);
    });
}

// Load Categories
async function loadCategories() {
    try {
        const patterns = await eel.get_spending_patterns()();
        displayTopCategories(patterns);
        displayCategoriesList(patterns);
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}

function displayTopCategories(patterns) {
    const ctx = document.getElementById('top-categories-chart').getContext('2d');
    
    if (topCategoriesChart) {
        topCategoriesChart.destroy();
    }
    
    const top10 = patterns.slice(0, 10);
    const labels = top10.map(p => p.category);
    const amounts = top10.map(p => parseFloat(p.total_amount));
    
    topCategoriesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Spending',
                data: amounts,
                backgroundColor: '#2563eb'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            }
        }
    });
}

function displayCategoriesList(patterns) {
    const container = document.getElementById('categories-list');
    container.innerHTML = '<h3 style="margin-bottom: 20px;">All Categories</h3>';
    
    patterns.forEach(pattern => {
        const item = document.createElement('div');
        item.className = 'category-item';
        item.innerHTML = `
            <div>
                <strong>${pattern.category}</strong>
                <div style="font-size: 12px; color: #64748b; margin-top: 5px;">
                    ${pattern.transaction_count} transactions • Avg: ${formatCurrency(pattern.average_transaction)}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 20px; font-weight: 600">${formatCurrency(pattern.total_amount)}</div>
                <div style="font-size: 12px; color: #64748b">${pattern.percentage_of_total ? pattern.percentage_of_total.toFixed(1) + '%' : 'N/A'}</div>
            </div>
        `;
        container.appendChild(item);
    });
}

// Export Transactions
async function exportTransactions() {
    try {
        const result = await eel.export_transactions()();
        alert(`Transactions exported to: ${result}`);
    } catch (error) {
        alert(`Error exporting: ${error.message || error}`);
    }
}

// Utility Functions
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function showLoading(show) {
    document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
}

function updatePagination(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pagination = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }
    
    let html = '';
    for (let i = 1; i <= totalPages; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="goToPage(${i})">${i}</button>`;
    }
    pagination.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadTransactions(page);
}

