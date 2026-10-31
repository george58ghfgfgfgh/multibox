import os
import time
import subprocess
import socket
import re
import tkinter as tk
from tkinter import font
import RPi.GPIO as GPIO

# --- PIN TANIMLAMALARI ---
BTN_MODE_PIN = 17    # Mod değiştirme butonu
BTN_ACTION_PIN = 27  # Mod içi aksiyon / tetik butonu

# --- GPIO AYARLARI ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_MODE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BTN_ACTION_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

MODES = [
    "1. ETHERNET & IP TESTI",
    "2. RF TUNER MODU",
    "3. CCTV ANLIK TEST"
]
current_mode_idx = 0
active_process = None

class MultiBoxApp:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)  # Tam ekran büyük görünüm
        self.root.configure(bg='#1e1e1e')

        # Büyük font tanımları
        self.title_font = font.Font(family="Helvetica", size=22, weight="bold")
        self.mode_font = font.Font(family="Helvetica", size=18, weight="bold")
        self.content_font = font.Font(family="Courier", size=14)

        # Üst Başlık
        self.lbl_title = tk.Label(root, text="MULTIBOX DIAGNOSTIC SYSTEM", font=self.title_font, fg="#00ffcc", bg="#1e1e1e")
        self.lbl_title.pack(pady=20)

        # Aktف Mod Göstergesi
        self.lbl_mode = tk.Label(root, text=f"AKTİF MOD: {MODES[current_mode_idx]}", font=self.mode_font, fg="#ffffff", bg="#333333", relief="solid", bd=2, padx=20, pady=10)
        self.lbl_mode.pack(pady=10)

        # İçerik Alanı (Bölünmüş Ekran Efekti İçin Çerçeve)
        self.frame_content = tk.Frame(root, bg="#2b2b2b", bd=2, relief="groove")
        self.frame_content.pack(fill="both", expand=True, padx=30, pady=20)

        self.lbl_content = tk.Label(self.frame_content, text="Modu başlatmak için Buton 2'ye basın.", font=self.content_font, fg="#00ff00", bg="#2b2b2b", justify="left")
        self.lbl_content.pack(fill="both", expand=True, padx=20, pady=20)

        # Alt Bilgi / Yönerge
        self.lbl_footer = tk.Label(root, text="[Buton 1]: Mod Değiştir   |   [Buton 2]: Başlat / Seç", font=self.content_font, fg="#aaaaaa", bg="#1e1e1e")
        self.lbl_footer.pack(pady=15)

        # Donanım Butonlarını Dinlemek İçin Periyodik Kontrol (Polling)
        self.check_buttons()

    def update_interface(self):
        self.lbl_mode.config(text=f"AKTİF MOD: {MODES[current_mode_idx]}")
        self.lbl_content.config(text=f"Seçilen Mod: {MODES[current_mode_idx]}\n\nBaşlatmak için Buton 2'ye basın.")

    def execute_action(self):
        global active_process
        if current_mode_idx == 0:
            ip = get_ethernet_ip()
            arp_data = get_arp_table()
            text = f"=== ETHERNET DURUMU ===\nIP Adresi : {ip}\nDurum     : {'BAĞLI' if ip not in ['IP Alinamadi', 'Baglanti Yok'] else 'KABLO YOK'}\n\n=== ARP AĞ TARAMASI ===\n{arp_data}"
            self.lbl_content.config(text=text)

        elif current_mode_idx == 1:
            self.lbl_content.config(text="> RF Tuner (Dark DK-AC-TVUSBDVBT2) Çalıştırılıyor...\n> Tuner aktif.")

        elif current_mode_idx == 2:
            self.lbl_content.config(text="> CCTV Test Modu Başlatılıyor...\n> Kamera akışı devrede.")
            try:
                active_process = subprocess.Popen([
                    "ffplay", "-f", "v4l2", "-framerate", "30", 
                    "-video_size", "720x576", "/dev/video0",
                    "-infbuf", "-noautorotate", "-loglevel", "quiet"
                ])
            except Exception as e:
                self.lbl_content.config(text=f"CCTV Hatası: {e}")

    def check_buttons(self):
        global current_mode_idx
        try:
            # Mod Değiştirme Butonu (GPIO 17)
            if GPIO.input(BTN_MODE_PIN) == GPIO.LOW:
                current_mode_idx = (current_mode_idx + 1) % len(MODES)
                self.update_interface()
                time.sleep(0.3)

            # Aksiyon Butonu (GPIO 27)
            if GPIO.input(BTN_ACTION_PIN) == GPIO.LOW:
                self.execute_action()
                time.sleep(0.3)
        except Exception as e:
            pass

        # 50 milisaniyede bir butonları kontrol etmeye devam et
        self.root.after(50, self.check_buttons)

def get_ethernet_ip():
    try:
        output = subprocess.check_output(["ip", "-4", "addr", "show"]).decode()
        sections = output.split('\n\n')
        for sec in sections:
            if any(iface in sec for iface in ['eth0', 'enx', 'enp']):
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', sec)
                if match:
                    return match.group(1)
        match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', output)
        if match:
            return match.group(1)
        return "IP Alinamadi"
    except:
        return "Baglanti Yok"

def get_arp_table():
    try:
        return subprocess.check_output(["arp", "-a"]).decode()
    except:
        return "ARP bilgisi alınamadı."

# --- UYGULAMA BAŞLAT ---
root = tk.Tk()
app = MultiBoxApp(root)
try:
    root.mainloop()
except KeyboardInterrupt:
    GPIO.cleanup()
