let currentEventId = null;
let students = []; // {student_name, result, absent}
let currentIndex = 0;
let currentStation = null;

async function fetchStations() {
    const res = await fetch('/api/stations');
    const data = await res.json();
    const select = document.getElementById('station-select');
    select.innerHTML = '';
    (data.stations || []).forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = `Station ${s}`;
        select.appendChild(opt);
    });
    if ((data.stations || []).length > 0) {
        currentStation = data.stations[0];
        select.value = currentStation;
    }
}

async function loadNextScheduledForStation(stationId) {
    const eventResponse = await fetch(`/api/get_event/${stationId}/next`);
    const eventData = await eventResponse.json();
    if (!eventData.event_id) {
        document.getElementById('event-title').innerText = "No upcoming events";
        document.getElementById('student-name').innerText = "";
        students = [];
        currentEventId = null;
        renderProgress();
        return;
    }
    await loadEvent(eventData.event_id, eventData);
}

async function loadEvent(eventId, eventData=null) {
    currentEventId = eventId;
    const info = eventData || (await (await fetch(`/api/get_event/${eventId}/next`)).json());
    document.getElementById('event-title').innerText = `${info.event_name} (Year ${info.year_level})`;

    const res = await fetch(`/api/get_event_students/${eventId}`);
    const data = await res.json();
    students = data.students || [];
    currentIndex = 0;
    renderCurrentStudent();
    renderProgress();
}

function renderCurrentStudent() {
    if (!students.length) {
        document.getElementById('student-name').innerText = "No students for this event";
        document.getElementById('student-house').textContent = 'House';
        document.getElementById('student-house').style.background = '#6b7280';
        document.getElementById('result').value = '';
        return;
    }
    const s = students[currentIndex];
    const houseName = s.house_name || 'Unknown';
    const houseColor = s.house_color || '#6b7280';

    document.getElementById('student-name').innerText = `Student: ${s.student_name}`;
    const houseEl = document.getElementById('student-house');
    houseEl.textContent = houseName;
    houseEl.style.background = houseColor;
    houseEl.style.border = '1px solid rgba(0,0,0,0.1)';

    document.getElementById('result').value = s.result == null ? '' : s.result;
    document.getElementById('mark-absent').textContent = s.absent ? 'Marked Not in Attendance' : 'Mark Not in Attendance';
}

function renderProgress() {
    const el = document.getElementById('progress');
    if (!students.length) {
        el.textContent = '';
        return;
    }
    el.textContent = `Student ${currentIndex + 1} of ${students.length}`;
}

async function saveCurrent(allowEmpty=false) {
    if (currentEventId == null) return {ok:false, msg:'No event loaded'};
    const s = students[currentIndex];
    const raw = document.getElementById('result').value;
    let result = raw === '' ? null : parseFloat(raw);
    if (!allowEmpty && result == null && !s.absent) {
        return {ok:false, msg:'Please enter a result or mark not in attendance.'};
    }

    const payload = {
        event_id: currentEventId,
        student_name: s.student_name,
        result: result,
        absent: s.absent ? 1 : 0
    };

    await fetch('/api/update_result', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify(payload)
    });

    // Update local copy
    s.result = result;
    s.absent = !!payload.absent;
    renderCurrentStudent();
    renderProgress();
    return {ok:true};
}

// Controls
document.getElementById('station-select').addEventListener('change', function(e){
    currentStation = parseInt(e.target.value);
});

document.getElementById('load-next-scheduled').addEventListener('click', async function(){
    if (currentStation == null) {
        alert('Please select a station');
        return;
    }
    await loadNextScheduledForStation(currentStation);
});

document.getElementById('prev-student').addEventListener('click', function(){
    if (currentIndex > 0) {
        currentIndex -= 1;
        renderCurrentStudent();
        renderProgress();
    }
});

document.getElementById('next-student').addEventListener('click', async function(){
    if (!students.length) return;
    const s = students[currentIndex];
    // if already saved or marked absent, allow move
    if ((s.result != null) || s.absent) {
        if (currentIndex < students.length - 1) {
            currentIndex += 1;
            renderCurrentStudent();
            renderProgress();
        } else {
            alert('Reached end of student list for this event');
        }
        return;
    }
    // if input has a value, auto-save then move
    const raw = document.getElementById('result').value;
    if (raw !== '') {
        const saved = await saveCurrent(true);
        if (saved.ok) {
            if (currentIndex < students.length - 1) {
                currentIndex += 1;
                renderCurrentStudent();
                renderProgress();
            } else {
                alert('Reached end of student list for this event');
            }
        }
        return;
    }
    alert('Please enter a result or mark Not in Attendance before moving to the next student.');
});

// Mark absent button
document.getElementById('mark-absent').addEventListener('click', async function(){
    if (!students.length) return;
    const s = students[currentIndex];
    // toggle
    s.absent = !s.absent;
    if (s.absent) {
        s.result = null;
    }
    // Save immediately
    await saveCurrent(true);
});

// Save form
document.getElementById('result-form').addEventListener('submit', async function(e){
    e.preventDefault();
    if (!students.length) return;
    const raw = document.getElementById('result').value;
    if (raw === '' && !students[currentIndex].absent) {
        alert('Please enter a result or mark Not in Attendance.');
        return;
    }
    await saveCurrent(true);
    alert('Saved');
});

// Initial load
(async function(){
    await fetchStations();
    const sel = document.getElementById('station-select');
    if (sel.options.length > 0) {
        currentStation = parseInt(sel.value);
        await loadNextScheduledForStation(currentStation);
    }
})();
