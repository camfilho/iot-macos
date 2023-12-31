import network
import socket
import json
import time
from machine import ADC, Pin, I2C
from bme280 import BME280
import rp2
import binascii
import picozero
import ntptime
from ssd1306 import SSD1306_I2C


# Wifi, can be overwriten
wifi_sid = ""
wifi_pswd = ""

# Remote Host, can be overwriten
remote_port = 1500
remote_address = "192.168.1.80"

# i2c variables bme 280 and ssd1306
i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)

# Country Location
rp2.country('US')

class Data:
    def __init__(
        self, port=remote_port, host=remote_address, sid=wifi_sid, pwd=wifi_pswd
    ):
        self.wifi_sid = sid
        self.wifi_pswd = pwd
        self.remote_port = port
        self.remote_address = host
        self.wlan = network.WLAN()
        self.wlan.active(True)
        self.i2c = i2c
        self.bme = BME280(i2c=self.i2c)

    def __enter__(self):
        Pin("LED", Pin.OUT).on()
        self.wifi_connect()
        ntptime.settime()
        print("Press the button 1 to start streaming. and button 2 to stop.")
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        Pin("LED", Pin.OUT).off()
        Pin(2, Pin.OUT).off()
        Pin(3, Pin.OUT).off()

    def wifi_connect(self):
        try:
            for i in range(10):
                if self.wlan.isconnected() != True:
                    print("Waiting for connection...")
                    Pin(15, Pin.OUT).on()
                    self.wlan.connect(self.wifi_sid, self.wifi_pswd)
                    time.sleep(3)
                    Pin(15, Pin.OUT).off()
                    time.sleep(1)
                else:
                    print(f"* Local IP: {self.wlan.ifconfig()[0]}")
                    Pin(2, Pin.OUT).on()
                    Pin(15, Pin.OUT).off()
            return self.wlan
        except Exception as error:
            print(f"[*Exception] has been occured while connecting to wifi.: {error}")

    def remoteHost_send(self, dictionary: dict):
        try:
            sock = socket.socket()
            sock.connect((self.remote_address, self.remote_port))
            jsondata = json.dumps(dictionary)
            print(f"[*] Sending json to remote host {self.remote_address}:\n{jsondata}")
            Pin(3, Pin.OUT).on()
            sock.send(jsondata)
            sock.close()
            time.sleep(0.5)
            Pin(3, Pin.OUT).off()
        except Exception as error:
            print(
                f"[*Exception]: An error has been occured while connecting to remote host: {error}"
            )
            raise Exception(f"Remote Host Unrechhable: {error}")
        
    def list_networks(self):
        networks = self.wlan.scan() # list with tuples (ssid, bssid, channel, RSSI, security, hidden)
        networks.sort(key=lambda x:x[3],reverse=True) # sorted on RSSI (3)
        for i, w in enumerate(networks):
              print(i+1, w[0].decode(), binascii.hexlify(w[1]).decode(), w[2], w[3], w[4], w[5])

    def get_board_temperature(self) -> float:
        return picozero.pico_temp_sensor.temp

    def read_bme280(self):
        temp, press, hum = self.bme.values
        now = time.gmtime()
        return {
            "temperature": temp,
            "pressure": press,
            "humidity": hum,
            "read_datetime": f"{now[0]}-{now[1]}-{now[2]} {now[3]}:{now[4]}:{now[5]}",
        }
    
    def display(self):
        temp, press, hum = self.bme.values
        ip = self.wlan.ifconfig()[0]
        oled.fill(0)
        oled.text(f"IP:{ip}",0,0)
        oled.text(f"Temp:{temp}",0,10)
        oled.text(f"Hum:{hum}",0,20)
        oled.text(f"Press:{press}",0,30)
        oled.text(f"Streaming [{remote_port}]:",0,40)
        oled.text(f"{remote_address}",0,50)
        oled.show()
