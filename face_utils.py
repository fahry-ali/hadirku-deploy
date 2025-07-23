import face_recognition
import numpy as np
import pickle
import os
import cv2
from models import User

def optimize_image_for_recognition(image_rgb, max_width=640):
    """
    Optimasi ukuran gambar untuk mengurangi beban processing
    """
    height, width = image_rgb.shape[:2]
    if width > max_width:
        scale = max_width / width
        new_width = int(width * scale)
        new_height = int(height * scale)
        return cv2.resize(image_rgb, (new_width, new_height))
    return image_rgb

def generate_encoding_from_image(image_rgb):
    """
    Menghasilkan satu face encoding dari sebuah gambar (format RGB).
    Mengembalikan None jika tidak ada wajah atau ada lebih dari satu wajah.
    """
    # Optimasi ukuran gambar
    optimized_image = optimize_image_for_recognition(image_rgb)
    
    # Deteksi lokasi wajah dalam gambar dengan model yang lebih ringan
    face_locations = face_recognition.face_locations(optimized_image, model="hog")

    # Validasi: Pastikan hanya ada SATU wajah untuk pendaftaran
    if len(face_locations) != 1:
        return None

    # Hasilkan encoding dari wajah yang ditemukan
    # Ambil encoding pertama (dan satu-satunya)
    face_encodings = face_recognition.face_encodings(optimized_image, known_face_locations=face_locations)
    
    return face_encodings[0]

def find_match_in_db(unknown_image_rgb):
    """
    Mencari kecocokan wajah dari gambar dengan semua encoding yang ada di database.
    Mengembalikan ID user yang cocok atau None.
    """
    # Optimasi ukuran gambar
    optimized_image = optimize_image_for_recognition(unknown_image_rgb)
    
    # Ambil semua pengguna yang sudah punya data encoding wajah
    users_with_faces = User.query.filter(User.face_encoding.isnot(None)).all()
    if not users_with_faces:
        return None, "Database wajah kosong. Tidak ada referensi untuk perbandingan."

    # Siapkan data untuk perbandingan
    known_encodings = [pickle.loads(user.face_encoding) for user in users_with_faces]
    known_user_ids = [user.id for user in users_with_faces]

    # Deteksi semua wajah di gambar dari webcam dengan model yang lebih ringan
    unknown_face_locations = face_recognition.face_locations(optimized_image, model="hog")
    if not unknown_face_locations:
        return None, "Tidak ada wajah terdeteksi di kamera."
        
    unknown_face_encodings = face_recognition.face_encodings(optimized_image, known_face_locations=unknown_face_locations)

    # Toleransi dari environment variable atau default
    tolerance = float(os.environ.get('FACE_RECOGNITION_TOLERANCE', 0.5))

    # Bandingkan setiap wajah yang ditemukan dengan database
    for unknown_encoding in unknown_face_encodings:
        # Fungsi compare_faces mengembalikan list [True, False, True, ...]
        matches = face_recognition.compare_faces(known_encodings, unknown_encoding, tolerance=tolerance)
        
        # Cari indeks pertama yang cocok (bernilai True)
        if True in matches:
            first_match_index = matches.index(True)
            matched_user_id = known_user_ids[first_match_index]
            return matched_user_id, "Wajah dikenali."
            
    return None, "Wajah tidak dikenali di dalam database."