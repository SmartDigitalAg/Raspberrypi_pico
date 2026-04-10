import machine
import utime
from dht import DHT11

dht_sensor = DHT11(machine.Pin(28))
led = machine.Pin("LED", machine.Pin.OUT)

def read_sensor():
    try:
        dht_sensor.measure()
        temperature = dht_sensor.temperature()
        humidity = dht_sensor.humidity()

        print(f"온도: {temperature}°C, 습도: {humidity}%")

        led.value(1)
        utime.sleep(0.1)
        led.value(0)

        return temperature, humidity

    except Exception as e:
        print("센서 읽기 오류:", e)
        return None, None

print("DHT11 온도 및 습도 모니터링 시작")
print("5초마다 측정값을 출력합니다...")

while True:
    read_sensor()
    utime.sleep(5)
