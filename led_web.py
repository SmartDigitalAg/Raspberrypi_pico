import network
import socket
import time
from machine import Pin

# Set up LED
led = Pin('LED', Pin.OUT)

# Wi-Fi credentials - replace with your own
ssid = 'SmartDigitalAgLab'
password = 'Smartfarm208!'


# Connect to Wi-Fi
def connect_to_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)

    # Wait for connection with timeout
    max_wait = 10
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('Waiting for connection...')
        time.sleep(1)

    # Handle connection status
    if wlan.status() != 3:
        print('Network connection failed')
        return None
    else:
        status = wlan.ifconfig()
        print(f'Connected to {ssid}')
        print(f'IP address: {status[0]}')
        return status[0]


# HTML content for web interface
def get_html():
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Pico W LED Control</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                margin: 20px;
            }
            .button {
                display: inline-block;
                padding: 15px 30px;
                font-size: 18px;
                cursor: pointer;
                text-align: center;
                text-decoration: none;
                outline: none;
                color: #fff;
                background-color: #4CAF50;
                border: none;
                border-radius: 15px;
                box-shadow: 0 9px #999;
                margin: 10px;
            }
            .button:hover {background-color: #3e8e41}
            .button:active {
                background-color: #3e8e41;
                box-shadow: 0 5px #666;
                transform: translateY(4px);
            }
            .button-red {
                background-color: #f44336;
            }
            .button-red:hover {background-color: #d32f2f}
            .status {
                font-size: 18px;
                margin: 20px;
            }
        </style>
    </head>
    <body>
        <h1>Raspberry Pi Pico W LED Control</h1>
        <div class="status">LED Status: <span id="status">Checking...</span></div>
        <div>
            <button class="button" onclick="turnOn()">Turn ON</button>
            <button class="button button-red" onclick="turnOff()">Turn OFF</button>
        </div>

        <script>
            function updateStatus() {
                fetch('/status')
                    .then(response => response.text())
                    .then(data => {
                        document.getElementById('status').textContent = data;
                    });
            }

            function turnOn() {
                fetch('/on')
                    .then(response => response.text())
                    .then(data => {
                        updateStatus();
                    });
            }

            function turnOff() {
                fetch('/off')
                    .then(response => response.text())
                    .then(data => {
                        updateStatus();
                    });
            }

            // Update status when page loads
            updateStatus();
        </script>
    </body>
    </html>
    """
    return html


# Start web server
def start_server(ip):
    # Open socket
    addr = (ip, 80)
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # 포트 재사용 옵션
    s.bind(addr)
    s.listen(1)

    print(f'Web server started on http://{ip}')

    # Listen for connections
    while True:
        try:
            client, addr = s.accept()
            print(f'Client connected from {addr}')
            request = client.recv(1024)
            request = str(request)

            # Process request
            if '/on' in request:
                led.value(1)
                response = "ON"
            elif '/off' in request:
                led.value(0)
                response = "OFF"
            elif '/status' in request:
                response = "ON" if led.value() else "OFF"
            else:
                response = get_html()

            # Send response
            if '/status' in request or '/on' in request or '/off' in request:
                client.send('HTTP/1.0 200 OK\r\nContent-type: text/plain\r\n\r\n')
                client.send(response)
            else:
                client.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
                client.send(response)

            client.close()

        except Exception as e:
            print(f"Error: {e}")
            client.close()


# Main function
def main():
    ip = connect_to_wifi()
    if ip:
        start_server(ip)


if __name__ == "__main__":
    main()
