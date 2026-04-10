import network
import socket
import time
import sys
import os
from machine import Pin, I2C
from lcd_project.lcd_api import LcdApi
from lcd_project.i2c_lcd import I2cLcd
from dht import DHT11

# ── 설정 ──────────────────────────────────────────
SSID     = 'SmartDigitalAgLab'
PASSWORD = 'Smartfarm208!'

# I2C LCD (SDA=GPIO6, SCL=GPIO3)
i2c = I2C(1, sda=Pin(6), scl=Pin(3), freq=100000)
lcd = I2cLcd(i2c, 0x27, 2, 16)

# DHT11 (GPIO28)
dht_sensor = DHT11(Pin(28))

# LED
led = Pin("LED", Pin.OUT)

# 전역 센서값
latest = {"temp": None, "humi": None, "time": ""}
# ──────────────────────────────────────────────────


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    lcd.clear()
    lcd.putstr("WiFi Connecting.")

    for _ in range(10):
        if wlan.status() >= 3:
            break
        time.sleep(1)

    if wlan.status() != 3:
        lcd.clear()
        lcd.putstr("WiFi Failed!")
        return None

    ip = wlan.ifconfig()[0]
    lcd.clear()
    lcd.putstr("WiFi Connected!")
    lcd.move_to(0, 1)
    lcd.putstr(ip)
    print(f"IP: {ip}")
    return ip


def display_lcd(temp, humi):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(f"Temp: {temp:.1f}C" if temp is not None else "Temp: --")
    lcd.move_to(0, 1)
    lcd.putstr(f"Humi: {humi:.1f}%" if humi is not None else "Humi: --")


def read_sensor():
    try:
        dht_sensor.measure()
        t = dht_sensor.temperature()
        h = dht_sensor.humidity()
        led.value(1); time.sleep(0.1); led.value(0)
        return t, h
    except Exception as e:
        print("센서 오류:", e)
        return None, None


def get_html():
    t = latest["temp"]
    h = latest["humi"]
    ts = latest["time"]
    temp_str = f"{t:.1f}" if t is not None else "--"
    humi_str = f"{h:.1f}" if h is not None else "--"

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Pico DHT11 Monitor</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: Arial, sans-serif;
      background: #1a1a2e;
      color: #eee;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 20px;
    }}
    h1 {{ font-size: 1.4rem; margin-bottom: 24px; color: #0ff; letter-spacing: 2px; }}
    .cards {{
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
      justify-content: center;
    }}
    .card {{
      background: #16213e;
      border: 2px solid #0f3460;
      border-radius: 16px;
      padding: 30px 40px;
      text-align: center;
      min-width: 160px;
    }}
    .card .label {{
      font-size: 0.85rem;
      color: #888;
      margin-bottom: 8px;
      letter-spacing: 1px;
    }}
    .card .value {{
      font-size: 3rem;
      font-weight: bold;
    }}
    .card .unit {{ font-size: 1.2rem; color: #aaa; }}
    .temp .value {{ color: #ff6b6b; }}
    .humi .value {{ color: #4ecdc4; }}
    .updated {{
      margin-top: 24px;
      font-size: 0.8rem;
      color: #555;
    }}
    .btn {{
      margin-top: 20px;
      padding: 10px 28px;
      background: #0f3460;
      color: #0ff;
      border: 1px solid #0ff;
      border-radius: 8px;
      font-size: 0.9rem;
      cursor: pointer;
    }}
  </style>
</head>
<body>
  <h1>🌡 DHT11 Monitor</h1>
  <div class="cards">
    <div class="card temp">
      <div class="label">TEMPERATURE</div>
      <div class="value" id="temp">{temp_str}<span class="unit">°C</span></div>
    </div>
    <div class="card humi">
      <div class="label">HUMIDITY</div>
      <div class="value" id="humi">{humi_str}<span class="unit">%</span></div>
    </div>
  </div>
  <div class="updated" id="ts">마지막 측정: {ts}</div>
  <button class="btn" onclick="refresh()">새로고침</button>

  <script>
    // 5초마다 자동 갱신
    setInterval(refresh, 5000);

    function refresh() {{
      fetch('/data')
        .then(r => r.json())
        .then(d => {{
          document.getElementById('temp').innerHTML =
            (d.temp !== null ? d.temp.toFixed(1) : '--') + '<span class="unit">°C</span>';
          document.getElementById('humi').innerHTML =
            (d.humi !== null ? d.humi.toFixed(1) : '--') + '<span class="unit">%</span>';
          document.getElementById('ts').textContent = '마지막 측정: ' + d.time;
        }});
    }}
  </script>
</body>
</html>"""


def start_server(ip):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, 80))
    s.listen(5)
    s.settimeout(0.5)          # non-blocking 처리용 타임아웃
    print(f"웹 서버: http://{ip}")

    last_read = 0

    while True:
        # ── 5초마다 센서 읽기 ──
        now = time.ticks_ms()
        if time.ticks_diff(now, last_read) >= 5000:
            t, h = read_sensor()
            if t is not None:
                latest["temp"] = t
                latest["humi"] = h
                latest["time"] = f"{time.ticks_ms() // 1000}s"
                display_lcd(t, h)
                print(f"Temp={t}°C  Humi={h}%")
            last_read = now

        # ── 클라이언트 요청 처리 ──
        try:
            client, addr = s.accept()
            request = client.recv(1024).decode()

            if '/data' in request:
                # JSON API
                t = latest["temp"]
                h = latest["humi"]
                t_str = f"{t:.1f}" if t is not None else "null"
                h_str = f"{h:.1f}" if h is not None else "null"
                body = f'{{"temp":{t_str},"humi":{h_str},"time":"{latest["time"]}"}}'
                client.send('HTTP/1.0 200 OK\r\nContent-Type: application/json\r\n\r\n')
                client.send(body)
            else:
                # HTML 페이지
                html = get_html()
                client.send('HTTP/1.0 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n')
                client.send(html)

            client.close()

        except OSError:
            pass  # 타임아웃 → 루프 계속
        except Exception as e:
            print("서버 오류:", e)
            try: client.close()
            except: pass


def main():
    ip = connect_wifi()
    if not ip:
        return
    time.sleep(1)

    # 첫 측정
    t, h = read_sensor()
    if t is not None:
        latest["temp"] = t
        latest["humi"] = h
        latest["time"] = "0s"
        display_lcd(t, h)

    start_server(ip)


if __name__ == "__main__":
    main()
