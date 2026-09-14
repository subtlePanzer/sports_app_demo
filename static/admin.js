async function fetchStudents() {
    const res = await fetch('/api/admin/students');
    const data = await res.json();
    const container = document.getElementById('students-list');
    if (!data.students || !data.students.length) {
        container.innerText = 'No students';
        return;
    }
    const table = document.createElement('table');
    table.border = 1;
    const head = document.createElement('tr');
    ['ID','First','Last','House','Year','Sex'].forEach(h => {
        const th = document.createElement('th'); th.innerText = h; head.appendChild(th);
    });
    table.appendChild(head);
    data.students.forEach(s => {
        const tr = document.createElement('tr');
        [s.student_id, s.first_name, s.last_name, s.house, s.year_level, s.sex].forEach(val => {
            const td = document.createElement('td'); td.innerText = val; tr.appendChild(td);
        });
        table.appendChild(tr);
    });
    container.innerHTML = ''; container.appendChild(table);
}

document.getElementById('add-student-form').addEventListener('submit', async function(e){
    e.preventDefault();
    const payload = {
        first_name: document.getElementById('first_name').value,
        last_name: document.getElementById('last_name').value,
        house: parseInt(document.getElementById('house').value) || 0,
        year_level: parseInt(document.getElementById('year_level').value) || 0,
        sex: document.getElementById('sex').value || ''
    };
    const res = await fetch('/api/admin/add_student', {
        method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload)
    });
    const data = await res.json();
    const out = document.getElementById('add-result');
    if (data.status === 'ok') {
        out.innerText = 'Added';
        document.getElementById('add-student-form').reset();
        await fetchStudents();
    } else if (data.status === 'exists') {
        out.innerText = 'Student already exists';
    } else {
        out.innerText = 'Error: ' + (data.message || JSON.stringify(data));
    }
});

document.getElementById('upload-csv').addEventListener('click', async function(){
    const f = document.getElementById('csv-file').files[0];
    const out = document.getElementById('upload-result');
    if (!f) { out.innerText = 'Please select a CSV file'; return; }
    const fd = new FormData(); fd.append('file', f);
    const res = await fetch('/api/admin/upload_students', { method: 'POST', body: fd });
    const data = await res.json();
    if (data.status === 'ok') {
        out.innerText = `Added ${data.added} skipped ${data.skipped}`;
        await fetchStudents();
    } else {
        out.innerText = 'Error: ' + (data.message || JSON.stringify(data));
    }
});

// Initial
fetchStudents();
