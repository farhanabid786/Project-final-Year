"""
main.py — Final Stable FastAPI for Dual Model Deployment

✔ EfficientNet (image)
✔ TensorFlow (video + live)
✔ Lazy loading
✔ No startup blocking
✔ Thread-safe execution
"""

import os
import cv2
import torch
import numpy as np
import asyncio
import gdown

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from model import load_model, DEFAULT_MODEL_CONFIG
from inference import load_face_net, predict_from_bytes


# ================= PATHS =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

EFF_MODEL_PATH = os.path.join(MODEL_DIR, "best_model_v3.pth")
TF_MODEL_PATH = os.path.join(MODEL_DIR, "deepfake_model.h5")
DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ================= DRIVE LINKS =================
EFF_URL = "https://drive.google.com/uc?id=1xigFpgBhZrlwRn4FWX8LZaf7_Rq5E7G3"
TF_URL  = "https://drive.google.com/uc?id=1xwuOR6UsC9bEMoMZgk2slrtXMlrLZYcB"


# ================= GLOBAL MODELS =================
eff_model = None
face_net = None
threshold = None
tf_model = None


# ================= DOWNLOAD =================
def ensure_models():
    if not os.path.exists(EFF_MODEL_PATH):
        print("⬇️ Downloading EfficientNet...")
        gdown.download(EFF_URL, EFF_MODEL_PATH, quiet=False)

    if not os.path.exists(TF_MODEL_PATH):
        print("⬇️ Downloading TensorFlow...")
        gdown.download(TF_URL, TF_MODEL_PATH, quiet=False)


# ================= LOADERS =================
def load_eff_model():
    global eff_model, face_net, threshold

    if eff_model is None:
        ensure_models()
        print("🔄 Loading EfficientNet...")
        eff_model, threshold = load_model(EFF_MODEL_PATH, DEVICE)
        face_net = load_face_net(DETECTOR_DIR)
        print("✅ EfficientNet ready")


def load_tf_model():
    global tf_model

    if tf_model is None:
        ensure_models()
        print("🔄 Loading TensorFlow...")
        from tensorflow.keras.models import load_model
        tf_model = load_model(TF_MODEL_PATH, compile=False)
        print("✅ TensorFlow ready")


# ================= THREAD WRAPPER =================
async def run_async(func, *args):
    return await asyncio.to_thread(func, *args)


# ================= FASTAPI =================
app = FastAPI(title="Deepfake Detection API")

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
    return {"message": "API running 🚀"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ================= IMAGE =================
@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    contents = await file.read()

    await run_async(load_eff_model)

    result = await run_async(
        predict_from_bytes,
        contents,
        eff_model,
        face_net,
        DEVICE,
        threshold,
        DEFAULT_MODEL_CONFIG["use_amp"]
    )

    return {
        "model": "EfficientNet",
        "result": result
    }


# ================= VIDEO =================
@app.post("/predict/video")
async def predict_video(file: UploadFile = File(...)):
    contents = await file.read()

    await run_async(load_tf_model)

    temp_path = "temp.mp4"
    with open(temp_path, "wb") as f:
        f.write(contents)

    def process_video():
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
            return {"error": "Invalid video"}

        return round((fake / total) * 100, 2)

    fake_percentage = await run_async(process_video)

    return {
        "model": "TF Video",
        "fake_percentage": fake_percentage
    }


# ================= LIVE =================
@app.post("/predict/live")
async def predict_live(file: UploadFile = File(...)):
    contents = await file.read()

    await run_async(load_tf_model)

    def process_frame():
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

    return await run_async(process_frame)
