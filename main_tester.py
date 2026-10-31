import os
import time
import subprocess
import socket
import RPi.GPIO as GPIO

# --- PIN TANIMLAMALARI ---
BTN_MODE_PIN = 17    # Mod değiştirme butonu
BTN_ACTION_PIN = 27  # Mod içi aksiyon / tetik butonu

# --- GPIO AYARLARI ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_MODE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ACTION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- MODLAR ---
MODES = [
    "1. IP & KABLO TESTI",
    "2. RF TUNER MODU",
    "3. CCTV ANLIK TEST"
]
current_mode_idx = 0
active_process = None

def clear_screen():
    os.system('clear')

def draw_interface():
    clear_screen()
    print("=" * 66)
    print("  M U L T I B O X   D I A G N O S T I C   S Y S T E M  ")
    print("=" * 66)
    print("\n")
    print(f"   >>> AKTIF MOD: [ {MODES[current_mode_idx]} ] <<<   ")
    print("\n")
    print("-" * 66)
    print("  [ Buton 1 (GPIO 17) ] ---> Modu Degistir")
    print("  [ Buton 2 (GPIO 27) ] ---> Baslat / Islem Yap / Geri Don")
    print("=" * 66)

def execute_mode_action():
    global active_process
    if active_process and active_process.poll() is None:
        active_process.terminate()
        active_process = None

    clear_screen()
    print("=" * 66)
    print(f"   CALISTIRILIYOR: {MODES[current_mode_idx]}")
    print("=" * 66 + "\n")

    if current_mode_idx == 0:
        ip = get_ip_address()
        print(f"  > Cihaz IP Adresi : {ip}")
        print("  > Ag Taramasi ve ARP Tablosu Kontrol Ediliyor...\n")
        subprocess.run(["arp", "-a"])
        print("\n  [!] Ana menüye dönmek için Buton 2'ye basın...")
        
        while True:
            if GPIO.input(BTN_ACTION_PIN) == GPIO.LOW:
                time.sleep(0.3)
                break
            time.sleep(0.05)

    elif current_mode_idx == 1:
        print("  > RF Tuner (Dark DK-AC-TVUSBDVBT2) Baslatiliyor...")
        print("  > Tuner aktif. Çıkmak için Buton 2'ye basın.\n")
        
        while True:
            if GPIO.input(BTN_ACTION_PIN) == GPIO.LOW:
                time.sleep(0.3)
                break
            time.sleep(0.05)

    elif current_mode_idx == 2:
        print("  > CCTV Test Moduna Giriliyor...")
        print("  > Kamera akışı başlatılıyor (Çıkış için Buton 2)...\n")
        
        try:
            active_process = subprocess.Popen([
                "ffplay", "-f", "v4l2", "-framerate", "30", 
                "-video_size", "720x576", "/dev/video0",
                "-infbuf", "-noautorotate"
            ])
            
            while active_process.poll() is None:
                if GPIO.input(BTN_ACTION_PIN) == GPIO.LOW:
                    active_process.terminate()
                    break
                time.sleep(0.05)
                
        except Exception as e:
            print(f"  > CCTV Hatası: {e}")

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "IP Alinamadi"

# --- ANA DÖNGÜ ---
draw_interface()

try:
    while True:
        if GPIO.input(BTN_MODE_PIN) == GPIO.LOW:
            current_mode_idx = (current_mode_idx + 1) % len(MODES)
            draw_interface()
            time.sleep(0.3)

        if GPIO.input(BTN_ACTION_PIN) == GPIO.LOW:
            execute_mode_action()
            draw_interface()
            time.sleep(0.3)

        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()
