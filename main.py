from flask import Flask, render_template, send_file
import sqlite3
app = Flask(__name__)

def make_sql_query(cmd: str, params: tuple=()):
        with sqlite3.connect("database.DB") as conn:
                cursor = conn.cursor()

                cursor.execute(cmd, params) # prevents SQL injection

                out = cursor.fetchall()
                conn.commit()

        return out

def launch():
        # launch the website
        app.run(debug=True)

@app.route('/')
def index_page():
        # homepage
        return render_template('index.html')

@app.route('/manifest.json')
def serve_manifest():
        return send_file('manifest.json', mimetype='application/manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_file('sw.js', mimetype='application/javascript')

class event_data:
        event_name: str
        year_level: int
        sex: str
        is_complete: bool
        scheduled_time: int
        station: int

        def __init__(self, event_name, year_level, sex, is_complete, scheduled_time, station):
                self.event_name = event_name
                self.year_level = year_level
                self.year_level = year_level
                self.sex = sex
                self.is_complete = is_complete
                self.scheduled_time = scheduled_time
                self.station = station

@app.route('/field')
def field_event():
        return render_template("field.html")

@app.route('/api/get_event/<int:station_id>/next')
def api_get_next_event_info(station_id):
        data = make_sql_query("""
        SELECT event_name, year_level, sex, is_complete, scheduled_time, station
        FROM events
        WHERE (is_complete = 0 AND station = ?)
        ORDER_BY scheduled_time ASC
        LIMIT 1
        """, (station_id))[0]

        event_info = event_data(event_name=data[0], year_level=int(data[1]), sex=chr(data[2]), is_complete=bool(data[3]), scheduled_time=int(data[4]), station=int(data[5]))
        return event_info

@app.route('/api/get_event/all/<int:event_id>')
def api_get_next_event_info_anywhere(event_id):
        ...

@app.route('/api/get_event/<int:station_id>/<int:event_id>')
def api_get_nth_event_info_station(station_id, event_id):
        ...

def setup():
        make_sql_query("""
        CREATE TABLE IF NOT EXISTS events (
        event_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_name STRING,
        year_level INTEGER,
        sex INTEGER,
        is_complete INTEGER,
        scheduled_time INTEGER,
        station INTEGER
        )"""
#        excepted_students STRING,
        )

        make_sql_query("""
        INSERT INTO events (event_name, year_level, sex, is_complete, scheduled_time, station)
        VALUES (?, ?, ?, ?, ?, ?)
        """, ("High Jump", 7, ord('M'), 0, 1100, 1))

if __name__ == '__main__':
        setup()
        launch()
