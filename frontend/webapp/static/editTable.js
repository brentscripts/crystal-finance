(function() {
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.edit-btn').forEach(function(editBtn) {
            editBtn.addEventListener('click', function() {
                var row = editBtn.closest('tr');
                ['date','description','category','amount','source'].forEach(function(field) {
                    var td = row.querySelector('.td-' + field);
                    var value = td.textContent;
                    td.innerHTML = '<input type="text" class="edit-input" name="' + field + '" value="' + value + '">';
                });
                row.querySelector('.save-btn').style.display = '';
                editBtn.style.display = 'none';
            });
        });
        document.querySelectorAll('.save-btn').forEach(function(saveBtn) {
            saveBtn.addEventListener('click', function() {
                var row = saveBtn.closest('tr');
                var id = row.getAttribute('data-id');
                var data = {};
                ['date','description','category','amount','source'].forEach(function(field) {
                    data[field] = row.querySelector('input[name="' + field + '"]').value;
                });
                const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
                fetch('/update/' + id, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify(data)
                }).then(resp => resp.json()).then(resp => {
                    if (resp.success) {
                        ['date','description','category','amount','source'].forEach(function(field) {
                            var td = row.querySelector('.td-' + field);
                            td.textContent = data[field];
                        });
                        saveBtn.style.display = 'none';
                        row.querySelector('.edit-btn').style.display = '';
                    } else {
                        alert('Update failed');
                    }
                });
            });
        });
    });
})();
