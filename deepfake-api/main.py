# """
# main.py — Deepfake Detection REST API (FastAPI)

# Endpoints
# ─────────
# GET  /              → API info & status
# GET  /health        → liveness check
# POST /predict       → multipart image upload → prediction JSON

# Usage
# ─────
#   uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Environment variables (optional overrides)
# ──────────────────────────────────────────
#   CHECKPOINT_PATH   path to best_model_v3.pth
#   DETECTOR_DIR      directory for OpenCV face-detector weights
#   DEVICE            "cuda" | "cpu"  (auto-detected if not set)
# """

# import os
# import gc
# import time
# import logging
# from contextlib import asynccontextmanager

# import torch
# import uvicorn
# from fastapi import FastAPI, File, HTTPException, UploadFile, status
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.responses import JSONResponse
# from pydantic import BaseModel

# from model import load_model, DEFAULT_MODEL_CONFIG
# from inference import load_face_net, predict_from_bytes

# # ── Logging ──────────────────────────────────────────────────────────────────
# logging.basicConfig(
#     level=logging.INFO,
#     format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
# )
# logger = logging.getLogger("deepfake_api")

# # ── Configuration ─────────────────────────────────────────────────────────────
# CHECKPOINT_PATH = os.getenv(
#     "CHECKPOINT_PATH",
#     "D:/deepfake_project/models/checkpoints/best_model_v3.pth",
# )
# DETECTOR_DIR = os.getenv(
#     "DETECTOR_DIR",
#     "D:/deepfake_project/face_detector",
# )

# # Accepted MIME types
# ALLOWED_MIME = {
#     "image/jpeg",
#     "image/jpg",
#     "image/png",
#     "image/bmp",
#     "image/webp",
#     "image/tiff",
# }

# # Max upload size: 20 MB
# MAX_UPLOAD_BYTES = 20 * 1024 * 1024

# # ── Global state (loaded once at startup) ────────────────────────────────────
# _state: dict = {
#     "model"     : None,
#     "face_net"  : None,
#     "device"    : None,
#     "threshold" : 0.46,
#     "ready"     : False,
# }


# # ── Lifespan (replaces deprecated @app.on_event) ─────────────────────────────
# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Load model and face-detector on startup; clean up on shutdown."""
#     # ── Startup ──────────────────────────────────────────────────────────────
#     logger.info("=" * 55)
#     logger.info("Deepfake Detection API — starting up")
#     logger.info("=" * 55)

#     # Device
#     _env_device = os.getenv("DEVICE", "").lower()
#     if _env_device in ("cuda", "cpu"):
#         device = torch.device(_env_device)
#     else:
#         device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     _state["device"] = device
#     logger.info(f"Device        : {device}")

#     if device.type == "cuda":
#         gc.collect()
#         torch.cuda.empty_cache()
#         props = torch.cuda.get_device_properties(0)
#         logger.info(f"GPU           : {props.name}")
#         logger.info(f"VRAM          : {props.total_memory / 1e9:.2f} GB")

#     # Load model
#     if not os.path.exists(CHECKPOINT_PATH):
#         logger.error(f"Checkpoint NOT found: {CHECKPOINT_PATH}")
#         logger.error("Set CHECKPOINT_PATH env var or update main.py")
#         # App starts anyway — /health will report not-ready
#     else:
#         logger.info(f"Loading model : {CHECKPOINT_PATH}")
#         t0 = time.time()
#         model, threshold = load_model(CHECKPOINT_PATH, device)
#         _state["model"]     = model
#         _state["threshold"] = threshold
#         logger.info(
#             f"Model loaded  : {time.time() - t0:.1f}s  "
#             f"(threshold={threshold:.2f})"
#         )

#         # Load face detector (auto-downloads if missing)
#         logger.info(f"Face detector : {DETECTOR_DIR}")
#         _state["face_net"] = load_face_net(DETECTOR_DIR)
#         logger.info("Face detector : ready")

#         _state["ready"] = True
#         logger.info("API is READY")

#     logger.info("=" * 55)
#     yield   # <- app runs here

#     # ── Shutdown ─────────────────────────────────────────────────────────────
#     logger.info("Shutting down ...")
#     _state["model"]    = None
#     _state["face_net"] = None
#     if _state["device"] and _state["device"].type == "cuda":
#         torch.cuda.empty_cache()
#     gc.collect()
#     logger.info("Shutdown complete.")


