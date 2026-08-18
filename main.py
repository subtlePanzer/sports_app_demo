from flask import Flask, render_template, send_file

app = Flask(__name__)

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

if __name__ == '__main__':
        launch()
