(function () {
    document.addEventListener('DOMContentLoaded', function () {

        // === Expenses by Category ===
        fetch('/api/expenses_by_category')
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById('expensesChart').getContext('2d');
                new Chart(ctx, {
                    type: 'pie',
                    data: {
                        labels: data.map(item => item.category),
                        datasets: [{
                            data: data.map(item => item.total),
                            backgroundColor: [
                                '#FF6384', '#36A2EB', '#FFCE56',
                                '#4BC0C0', '#9966FF', '#FF9F40'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            })
            .catch(err => {
                console.error('Error loading expenses chart:', err);
            });

        fetch('/api/income_vs_expenses')
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById('incomeVsExpensesChart').getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Income', 'Expenses'],
                        datasets: [{
                            data: [data.income, data.expenses],
                            backgroundColor: ['#4CAF50', '#F44336']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });
            })
        .catch(err => console.error('Error loading income vs expenses chart:', err));


        // === Donations vs Income (Total) ===
        fetch('/api/donations_vs_income')
            .then(res => res.json())
            .then(data => {
                const ctx = document.getElementById('donationsVsIncomeChart').getContext('2d');
                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: ['Income', 'Donations & Giving'],
                        datasets: [{
                            data: [data.income, data.donations],
                            backgroundColor: ['#2196F3', '#FF9800']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'bottom'
                            }
                        }
                    }
                });
            })
            .catch(err => {
                console.error('Error loading donations chart:', err);
            });

        // === Monthly Cash Flow: Income, Expenses, Net (Line Overlay) ===
        fetch('/api/monthly_cash_flow')
            .then(res => res.json())
            .then(data => {
                const months = data.map(item => item.month);
                const income = data.map(item => item.income);
                const expenses = data.map(item => item.expenses);
                const net = data.map((item) => item.income - item.expenses);

                const ctx = document.getElementById('monthlyCashFlowChart').getContext('2d');
                new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: months,
                        datasets: [
                            {
                                label: 'Income',
                                data: income,
                                backgroundColor: '#4CAF50'
                            },
                            {
                                label: 'Expenses',
                                data: expenses,
                                backgroundColor: '#F44336'
                            },
                            {
                                label: 'Net Cash Flow',
                                data: net,
                                type: 'line',
                                borderColor: '#000000',
                                backgroundColor: 'transparent',
                                borderWidth: 2,
                                tension: 0.3,
                                fill: false,
                                pointRadius: 3,
                                pointHoverRadius: 5
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        interaction: {
                            mode: 'index',
                            intersect: false
                        },
                        plugins: {
                            legend: {
                                position: 'bottom'
                            },
                            tooltip: {
                                mode: 'index',
                                intersect: false
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            })
            .catch(err => {
                console.error('Error loading monthly cash flow chart:', err);
            });

    });
})();

