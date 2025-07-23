import cv2
import numpy as np
import pickle
import mediapipe as mp
from sklearn.metrics.pairwise import cosine_similarity
from models import User

# Initialize MediaPipe Face Detection dan Face Mesh
mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh

def extract_face_embedding_mediapipe(image_rgb):
    """
    Extract face embedding menggunakan MediaPipe (alternative untuk face_recognition)
    """
    with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
        with mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, 
                                   refine_landmarks=True, min_detection_confidence=0.5) as face_mesh:
            
            # Convert BGR to RGB if needed
            if len(image_rgb.shape) == 3:
                rgb_image = image_rgb
            else:
                rgb_image = cv2.cvtColor(image_rgb, cv2.COLOR_BGR2RGB)
            
            # Detect faces
            results = face_detection.process(rgb_image)
            
            if not results.detections or len(results.detections) != 1:
                return None
            
            # Get face mesh landmarks
            mesh_results = face_mesh.process(rgb_image)
            
            if not mesh_results.multi_face_landmarks:
                return None
            
            # Extract landmarks sebagai feature vector
            landmarks = mesh_results.multi_face_landmarks[0]
            
            # Convert landmarks ke array numpy
            face_embedding = []
            for landmark in landmarks.landmark:
                face_embedding.extend([landmark.x, landmark.y, landmark.z])
            
            return np.array(face_embedding, dtype=np.float32)

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
    Generate encoding menggunakan MediaPipe (replacement untuk face_recognition)
    """
    # Optimasi ukuran gambar
    optimized_image = optimize_image_for_recognition(image_rgb)
    
    # Extract embedding
    embedding = extract_face_embedding_mediapipe(optimized_image)
    
    return embedding

def find_match_in_db(unknown_image_rgb):
    """
    Mencari kecocokan wajah menggunakan MediaPipe dan cosine similarity
    """
    # Optimasi ukuran gambar
    optimized_image = optimize_image_for_recognition(unknown_image_rgb)
    
    # Extract embedding dari gambar unknown
    unknown_embedding = extract_face_embedding_mediapipe(optimized_image)
    
    if unknown_embedding is None:
        return None, "Tidak ada wajah terdeteksi di kamera."
    
    # Ambil semua pengguna yang sudah punya data encoding wajah
    users_with_faces = User.query.filter(User.face_encoding.isnot(None)).all()
    if not users_with_faces:
        return None, "Database wajah kosong. Tidak ada referensi untuk perbandingan."

    # Siapkan data untuk perbandingan
    known_embeddings = []
    known_user_ids = []
    
    for user in users_with_faces:
        try:
            user_embedding = pickle.loads(user.face_encoding)
            known_embeddings.append(user_embedding)
            known_user_ids.append(user.id)
        except:
            continue
    
    if not known_embeddings:
        return None, "Tidak ada data encoding valid di database."
    
    # Reshape untuk cosine similarity
    unknown_embedding = unknown_embedding.reshape(1, -1)
    known_embeddings = np.array(known_embeddings)
    
    # Hitung cosine similarity
    similarities = cosine_similarity(unknown_embedding, known_embeddings)[0]
    
    # Threshold untuk kecocokan (adjust sesuai kebutuhan)
    threshold = 0.85
    
    # Cari similarity tertinggi
    max_similarity_idx = np.argmax(similarities)
    max_similarity = similarities[max_similarity_idx]
    
    if max_similarity >= threshold:
        matched_user_id = known_user_ids[max_similarity_idx]
        return matched_user_id, f"Wajah dikenali dengan confidence: {max_similarity:.2f}"
    
    return None, f"Wajah tidak dikenali. Max similarity: {max_similarity:.2f}"
