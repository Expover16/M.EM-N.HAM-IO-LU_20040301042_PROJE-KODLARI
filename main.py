import pytesseract
import cv2 as cv
import pandas as pd
from datetime import datetime
import os
from ultralytics import YOLO
import asyncio

# Tesseract yolunu belirtin
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\MUHAMMED\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'
df = pd.DataFrame(columns=["Müşteri Kodu", "Tedarikçi Kodu", "Ürün İsmi", "Ürün Adeti"])
class_names = {
    0: 'label',
}
model = YOLO("last.pt")

# Görüntülerin bulunduğu dizin
images_dir = "C:/Users/MUHAMMED/Desktop/Yeni klasör (3)/image_path"

# Eş zamanlı işlem için kullanılacak değişken
all_labels_info = []

async def process_image(image_file):
    global df  # df değişkenini global kapsamda tanımla

    image_path = os.path.join(images_dir, image_file)
    image = cv.imread(image_path)

    detections = model(image)[0]

    # Her etiketin bilgilerini saklamak için liste
    labels_info = []

    # YOLO sonuçlarını çerçeve üzerine çiz
    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score, ID = detection
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

        # Set a threshold for the confidence score (adjust as needed)
        if score >= 0.3:  # yüzde doğruluk oranına göre çizim yapar.
            color = (0, 255, 0)  # Yeşil renk
            thickness = 2

            cv.rectangle(image, (x1, y1), (x2, y2), color, thickness)
            box2 = [x1, y1, x2, y2]  # Her bir dikdörtgen için box2'yi tanımla

            if int(ID) in class_names:
                class_name = class_names[int(ID)]
            else:
                class_name = 'Unknown'

            text = f"{class_name}"
            text_position = (x1 + 50, y1)
            font = cv.FONT_HERSHEY_SIMPLEX
            font_scale = 0.7
            font_color = (0, 255, 0)
            font_thickness = 1

            cv.putText(image, text, text_position, font, font_scale, font_color, font_thickness)
            cropped_image = image[y1:y2, x1:x2]

            # Tesseract ile metin tanıma yap
            detected_text = pytesseract.image_to_string(cropped_image, lang='tur')

            # Tanınan metni yazdır
            print("Detected Text:", detected_text)

            parts = detected_text.split()

            # DataFrame'e ekle
            if len(parts) >= 4:
                df = df.append({
                    "Müşteri Kodu": parts[0],
                    "Tedarikçi Kodu": parts[1],
                    "Ürün İsmi": " ".join(parts[2:-1]),
                    "Ürün Adeti": parts[-1]
                }, ignore_index=True)

        # Görüntü adı ekle
        for label in labels_info:
            label["Görüntü Adı"] = image_file

        # Resimdeki farklı ürün sayısını hesapla
        unique_products_count = len(labels_info)

        # Farklı ürün sayısını kaydet
        for label in labels_info:
            label["Farklı Ürün Sayısı"] = unique_products_count

        all_labels_info.extend(labels_info)

        # İşlenen görüntüyü göster
        cv.imshow(f"Goruntu - {image_file}", image)
        cv.waitKey(0)
        cv.destroyAllWindows()

async def process_images():
    # Görüntülerin bulunduğu dizindeki tüm dosyaları al
    image_files = os.listdir(images_dir)
    tasks = [process_image(image_file) for image_file in image_files]
    await asyncio.gather(*tasks)
    
async def camera_stream():
    global df  # df değişkenini global kapsamda tanımla

    # Kamera başlat
    cap = cv.VideoCapture(0)
    while True:
        # Kamera görüntüsünü yakala
        ret, frame = cap.read()

        # Eğer görüntü başarılı bir şekilde yakalandıysa işleme devam et
        if ret:
            # Görüntüyü siyah beyaz yap
            gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

            # Tesseract ile metin tanıma yap
            detected_text = pytesseract.image_to_string(gray, lang='tur')

            # Tanınan metni ekrana yazdır
            cv.putText(frame, detected_text, (50, 50), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

            # Görüntüyü ekrana göster
            cv.imshow('Etiket Tarama', frame)
            parts = detected_text.split()
            # DataFrame'e ekle
            if len(parts) >= 4:
                df = df.append({
                    "Müşteri Kodu": parts[0],
                    "Tedarikçi Kodu": parts[1],
                    "Ürün İsmi": " ".join(parts[2:-1]),
                    "Ürün Adeti": parts[-1]
                }, ignore_index=True)

        # Çıkış için 'q' tuşuna basılmasını bekle
        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    # Kamerayı kapat
    cap.release()

def main():
    print("1. Görüntü Dosyalarını İşle")
    print("2. Kamera Akışını Kullanarak İşle")
    choice = int(input("Bir seçenek seçin: "))

    if choice == 1:
        asyncio.run(process_images())
    elif choice == 2:
        asyncio.run(camera_stream())
    else:
        print("Geçersiz seçenek.")

    # Benzersiz dosya ismi oluştur
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"etiketler_{timestamp}.xlsx"

    # Tüm etiket bilgilerini Excel dosyasına yaz
    df.to_excel(excel_filename, index=False)

    print(f"Etiket bilgileri '{excel_filename}' dosyaqsına başarılı bir şekilde kaydedildi.")

if __name__ == "__main__":
    main()