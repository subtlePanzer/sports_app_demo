from flask import Flask, render_template, send_file, jsonify, request
import sqlite3

app = Flask(__name__)

def make_sql_query(cmd: str, params: tuple=()):
    with sqlite3.connect("database.DB") as conn:
        cursor = conn.cursor()
        cursor.execute(cmd, params)
        out = cursor.fetchall()
        conn.commit()
    return out

def launch():
    app.run(debug=True)

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/manifest.json')
def serve_manifest():
    return send_file('manifest.json', mimetype='application/manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_file('sw.js', mimetype='application/javascript')

HOUSE_META = {
    1: {"name": "Brooklyn", "color": "#FFDD00"},
    2: {"name": "Eldergreen", "color": "#008F4F"},
    3: {"name": "Greenwith", "color": "#7B1272"},
    4: {"name": "Hillcott", "color": "#E42618"},
    5: {"name": "Petworth", "color": "#FF7900"},
    6: {"name": "Surrey", "color": "#00B5DD"}
}


class event_data:
    def __init__(self, event_id, event_name, year_level, sex, is_complete, scheduled_time, station):
        self.event_id = event_id
        self.event_name = event_name
        self.year_level = year_level
        self.sex = sex
        self.is_complete = is_complete
        self.scheduled_time = scheduled_time
        self.station = station


def get_next_student(event_id):    
    event_info = make_sql_query("""
    SELECT year_level, sex FROM events WHERE event_id = ?
    """, (event_id,))

    if not event_info:
        return None

    year_level, sex = event_info[0]

    student = make_sql_query("""
    SELECT first_name, last_name
    FROM students
    WHERE year_level = ? 
      AND sex = ?
      AND (first_name || ' ' || last_name) NOT IN (
          SELECT student_name FROM results WHERE event_id = ?
      )
    ORDER BY house ASC, last_name ASC, first_name ASC
    LIMIT 1
    """, (year_level, sex, event_id))

    if student:
        return f"{student[0][0]} {student[0][1]}"
    return None

@app.route('/field')
def field_event():
    return render_template("field.html")

@app.route('/api/get_event/<int:station_id>/next')
def api_get_next_event_info(station_id):
    data = make_sql_query("""
    SELECT event_id, event_name, year_level, sex, is_complete, scheduled_time, station
    FROM events
    WHERE (is_complete = 0 AND station = ?)
    ORDER BY scheduled_time ASC
    LIMIT 1
    """, (station_id,))

    if not data:
        return jsonify({})

    row = data[0]
    event_info = event_data(
        event_id=row[0],
        event_name=row[1],
        year_level=int(row[2]),
        sex=chr(row[3]),
        is_complete=bool(row[4]),
        scheduled_time=int(row[5]),
        station=int(row[6])
    )
    return jsonify(event_info.__dict__)

@app.route('/api/get_next_student/<int:event_id>')
def api_get_next_student(event_id):
    student_name = get_next_student(event_id)
    return jsonify({"student_name": student_name})

@app.route('/api/submit_result', methods=['POST'])
def api_submit_result():
    # Backwards-compatible endpoint: accepts event_id, student_name, result
    data = request.get_json()
    event_id = data.get('event_id')
    student_name = data.get('student_name')
    result = data.get('result')

    # Treat missing result as absent
    absent = 1 if result is None else 0

    # Upsert: update if a row exists otherwise insert
    existing = make_sql_query("""
    SELECT result_id FROM results WHERE event_id = ? AND student_name = ?
    """, (event_id, student_name))

    if existing:
        make_sql_query("""
        UPDATE results SET result = ?, absent = ? WHERE result_id = ?
        """, (result, absent, existing[0][0]))
    else:
        make_sql_query("""
        INSERT INTO results (event_id, student_name, result, absent)
        VALUES (?, ?, ?, ?)
        """, (event_id, student_name, result, absent))

    return jsonify({"status": "success"})


@app.route('/api/get_event_students/<int:event_id>')
def api_get_event_students(event_id):
    # Return the full ordered student list for the event and any existing results
    event_info = make_sql_query("""
    SELECT year_level, sex FROM events WHERE event_id = ?
    """, (event_id,))

    if not event_info:
        return jsonify({"students": []})

    year_level, sex = event_info[0]

    students = make_sql_query("""
    SELECT s.first_name || ' ' || s.last_name AS student_name,
           r.result, COALESCE(r.absent, 0) as absent
    FROM students s
    LEFT JOIN results r ON r.event_id = ? AND r.student_name = (s.first_name || ' ' || s.last_name)
    WHERE s.year_level = ? AND s.sex = ?
    ORDER BY s.house ASC, s.last_name ASC, s.first_name ASC
    """, (event_id, year_level, sex))

    student_list = []
    for row in students:
        student_list.append({
            "student_name": row[0],
            "result": row[1],
            "absent": bool(row[2])
        })

    return jsonify({"students": student_list})


@app.route('/api/update_result', methods=['POST'])
def api_update_result():
    # New endpoint to set/clear a result or mark absent for a specific student index
    data = request.get_json()
    event_id = data.get('event_id')
    student_name = data.get('student_name')
    result = data.get('result')
    absent = 1 if data.get('absent') else 0

    existing = make_sql_query("""
    SELECT result_id FROM results WHERE event_id = ? AND student_name = ?
    """, (event_id, student_name))

    if existing:
        make_sql_query("""
        UPDATE results SET result = ?, absent = ? WHERE result_id = ?
        """, (result, absent, existing[0][0]))
    else:
        make_sql_query("""
        INSERT INTO results (event_id, student_name, result, absent)
        VALUES (?, ?, ?, ?)
        """, (event_id, student_name, result, absent))

    return jsonify({"status": "ok"})


@app.route('/api/stations')
def api_get_stations():
    # Return distinct station ids from events to populate dropdown
    rows = make_sql_query("""
    SELECT DISTINCT station FROM events ORDER BY station ASC
    """)
    stations = [r[0] for r in rows]
    return jsonify({"stations": stations})

def setup():
    make_sql_query("""
    CREATE TABLE IF NOT EXISTS events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT,
    year_level INTEGER,
    sex INTEGER,
    is_complete INTEGER,
    scheduled_time INTEGER,
    station INTEGER
    )""")

    # Create results table with an 'absent' flag. If the table already exists without the column,
    # try to add the column safely.
    make_sql_query("""
    CREATE TABLE IF NOT EXISTS results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    student_name TEXT,
    result REAL,
    absent INTEGER DEFAULT 0
    )""")

    # If running against an older DB that has results but no 'absent' column, attempt to add it.
    try:
        cols = make_sql_query("PRAGMA table_info(results)")
        col_names = [c[1] for c in cols]
        if 'absent' not in col_names:
            make_sql_query("ALTER TABLE results ADD COLUMN absent INTEGER DEFAULT 0")
    except Exception:
        # Ignore if we cannot alter (e.g., permission issues) — the application can still function.
        pass

    make_sql_query("""
    CREATE TABLE IF NOT EXISTS students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    house INTEGER,
    year_level INTEGER,
    sex INTEGER
    )""")

    # Leave existing data untouched. Startup only ensures tables exist.


if __name__ == '__main__':
    setup()
    launch()
# 
