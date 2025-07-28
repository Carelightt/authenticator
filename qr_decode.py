from pyzbar.pyzbar import decode
from PIL import Image

# 📂 QR görüntüsünün dosya adını yaz
img = Image.open("qr_kodum.png")

# QR'ı çöz
data = decode(img)[0].data.decode()

print("🎯 QR'dan çıkan veri:")
print(data)
