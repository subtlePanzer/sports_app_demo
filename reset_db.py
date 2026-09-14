import sqlite3

conn = sqlite3.connect('database.DB')
cur = conn.cursor()
cur.executescript('''
DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS events;
''')
conn.commit()

# Recreate tables
cur.executescript('''
CREATE TABLE events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_name TEXT,
    year_level INTEGER,
    sex INTEGER,
    is_complete INTEGER,
    scheduled_time INTEGER,
    station INTEGER
);
CREATE TABLE results (
    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER,
    student_name TEXT,
    result REAL,
    absent INTEGER DEFAULT 0
);
CREATE TABLE students (
    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    house INTEGER,
    year_level INTEGER,
    sex INTEGER
);
''')
conn.commit()

# Seed data
cur.execute("INSERT INTO events (event_name, year_level, sex, is_complete, scheduled_time, station) VALUES (?,?,?,?,?,?)", ("High Jump", 7, ord('M'), 0, 1100, 1))
cur.executemany("INSERT INTO students (first_name, last_name, house, year_level, sex) VALUES (?,?,?,?,?)", [
    ("Charlie", "Brown", 2, 7, ord('M')),
    ("Alice", "Smith", 1, 7, ord('M')),
    ("Bob", "Adams", 1, 7, ord('M')),
])
conn.commit()

# Report counts
students_count = cur.execute('select count(*) from students').fetchone()[0]
events_count = cur.execute('select count(*) from events').fetchone()[0]
results_count = cur.execute('select count(*) from results').fetchone()[0]
print('students', students_count)
print('events', events_count)
print('results_rows', results_count)

conn.close()
