# Required Libraries"
# micropython-uuid
# micropython-bme280

from data import Data
from machine import Pin
import time
import uuid
  
start_btn = Pin(7, Pin.IN, Pin.PULL_UP)
stop_btn = Pin(8, Pin.IN, Pin.PULL_UP)


with Data() as data:
    local_ip = data.wlan.ifconfig()[0]

    try:
        while True:
            time.sleep(1)
            if start_btn.value() == 0:
                while True:
                    time.sleep(2)
                    if stop_btn.value() == 0:
                        break
                    payload = {
                        "picow": {
                            "id": uuid.uuid1(),
                            "local_ip": local_ip,
                            "temperature": data.get_board_temperature(),
                        },
                        "bme280": data.read_bme280(),
                    }
                    data.remoteHost_send(payload)

    except Exception as e:
        print(f"[*Exception]: {e}")
    except KeyboardInterrupt:
        print("[*] Keyboard Program Interrupted.")
        print(f"Exception(KeyboardInterrupt)")

