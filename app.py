from flask import Flask, render_template_string, request, jsonify
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

# INLINE STUDENT PAGE (no templates needed)
STUDENT_HTML = """
<!DOCTYPE html>
<html><head><title>Smart Attendance</title>
<style>body{background:#000;color:#0ff;font-family:Arial;text-align:center;padding:50px}
video{border:10px solid #0ff;border-radius:30px} h1{font-size:50px}</style></head>
<body><h1>SMART ATTENDANCE</h1>
<input id="roll" placeholder="Enter Roll Number" style="padding:15px;font-size:25px;width:300px"><br><br>
<button onclick="go()" style="padding:15px 30px;font-size:25px;border:2px solid #0ff;background:#000;color:#0ff">START CAMERA</button>
<video id="v" width="640" height="480" autoplay muted></video>
<div id="msg" style="font-size:40px;margin:20px">Click START and look at camera</div>

<script>
let marked=false;
function go(){
    const roll = document.getElementById("roll").value.trim();
    if(!roll){alert("Enter roll number first!");return;}
    navigator.mediaDevices.getUserMedia({video:true}).then(s=>{
        document.getElementById("v").srcObject=s;
        document.getElementById("msg").innerText="Looking for your face...";
        setInterval(()=>scan(roll),1500);
    }).catch(e=>alert("Camera error: "+e));
}
async function scan(roll){
    if(marked)return;
    const c=document.createElement("canvas"); c.width=640; c.height=480;
    c.getContext("2d").drawImage(document.getElementById("v"),0,0);
    try{
        const r=await fetch("/mark",{method:"POST",headers:{"Content-Type":"application/json"},
            body:JSON.stringify({name:"Student",roll:roll})});
        const d=await r.json();
        if(d.status==="success"){
            document.getElementById("msg").innerHTML="<span style='color:lime'>✓ ATTENDANCE MARKED!</span>";
            marked=true;
        } else if(d.status==="closed"){
            document.getElementById("msg").innerHTML="<span style='color:red'>Time closed!</span>";
        }
    }catch(e){
        document.getElementById("msg").innerHTML="<span style='color:red'>Server error</span>";
    }
}
</script></body></html>
"""

@app.route("/")
def home():
    global start_time, end_time, running
    if not running:
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=DURATION)
        running = True
        threading.Thread(target=close_attendance, daemon=True).start()
    return render_template_string(STUDENT_HTML)

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
    
    table_rows = "".join([f"<tr><td>{i+1}</td><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>" for i, row in enumerate(rows)])
    
    DASHBOARD_HTML = f"""
    <!DOCTYPE html>
    <html><head><meta http-equiv="refresh" content="3"><title>Dashboard</title>
    <style>body{{background:#000033;color:#0ff;font-family:Arial;text-align:center;padding:20px}}
    h1{{font-size:60px;margin:20px}} table{{margin:auto;width:90%;border-collapse:collapse}} th,td{{border:2px solid #0ff;padding:15px;font-size:20px}} th{{background:#000}}</style></head>
    <body><h1>SMART ATTENDANCE SYSTEM</h1>
    <h1 style="font-size:100px">{timer}</h1>
    <h2 style="color:{'lime' if running else 'red'}">{'OPEN' if running else 'CLOSED'}</h2>
    <table><tr><th>No.</th><th>Name</th><th>Roll No</th><th>IP</th><th>Time</th></tr>
    {table_rows}
    </table>
    <p style="margin-top:50px;font-size:25px">Computer Networks Project – Live on Internet</p>
    </body></html>
    """
    return render_template_string(DASHBOARD_HTML)

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
    print(f"PRESENT → {data['name']} ({data['roll']}) from {ip}")
    return jsonify({"status":"success"})

def close_attendance():
    global running
    time.sleep(DURATION * 60)
    running = False
    print("ATTENDANCE CLOSED")

if __name__ == "__main__":
    app.run()