# # ── App ───────────────────────────────────────────────────────────────────────
# app = FastAPI(
#     title       = "Deepfake Detection API",
#     description = (
#         "EfficientNet-B4 model trained on ~74 k images from 6 datasets. "
#         "Upload a face image and receive a REAL / FAKE prediction with confidence."
#     ),
#     version     = "3.0.0",
#     lifespan    = lifespan,
# )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins     = ["*"],
#     allow_credentials = True,
#     allow_methods     = ["*"],
#     allow_headers     = ["*"],
# )


# # ── Pydantic response models ──────────────────────────────────────────────────
# class PredictionResponse(BaseModel):
#     label        : str    # "FAKE" | "REAL"
#     confidence   : float  # [0-100] — confidence in the predicted label
#     fake_prob    : float  # [0-100]
#     real_prob    : float  # [0-100]
#     face_detected: bool
#     threshold    : float
#     filename     : str
#     processing_ms: float


# class HealthResponse(BaseModel):
#     status    : str
#     ready     : bool
#     device    : str
#     model     : str
#     threshold : float


# # ── Routes ────────────────────────────────────────────────────────────────────
# @app.get("/", tags=["Info"])
# def root():
#     """Return API metadata."""
#     return {
#         "name"       : "Deepfake Detection API",
#         "version"    : "3.0.0",
#         "model"      : DEFAULT_MODEL_CONFIG["model_name"],
#         "image_size" : DEFAULT_MODEL_CONFIG["image_size"],
#         "endpoints"  : {
#             "health" : "GET  /health",
#             "predict": "POST /predict  (multipart/form-data, field=file)",
#             "docs"   : "GET  /docs",
#         },
#     }


# @app.get("/health", response_model=HealthResponse, tags=["Info"])
# def health():
#     """Liveness / readiness check."""
#     device = _state["device"]
#     return HealthResponse(
#         status    = "ok" if _state["ready"] else "not_ready",
#         ready     = _state["ready"],
#         device    = str(device) if device else "unknown",
#         model     = DEFAULT_MODEL_CONFIG["model_name"],
#         threshold = _state["threshold"],
#     )


# @app.post(
#     "/predict",
#     response_model = PredictionResponse,
#     status_code    = status.HTTP_200_OK,
#     tags           = ["Prediction"],
#     summary        = "Predict REAL or FAKE for an uploaded image",
#     description    = (
#         "Upload a face image (JPG, PNG, BMP, WEBP, TIFF). "
#         "The API detects the face, crops it, and runs the EfficientNet-B4 classifier. "
#         "Returns label, confidence, and probabilities."
#     ),
# )
# async def predict(file: UploadFile = File(..., description="Face image to analyse")):
#     # Guard: model must be loaded
#     if not _state["ready"]:
#         raise HTTPException(
#             status_code = status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail      = "Model not loaded. Check CHECKPOINT_PATH and restart.",
#         )

#     # Guard: MIME type (browsers sometimes send 'image/jpg' — handle both)
#     content_type = (file.content_type or "").lower()
#     if content_type and content_type not in ALLOWED_MIME:
#         raise HTTPException(
#             status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
#             detail      = (
#                 f"Unsupported content type '{content_type}'. "
#                 f"Accepted: {', '.join(sorted(ALLOWED_MIME))}"
#             ),
#         )

#     # Read bytes
#     image_bytes = await file.read()
#     if len(image_bytes) == 0:
#         raise HTTPException(
#             status_code = status.HTTP_400_BAD_REQUEST,
#             detail      = "Uploaded file is empty.",
#         )
#     if len(image_bytes) > MAX_UPLOAD_BYTES:
#         raise HTTPException(
#             status_code = status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
#             detail      = (
#                 f"File too large ({len(image_bytes) // 1024} KB). Max 20 MB."
#             ),
#         )

#     # Inference
#     t0 = time.perf_counter()
#     try:
#         result = predict_from_bytes(
#             image_bytes = image_bytes,
#             model       = _state["model"],
#             face_net    = _state["face_net"],
#             device      = _state["device"],
#             threshold   = _state["threshold"],
#             use_amp     = DEFAULT_MODEL_CONFIG["use_amp"],
#         )
#     except ValueError as exc:
#         raise HTTPException(
#             status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
#             detail      = str(exc),
#         )
#     except Exception as exc:
#         logger.exception("Inference error")
#         raise HTTPException(
#             status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail      = f"Inference failed: {exc}",
#         )

#     elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)

#     logger.info(
#         f"[{file.filename}] -> {result['label']} "
#         f"({result['confidence']:.1f}%)  {elapsed_ms} ms  "
#         f"face={'YES' if result['face_detected'] else 'NO'}"
#     )

#     return PredictionResponse(
#         **result,
#         filename      = file.filename or "unknown",
#         processing_ms = elapsed_ms,
#     )


