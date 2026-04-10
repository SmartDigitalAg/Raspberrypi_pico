from flask import Flask, jsonify, render_template
import requests
import threading
import time

app = Flask(__name__)

PICO_IP = "192.168.0.153"  # ← 피코 IP로 변경

latest = {"temp": None, "humi": None, "time": ""}

def fetch_loop():
    while True:
        try:
            res = requests.get(f"http://{PICO_IP}/data", timeout=5)
            data = res.json()
            latest.update(data)
            print(f"온도: {data['temp']}°C  습도: {data['humi']}%")
        except Exception as e:
            print("수집 오류:", e)
        time.sleep(5)

@app.route("/data")
def get_data():
    return jsonify(latest)

@app.route("/")
def dashboard():
    temp = latest["temp"] if latest["temp"] is not None else "--"
    humi = latest["humi"] if latest["humi"] is not None else "--"
    time = latest["time"] if latest["time"] else "대기 중..."
    return render_template("index.html", temp=temp, humi=humi, time=time)

if __name__ == "__main__":
    t = threading.Thread(target=fetch_loop, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)