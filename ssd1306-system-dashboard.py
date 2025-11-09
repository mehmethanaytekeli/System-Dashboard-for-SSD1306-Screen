import time
import psutil
import netifaces
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from luma.oled.device import ssd1306
from luma.core.interface.serial import i2c

try:
    # Ekranı başlatıyoruz
    serial = i2c(port=1, address=0x3C)
    disp = ssd1306(serial)

    # Font ayarı
    font = ImageFont.load_default()

    # Görüntü oluşturma
    image = Image.new('1', (disp.width, disp.height))
    draw = ImageDraw.Draw(image)

    # Yazma işlemi için konum
    x = 0
    y = 4

    # Sonraki okuma için eski ağ verisi
    prev_recv = psutil.net_io_counters().bytes_recv
    prev_sent = psutil.net_io_counters().bytes_sent

    def format_speed(speed):
        # speed (hız) zaten KB/s cinsinden geliyor
        if speed > 1024:
            return f"{speed / 1024:.1f}MB/s"
        else:
            return f"{speed:.1f}KB/s"

    while True:
        # Ana döngüyü de try-except içine alalım ki
        # sensör okuma hatası gibi başka bir hata olursa komut dosyası çökmesin
        try:
            # Bilgileri toplama
            cpu_temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
            ram_usage = psutil.virtual_memory().percent
            current_time = datetime.now().strftime('%H:%M:%S')
            cpu_usage = psutil.cpu_percent(interval=0.1)

            # --- IP ADRESİ GÜNCELLEMESİ ---
            # IP adresini almayı dene
            try:
                ip_address = netifaces.ifaddresses('eth0')[netifaces.AF_INET][0]['addr']
            except (KeyError, IndexError):
                # Başarısız olursa "disconnect" yaz
                ip_address = "disconnect"
            # --- GÜNCELLEME SONU ---

            # Ağ hızı bilgisi (saniyede KB olarak)
            curr_recv = psutil.net_io_counters().bytes_recv
            curr_sent = psutil.net_io_counters().bytes_sent
            
            # 1 saniyelik farkı KB'a böl
            download_speed = (curr_recv - prev_recv) / 1024
            upload_speed = (curr_sent - prev_sent) / 1024
            
            prev_recv, prev_sent = curr_recv, curr_sent

            # Ekranı temizle
            draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)

            # Bilgileri çiz
            draw.text((x, y), f"    Time: {current_time}", font=font, fill=255)
            draw.text((x, y + 10), f"CPU: {round(cpu_temp)}°C", font=font, fill=255)
            draw.text((x, y + 20), f"Usage: {cpu_usage}%", font=font, fill=255)
            draw.text((x, y + 30), f"IP: {ip_address}", font=font, fill=255) # Güncellenen satır
            draw.text((x, y + 40), f"RAM: {ram_usage}%", font=font, fill=255)

            # Ok çizimleri (Daha mantıklı sıralama)
            arrow_y = y + 52
            
            # Sol Taraf: Download ▼
            draw.polygon([(0, arrow_y+2), (4, arrow_y+2), (2, arrow_y+5)], fill=255)  # ▼
            draw.text((6, arrow_y-2), format_speed(download_speed), font=font, fill=255)

            # Sağ Taraf: Upload ▲
            draw.polygon([(64, arrow_y+5), (68, arrow_y+5), (66, arrow_y+2)], fill=255) # ▲
            draw.text((70, arrow_y-2), format_speed(upload_speed), font=font, fill=255)

            # Ekranı güncelle
            disp.display(image)
        
        except Exception as e:
            # Beklenmedik bir hata olursa ekrana yazdır (çökme yerine)
            try:
                draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
                draw.text((x, y), "Hata olustu:", font=font, fill=255)
                draw.text((x, y + 10), str(e), font=font, fill=255)
                disp.display(image)
            except:
                pass # Ekrana yazarken de hata olursa döngüye devam et

        time.sleep(1)

except KeyboardInterrupt:
    print("Program sonlandirildi.")
    # Ekranı temizle ve kapat
    draw.rectangle((0, 0, disp.width, disp.height), outline=0, fill=0)
    disp.display(image)
except Exception as e:
    print(f"Kritik hata: {e}")
    # Kritik bir başlangıç hatası olursa (örn. I2C bulunamadı)
