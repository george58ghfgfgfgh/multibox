import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
pins = [16, 17]
for p in pins:
    GPIO.setup(p, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print('Canli izleme baslatildi. Butonlara basin (Cikis icin Ctrl+C):')
try:
    while True:
        status = ' | '.join([f'GPIO {p}: {GPIO.input(p)}' for p in pins])
        print(status, end='\\r')
        time.sleep(0.1)
except KeyboardInterrupt:
    GPIO.cleanup()
    print('\\nKapatildi.')
'''
with open('live_test.py', 'w') as f:
    f.write(code)
"
