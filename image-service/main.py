import os
import torch
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from model import load_model
from inference import load_face_net, predict_from_bytes

# ---------------- CONFIG ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MODEL_PATH = os.path.join(BASE_DIR, "models", "best_model_v3.pth")
DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------- LOAD ----------------
print("🚀 Loading EfficientNet model...")

model, threshold = load_model(MODEL_PATH, DEVICE)
face_net = load_face_net(DETECTOR_DIR)

print("✅ Model ready!")

# ---------------- APP ----------------
app = FastAPI(title="Deepfake Image Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- ROUTES ----------------
@app.get("/")
def root():
    return {"status": "running", "model": "EfficientNet-B4"}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()

        result = predict_from_bytes(
            contents,
            model,
            face_net,
            DEVICE,
            threshold
        )

        return result

    except Exception as e:
        raise HTTPException(500, str(e))
