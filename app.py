from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
import threading, time

app = Flask(__name__)
DB = "att.db"
DURATION = 10
start_time = None
end_time = None
running = False

def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS att 
                 (date TEXT, name TEXT, roll TEXT, ip TEXT, time TEXT)''')
    conn.commit()
    conn.close()
init_db()

@app.route("/")
def home():
    global start_time, end_time, running
    if not running:
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=DURATION)
        running = True
        threading.Thread(target=close_attendance, daemon=True).start()
    return render_template("index.html")

@app.route("/dashboard")
def dash():
    timer = "CLOSED"
    if running:
        left = max(0, int((end_time - datetime.now()).total_seconds()))
        m, s = divmod(left, 60)
        timer = f"{m:02d}:{s:02d}"
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("SELECT name, roll, ip, time FROM att ORDER BY time DESC")
    rows = c.fetchall()
    conn.close()
    return render_template("dashboard.html", timer=timer, rows=rows, open=running)

@app.route("/mark", methods=["POST"])
def mark():
    if not running: return jsonify({"status":"closed"})
    data = request.json
    ip = request.remote_addr
    t = datetime.now().strftime("%H:%M:%S")
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("INSERT INTO att VALUES (?,?,?,?,?)",
              (datetime.now().strftime("%Y-%m-%d"), data["name"], data["roll"], ip, t))
    conn.commit()
    conn.close()
    return jsonify({"status":"success"})

def close_attendance():
    global running
    time.sleep(DURATION * 60)
    running = False

if __name__ == "__main__":
    app.run()
