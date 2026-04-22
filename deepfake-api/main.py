"""
Render-ready FastAPI with lazy loading
Supports:
- Image → EfficientNet
- Video/Live → TensorFlow
"""

import os
import cv2
import torch
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Local imports
from model import load_model, DEFAULT_MODEL_CONFIG
from inference import load_face_net, predict_from_bytes

# ================= PATHS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EFF_MODEL_PATH = os.path.join(BASE_DIR, "models", "best_model_v3.pth")
TF_MODEL_PATH = os.path.join(BASE_DIR, "models", "deepfake_model.h5")
DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ================= GLOBALS (LAZY LOAD) =================
eff_model = None
face_net = None
threshold = None
tf_model = None


# ================= LAZY LOADERS =================
def get_eff_model():
    global eff_model, face_net, threshold

    if eff_model is None:
        print("🔄 Loading EfficientNet...")
        eff_model, threshold = load_model(EFF_MODEL_PATH, DEVICE)
        face_net = load_face_net(DETECTOR_DIR)
        print("✅ EfficientNet loaded")

    return eff_model, face_net, threshold


def get_tf_model():
    global tf_model

    if tf_model is None:
        print("🔄 Loading TensorFlow model...")
        from tensorflow.keras.models import load_model
        tf_model = load_model(TF_MODEL_PATH, compile=False)
        print("✅ TensorFlow model loaded")

    return tf_model


# ================= FASTAPI =================
app = FastAPI(title="Deepfake Detection API (Render Ready)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= ROUTES =================
@app.get("/")
def home():
    return {
        "message": "Deepfake API running 🚀",
        "endpoints": [
            "/predict/image",
            "/predict/video",
            "/predict/live"
        ]
    }


@app.get("/health")
def health():
    return {"status": "ok"}


# ================= IMAGE =================
@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    try:
        model, face_net, threshold = get_eff_model()

        contents = await file.read()

        result = predict_from_bytes(
            image_bytes=contents,
            model=model,
            face_net=face_net,
            device=DEVICE,
            threshold=threshold,
            use_amp=DEFAULT_MODEL_CONFIG["use_amp"]
        )

        return {"model": "EfficientNet", "result": result}

    except Exception as e:
        raise HTTPException(500, str(e))


# ================= VIDEO =================
@app.post("/predict/video")
async def predict_video(file: UploadFile = File(...)):
    try:
        tf_model = get_tf_model()

        contents = await file.read()

        temp_path = "temp.mp4"
        with open(temp_path, "wb") as f:
            f.write(contents)

        cap = cv2.VideoCapture(temp_path)

        fake = 0
        total = 0

        from tensorflow.keras.preprocessing.image import img_to_array

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            total += 1

            img = cv2.resize(frame, (224, 224))
            img = img_to_array(img) / 255.0
            img = np.expand_dims(img, axis=0)

            pred = tf_model.predict(img, verbose=0)[0][0]

            if pred > 0.5:
                fake += 1

        cap.release()
        os.remove(temp_path)

        if total == 0:
            raise ValueError("Invalid video")

        return {
            "model": "TF Video",
            "fake_percentage": round((fake / total) * 100, 2)
        }

    except Exception as e:
        raise HTTPException(500, str(e))


# ================= LIVE =================
@app.post("/predict/live")
async def predict_live(file: UploadFile = File(...)):
    try:
        tf_model = get_tf_model()

        contents = await file.read()

        np_arr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        from tensorflow.keras.preprocessing.image import img_to_array

        img = cv2.resize(frame, (224, 224))
        img = img_to_array(img) / 255.0
        img = np.expand_dims(img, axis=0)

        pred = tf_model.predict(img, verbose=0)[0][0]

        return {
            "prediction": "FAKE" if pred > 0.5 else "REAL",
            "confidence": float(pred)
        }

    except Exception as e:
        raise HTTPException(500, str(e))
