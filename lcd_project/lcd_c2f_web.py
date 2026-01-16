import sys
import os

# 현재 경로 설정
current_path = os.getcwd()
lcd_project_path = current_path + '/lcd_project'
if lcd_project_path not in sys.path:
    sys.path.append(lcd_project_path)
    print(f"경로 추가됨: {lcd_project_path}")

import network
import socket
import time
from machine import Pin, I2C
import utime
from lcd_project.lcd_api import LcdApi
from lcd_project.i2c_lcd import I2cLcd

# Wi-Fi 설정
ssid = 'SmartDigitalAgLab'
password = 'Smartfarm208!'

# I2C 설정 (GPIO 6을 SDA로, GPIO 3을 SCL로 사용)
i2c = I2C(1, sda=Pin(6), scl=Pin(3), freq=100000)

# LED 설정
led = Pin("LED", Pin.OUT)

# I2C 장치 스캔
devices = i2c.scan()
if devices:
    print("발견된 I2C 장치:", [hex(d) for d in devices])
    lcd_addr = devices[0]
else:
    print("I2C 장치를 찾을 수 없습니다!")
    print("연결을 확인하세요.")
    while True:
        pass  # 장치가 없으면 멈춤

# LCD 설정
LCD_ROWS = 2
LCD_COLS = 16
lcd = I2cLcd(i2c, lcd_addr, LCD_ROWS, LCD_COLS)


# LCD에 텍스트 표시 함수
def display_text(text, row=0):
    lcd.move_to(0, row)
    # 기존 텍스트 지우기 (16칸 공백으로 채움)
    lcd.putstr(" " * LCD_COLS)
    lcd.move_to(0, row)
    lcd.putstr(text)


# 섭씨를 화씨로 변환하는 함수
def celsius_to_fahrenheit(celsius):
    return (celsius * 9 / 5) + 32


# WiFi에 연결
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)

    # 이미 연결되어 있는지 확인
    if not wlan.isconnected():
        print("Wi-Fi에 연결 중...")
        display_text("Connecting WiFi", 0)
        wlan.connect(ssid, password)

        # 연결될 때까지 대기
        max_wait = 10
        while max_wait > 0:
            if wlan.isconnected():
                break
            max_wait -= 1
            print("연결 대기 중...")
            time.sleep(1)

        # 연결 실패 시
        if not wlan.isconnected():
            print("Wi-Fi 연결 실패!")
            display_text("WiFi Failed!", 0)
            return None

    # 연결 성공
    status = wlan.ifconfig()
    ip = status[0]
    print(f"연결됨! IP: {ip}")
    display_text(f"IP:{ip}", 0)
    return ip


# HTML 양식 - 이전 입력값을 유지하기 위해 수정
def webpage_html(last_celsius=""):
    html = f"""<!DOCTYPE html>
    <html>
    <head>
        <title>온도 변환기</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial; text-align: center; margin: 20px; }}
            .container {{ max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; }}
            input, button {{ padding: 10px; margin: 10px; }}
            button {{ background-color: #4CAF50; color: white; border: none; cursor: pointer; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>섭씨 → 화씨 변환</h2>
            <form action="/convert">
                <p>섭씨 온도: <input type="number" step="0.1" name="celsius" value="{last_celsius}" required></p>
                <p><button type="submit">변환하기</button></p>
            </form>
            <div id="result">%result%</div>
        </div>
    </body>
    </html>
    """
    return html


# 웹 서버 실행
def run_server():
    ip = connect_to_wifi()
    if not ip:
        return

    # 소켓 생성
    addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 포트 재사용 옵션
    s.bind(addr)
    s.listen(1)

    print('웹 서버 시작, http://%s 에 접속하세요' % ip)
    display_text("Server Ready", 1)

    # 결과 저장 변수
    last_result = ""
    last_celsius = ""

    # 서버 루프
    while True:
        try:
            cl, addr = s.accept()
            print('클라이언트 연결됨:', addr)

            # LED 깜빡임으로 연결 표시
            led.value(1)

            request = cl.recv(1024)
            request = str(request)

            # 요청 확인
            celsius_input = None
            if 'GET /convert' in request:
                celsius_param = request.find('celsius=')
                if celsius_param > 0:
                    # 파라미터에서 섭씨 값 추출
                    celsius_str = request[celsius_param + 8:]
                    celsius_end = celsius_str.find('&')
                    if celsius_end == -1:
                        celsius_end = celsius_str.find(' ')
                    celsius_str = celsius_str[:celsius_end]

                    try:
                        celsius_input = float(celsius_str)
                        last_celsius = celsius_str  # 마지막 입력값 저장
                    except ValueError:
                        celsius_input = None

            # 응답 생성
            response = ""
            if celsius_input is not None:
                # 섭씨 → 화씨 변환
                fahrenheit = celsius_to_fahrenheit(celsius_input)
                result_text = f"섭씨 {celsius_input}°C는 화씨 {fahrenheit:.1f}°F 입니다."

                # LCD에 표시
                display_text(f"C: {celsius_input:.1f}", 0)
                display_text(f"F: {fahrenheit:.1f}", 1)

                # 결과 저장
                last_result = result_text

                # 결과 포함한 HTML 응답
                response = webpage_html(last_celsius).replace('%result%', result_text)
            else:
                # 기본 HTML 응답
                response = webpage_html(last_celsius).replace('%result%', last_result)

            # 응답 전송 - UTF-8 인코딩 설정 추가
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html; charset=utf-8\r\n\r\n')
            cl.send(response)
            cl.close()

            # LED 끄기
            led.value(0)

        except Exception as e:
            print("오류 발생:", e)
            cl.close()
            led.value(0)


# 초기 메시지 표시
lcd.clear()
display_text("Temperature", 0)
display_text("Converter", 1)
utime.sleep(2)

# 메인 실행
if __name__ == "__main__":
    print("온도 변환 웹 서버 시작")
    run_server()