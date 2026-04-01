import network
import socket
import time
from machine import Pin, I2C
from lcd_project.lcd_api import LcdApi
from lcd_project.i2c_lcd import I2cLcd

# WiFi 설정 (본인 WiFi로 변경)
SSID = 'SmartDigitalAgLab'
PASSWORD = 'Smartfarm208!'

# I2C LCD 설정
i2c = I2C(1, sda=Pin(6), scl=Pin(3), freq=100000)
lcd = I2cLcd(i2c, 0x27, 2, 16)

# 현재 LCD에 표시된 텍스트
current_line1 = ""
current_line2 = ""


# WiFi 연결 함수
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    lcd.clear()
    lcd.putstr("WiFi 연결중...")

    max_wait = 10
    while max_wait > 0:
        if wlan.status() >= 3:
            break
        max_wait -= 1
        print("연결 대기중...")
        time.sleep(1)

    if wlan.status() != 3:
        lcd.clear()
        lcd.putstr("WiFi 연결 실패")
        return None

    ip = wlan.ifconfig()[0]
    print(f"연결됨! IP: {ip}")

    lcd.clear()
    lcd.putstr("WiFi Connected!")
    lcd.move_to(0, 1)
    lcd.putstr(ip)

    return ip


# LCD에 텍스트 표시
def display_lcd(line1, line2=""):
    global current_line1, current_line2
    current_line1 = line1[:16]  # 최대 16자
    current_line2 = line2[:16]

    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(current_line1)
    lcd.move_to(0, 1)
    lcd.putstr(current_line2)


# URL 디코딩 함수 (UTF-8 지원)
def url_decode(s):
    result = bytearray()
    i = 0
    while i < len(s):
        if s[i] == '%' and i + 2 < len(s):
            hex_val = s[i+1:i+3]
            try:
                result.append(int(hex_val, 16))
                i += 3
            except:
                result.append(ord(s[i]))
                i += 1
        elif s[i] == '+':
            result.append(32)  # space
            i += 1
        else:
            result.append(ord(s[i]))
            i += 1
    try:
        return result.decode('utf-8')
    except:
        return result.decode('latin-1')


# HTML 페이지
def get_html():
    return """<!DOCTYPE html>
<html>
<head>
    <title>Pico LCD Control</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta charset="UTF-8">
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            margin: 20px;
            background-color: #f0f0f0;
        }
        .container {
            max-width: 400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; }
        input[type="text"] {
            width: 90%;
            padding: 10px;
            margin: 10px 0;
            font-size: 16px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        .button {
            padding: 12px 30px;
            font-size: 16px;
            cursor: pointer;
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            margin: 5px;
        }
        .button:hover { background-color: #45a049; }
        .button-clear {
            background-color: #f44336;
        }
        .button-clear:hover { background-color: #d32f2f; }
        .lcd-preview {
            background: #1a1a2e;
            color: #0f0;
            font-family: monospace;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
            font-size: 18px;
            letter-spacing: 2px;
        }
        .lcd-line {
            height: 24px;
            overflow: hidden;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>LCD Control</h1>

        <div class="lcd-preview">
            <div class="lcd-line" id="line1">----------------</div>
            <div class="lcd-line" id="line2">----------------</div>
        </div>

        <div>
            <input type="text" id="text1" placeholder="Line 1 (max 16)" maxlength="16">
            <input type="text" id="text2" placeholder="Line 2 (max 16)" maxlength="16">
        </div>

        <div>
            <button class="button" onclick="sendText()">Send to LCD</button>
            <button class="button button-clear" onclick="clearLcd()">Clear</button>
        </div>
    </div>

    <script>
        function updatePreview() {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('line1').textContent = data.line1.padEnd(16, ' ') || '                ';
                    document.getElementById('line2').textContent = data.line2.padEnd(16, ' ') || '                ';
                });
        }

        function sendText() {
            const t1 = document.getElementById('text1').value;
            const t2 = document.getElementById('text2').value;
            fetch('/send?line1=' + encodeURIComponent(t1) + '&line2=' + encodeURIComponent(t2))
                .then(() => updatePreview());
        }

        function clearLcd() {
            fetch('/clear').then(() => {
                document.getElementById('text1').value = '';
                document.getElementById('text2').value = '';
                updatePreview();
            });
        }

        updatePreview();
    </script>
</body>
</html>"""


# 웹 서버 시작
def start_server(ip):
    PORT = 80
    addr = (ip, PORT)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(addr)
    s.listen(1)

    print(f"웹 서버 시작: http://{ip}")

    while True:
        try:
            client, addr = s.accept()
            request = client.recv(1024).decode()

            # 요청 파싱
            if '/send?' in request:
                # 텍스트 추출
                params = request.split('/send?')[1].split(' ')[0]
                line1 = ""
                line2 = ""

                for param in params.split('&'):
                    if param.startswith('line1='):
                        line1 = url_decode(param[6:])
                    elif param.startswith('line2='):
                        line2 = url_decode(param[6:])

                display_lcd(line1, line2)
                response = '{"ok":true}'
                content_type = 'application/json'

            elif '/clear' in request:
                display_lcd("", "")
                response = '{"ok":true}'
                content_type = 'application/json'

            elif '/status' in request:
                response = '{"line1":"' + current_line1 + '","line2":"' + current_line2 + '"}'
                content_type = 'application/json'

            else:
                response = get_html()
                content_type = 'text/html'

            client.send(f'HTTP/1.0 200 OK\r\nContent-type: {content_type}\r\n\r\n')
            client.send(response)
            client.close()

        except Exception as e:
            print(f"Error: {e}")
            try:
                client.close()
            except:
                pass


# 메인 실행
def main():
    ip = connect_wifi()
    if ip:
        time.sleep(2)
        display_lcd("Ready!", "Enter text...")
        start_server(ip)


if __name__ == "__main__":
    main()
