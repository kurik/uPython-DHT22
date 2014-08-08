import DHT22
import pyb

def measure(led, lcd):
    try:
        (hum, tem) = DHT22.measure()
        if ((hum == 0) and (tem == 0)) or (hum > 100):
            raise ValueError('Invalid data received from sensor')
        lcd.write('\nHumidity: %s%%\n    Temp: %sC\n\n' % (hum, tem)) 
        led.off()
    except Exception as e:
        lcd.write(str(e) + '\n')
        led.on()

DHT22.init()
lcd = pyb.LCD('X')
lcd.light(True)
led_red = pyb.LED(1) # 1 = Red

while True:
    measure(led_red, lcd)
    pyb.delay(3000)
    

