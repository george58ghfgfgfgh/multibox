import os
import time
import subprocess
import socket
import RPi.GPIO as GPIO

# --- PIN TANIMLAMALARI ---
BTN_MODE_PIN = 17   # Mod değiştirme butonu
BTN_ACTION_PIN = 27 # Mod içi aksiyon / tetik butonu

# --- GPIO AYARLARI ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_MODE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ACTION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# --- MODLAR ---
MODES = [
    "1. IP & Kablo Testi",
    "2. RF Tuner Modu",
    "3. CCTV Anlik Test"
]
current_mode_idx = 0
active_process = None

def clear_screen():
    os.system('clear')

def set_tv_out(state):
    """TV-Out çıkışını kapatır veya açar (state: True = Açık, False = Kapalı)"""
    try:
        if state:
            # TV Out / Composite sinyalini tekrar aç
            subprocess.run(["tvservice", "-p"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            # TV Out sinyalini kısa süreliğine kapat
            subprocess.run(["tvservice", "-o"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"TV Out Hatası: {e}")

def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "IP Alinamadi"

def draw_interface():
    clear_screen()
    print("========================================")
    print("         MULTIBOX TEST CIHAZI           ")
    print("========================================")
    print(f"\nAktif Mod: [{MODES[current_mode_idx]}]\n")
    print("----------------------------------------")
    print("Buton 1 (GPIO 17): Mod Degistir")
    print("Buton 2 (GPIO 16): Modu Baslat / Islem Yap")
    print("========================================")

def execute_mode_action():
    global active_process
    # Eğer çalışan eski bir process varsa kapat
    if active_process and active_process.poll() is None:
        active_process.terminate()
        active_process = None

    clear_screen()
    print(f"[{MODES[current_mode_idx]}] Calistiriliyor...\n")

    if current_mode_idx == 0:
        # Mod 1: IP ve Kablo Testi
        ip = get_ip_address()
        print(f"> Cihaz IP Adresi: {ip}")
        print("> Ethernet Kablosu ve Ag Taramasi Yapiliyor...")
        # Örnek ping veya arp taraması eklenebilir
        subprocess.run(["arp", "-a"])
        input("\nAna menüye dönmek için Enter'a basın...")

    elif current_mode_idx == 1:
        # Mod 2: RF Tuner Modu
        print("> RF Tuner (Dark DK-AC-TVUSBDVBT2) Baslatiliyor...")
        # Tuner uygulaması veya ffplay komutu buraya yazılabilir
        # Örnek: aktif_process = subprocess.Popen(["dvb-fe-tool", ...])
        print("Tuner aktif. Çıkmak için Buton 2'ye basın.")
        time.sleep(2)

    elif current_mode_idx == 2:
        # Mod 3: CCTV Anlık Testi (TV-Out kapatma senaryosu)
        print("> CCTV Test Moduna Giriliyor...")
        print("> TV-Out geçici olarak kapatılıyor...")
        
        # İstediğin gibi TV out'u kısa süreliğine kapatıyoruz
        set_tv_out(False)
        time.sleep(1) # Kısa bir bekleme
        
        # İşlem bittikten / moddan çıkarken tekrar açmak üzere simülasyon veya ffplay
        try:
            # CCTV akışını açmak için ffplay komutu (örnek)
            active_process = subprocess.Popen([
                "ffplay", "-f", "v4l2", "-framerate", "30", 
                "-video_size", "720x576", "/dev/video0"
            ])
            active_process.wait()
        except KeyboardInterrupt:
            pass
        finally:
            # Moddan çıkıldığında TV out'u geri aç
            print("> TV-Out tekrar açılıyor...")
            set_tv_out(True)

# --- ANA DÖNGÜ ---
draw_interface()

try:
    while True:
        # Mod Değiştirme Butonu (GPIO 17)
        if GPIO.input(BTN_MODE_PIN) == GPIO.LOW:
            current_mode_idx = (current_mode_idx + 1) % len(MODES)
            
            # Eğer Mod 3'ten çıkılıyorsa TV-out'un açık olduğundan emin olalım
            set_tv_out(True)
            
            draw_interface()
            time.sleep(0.3) # Debounce (titreşim) önleme

        # Mod İçi Aksiyon Butonu (GPIO 16)
        if GPIO.input(BTN_ACTION_PIN) == GPIO.LOW:
            execute_mode_action()
            draw_interface()
            time.sleep(0.3)

        time.sleep(0.05)

except KeyboardInterrupt:
    set_tv_out(True)
    GPIO.cleanup()
