import os
import torch

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from model import load_model
from inference import load_face_net, predict_from_bytes
from utils import download_model


# ================= CONFIG =================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODEL_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODEL_DIR, "best_model_v3.pth")

# ✅ YOUR DRIVE MODEL (CORRECT FORMAT)
MODEL_URL = "https://drive.google.com/uc?id=1xigFpgBhZrlwRn4FWX8LZaf7_Rq5E7G3"

DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ================= LOAD =================
print("\n🚀 Starting Image Deepfake Service...\n")

# Download model if missing
download_model(MODEL_PATH, MODEL_URL)

# Load model
print("🔄 Loading EfficientNet model...")
model, threshold = load_model(MODEL_PATH, DEVICE)

# Load face detector
print("🔄 Loading face detector...")
face_net = load_face_net(DETECTOR_DIR)

print("✅ Service Ready!\n")


# ================= FASTAPI =================
app = FastAPI(title="Deepfake Image Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ================= ROUTES =================
@app.get("/")
def root():
    return {
        "service": "Image Deepfake Detection",
        "model": "EfficientNet-B4",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": str(DEVICE)
    }


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        result = predict_from_bytes(
            image_bytes=contents,
            model=model,
            face_net=face_net,
            device=DEVICE,
            threshold=threshold
        )

        return {
            "filename": file.filename,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
