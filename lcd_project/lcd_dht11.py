import sys
import os

current_path = os.getcwd()
lcd_project_path = current_path + '/lcd_project'

if lcd_project_path not in sys.path:
    sys.path.append(lcd_project_path)
    print(f"경로 추가됨: {lcd_project_path}")

from machine import Pin, I2C
import utime
from lcd_project.lcd_api import LcdApi
from lcd_project.i2c_lcd import I2cLcd
from dht import DHT11

# I2C 설정 (GPIO 6을 SDA로, GPIO 3을 SCL로 사용)
i2c = I2C(1, sda=Pin(6), scl=Pin(3), freq=100000)

# DHT11 센서 설정 (GPIO 28에 연결)
dht_sensor = DHT11(Pin(28))

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


# DHT11 센서에서 온습도 읽기 함수
def read_sensor():
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()

        print(f"온도: {temperature}°C, 습도: {humidity}%")

        # LED 깜빡임으로 측정 표시
        led.value(1)
        utime.sleep(0.1)
        led.value(0)

        return temperature, humidity

    except Exception as e:
        print("센서 읽기 오류:", e)
        return None, None


# LCD 초기화 및 시작 메시지 표시
lcd.clear()
display_text("DHT11 온습도 측정", 0)
display_text("시작...", 1)
utime.sleep(2)

print("DHT11 온도 및 습도 모니터링 시작")
print("LCD에 측정값을 표시합니다...")

# 메인 루프
while True:
    # 온습도 읽기
    temp, humi = read_sensor()

    if temp is not None and humi is not None:
        # LCD에 온습도 표시
        temp_str = f"Temp: {temp:.1f}C"
        humi_str = f"Humi: {humi:.1f}%"

        display_text(temp_str, 0)
        display_text(humi_str, 1)
    else:
        # 에러 표시
        display_text("Error reading", 0)
        display_text("DHT11 sensor", 1)

    # 5초 대기
    utime.sleep(5)