# # ── Dev server entry-point ────────────────────────────────────────────────────
# if __name__ == "__main__":
#     uvicorn.run(
#         "main:app",
#         host    = "0.0.0.0",
#         port    = 8000,
#         reload  = False,   # set True only during development
#         workers = 1,       # keep 1 — PyTorch model is not fork-safe
#     )

"""
main.py — Deepfake Detection API

This API uses:
- EfficientNet-B4 (PyTorch) → Image prediction (accurate)
- TensorFlow model → Video + Live prediction

Designed for:
✔ Clean structure
✔ Easy debugging
✔ VS Code friendly
"""

import os
import cv2
import torch
import numpy as np

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# EfficientNet (your trained model)
from model import load_model, DEFAULT_MODEL_CONFIG
from inference import load_face_net, predict_from_bytes

# TensorFlow model
from tensorflow.keras.models import load_model as tf_load_model
from tensorflow.keras.preprocessing.image import img_to_array


#  PATH CONFIG 
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

EFF_MODEL_PATH = os.path.join(BASE_DIR, "models", "best_model_v3.pth")
TF_MODEL_PATH = os.path.join(BASE_DIR, "models", "deepfake_model.h5")
DETECTOR_DIR = os.path.join(BASE_DIR, "face_detector")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


#  LOAD MODELS 
print("\n🔄 Initializing Deepfake Detection System...\n")

if not os.path.exists(EFF_MODEL_PATH):
    raise FileNotFoundError(f"EfficientNet model not found at: {EFF_MODEL_PATH}")

if not os.path.exists(TF_MODEL_PATH):
    raise FileNotFoundError(f"TensorFlow model not found at: {TF_MODEL_PATH}")

# Load EfficientNet
print("Loading EfficientNet-B4...")
eff_model, threshold = load_model(EFF_MODEL_PATH, DEVICE)

# Load face detector
print("Loading face detector...")
face_net = load_face_net(DETECTOR_DIR)

# Load TensorFlow model
print("Loading TensorFlow model...")
tf_model = tf_load_model(TF_MODEL_PATH)

print("\n✅ All models loaded successfully!\n")


#  FASTAPI APP 
app = FastAPI(title="Deepfake Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#  BASIC ROUTES 
@app.get("/")
def home():
    return {
        "message": "Deepfake Detection API is running 🚀",
        "endpoints": [
            "/predict/image",
            "/predict/video",
            "/predict/live"
        ]
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": str(DEVICE)
    }


#  IMAGE PREDICTION 
@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...)):
    """
    Uses EfficientNet-B4 (BEST accuracy)
    """
    try:
        contents = await file.read()

        result = predict_from_bytes(
            image_bytes=contents,
            model=eff_model,
            face_net=face_net,
            device=DEVICE,
            threshold=threshold,
            use_amp=DEFAULT_MODEL_CONFIG["use_amp"]
        )

        return {
            "model": "EfficientNet-B4",
            "filename": file.filename,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image prediction error: {str(e)}")


#  VIDEO PREDICTION 
@app.post("/predict/video")
async def predict_video(file: UploadFile = File(...)):
    """
    Uses TensorFlow model (frame-by-frame)
    """
    try:
        contents = await file.read()

        temp_path = "temp_video.mp4"
        with open(temp_path, "wb") as f:
            f.write(contents)

        cap = cv2.VideoCapture(temp_path)

        total_frames = 0
        fake_frames = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1

            img = cv2.resize(frame, (224, 224))
            img = img_to_array(img) / 255.0
            img = np.expand_dims(img, axis=0)

            prediction = tf_model.predict(img, verbose=0)[0][0]

            if prediction > 0.5:
                fake_frames += 1

        cap.release()
        os.remove(temp_path)

        if total_frames == 0:
            raise ValueError("No frames detected in video")

        fake_percentage = (fake_frames / total_frames) * 100

        return {
            "model": "TensorFlow Video Model",
            "frames_processed": total_frames,
            "fake_percentage": round(fake_percentage, 2)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video prediction error: {str(e)}")


#  LIVE FRAME PREDICTION 
@app.post("/predict/live")
async def predict_live(file: UploadFile = File(...)):
    """
    Used for real-time webcam frames
    """
    try:
        contents = await file.read()

        np_array = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Invalid image frame")

        img = cv2.resize(frame, (224, 224))
        img = img_to_array(img) / 255.0
        img = np.expand_dims(img, axis=0)

        prediction = tf_model.predict(img, verbose=0)[0][0]

        label = "FAKE" if prediction > 0.5 else "REAL"

        return {
            "model": "TensorFlow Live Model",
            "prediction": label,
            "confidence": round(float(prediction), 4)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Live prediction error: {str(e)}")
