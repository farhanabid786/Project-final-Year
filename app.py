# =============================================================================
#  DeepFake Detection API
#  Architecture : EfficientNetB4 + BiLSTM + Temporal Attention
#  Framework    : FastAPI
#  Inference    : PyTorch (.pth checkpoint)
#  Endpoints    : Image | Video | Live (browser webcam)
# =============================================================================

import asyncio
import base64
import gc
import logging
import os
import random
import sys
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from torchvision.models import EfficientNet_B4_Weights, efficientnet_b4


#  LOGGING

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("deepfake_api")


#  CONFIGURATION


MODEL_PATH       = os.getenv("MODEL_PATH", "checkpoints/best_model.pth")
THRESHOLD        = float(os.getenv("THRESHOLD", "0.5"))
MAX_VIDEO_FRAMES = int(os.getenv("MAX_VIDEO_FRAMES", "120"))
PORT             = int(os.getenv("PORT", "8000"))

IMG_SIZE      = 380        
N_FRAMES      = 15         
LSTM_HIDDEN   = 256       
LSTM_LAYERS   = 2       
ATTENTION_DIM = 128     
DROPOUT       = 0.5       

# ImageNet normalization 
IMAGENET_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
IMAGENET_STD  = np.array([0.229, 0.224, 0.225], dtype=np.float32)

# Auto-detect GPU, fall back to CPU
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}
ALLOWED_VIDEO_TYPES = {
    "video/mp4", "video/avi", "video/quicktime",
    "video/x-matroska", "video/webm", "video/x-msvideo",
}

#  MODEL ARCHITECTURE

class TemporalAttention(nn.Module):
    """Soft attention over BiLSTM hidden states to weight each frame."""

    def __init__(self, hidden_dim: int, attention_dim: int):
        super().__init__()
        self.attn = nn.Sequential(
            nn.Linear(hidden_dim * 2, attention_dim),
            nn.Tanh(),
            nn.Linear(attention_dim, 1, bias=False),
        )

    def forward(self, lstm_out: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        scores  = self.attn(lstm_out).squeeze(-1)           # (B, T)
        weights = F.softmax(scores, dim=1).unsqueeze(-1)    # (B, T, 1)
        context = (lstm_out * weights).sum(dim=1)           # (B, hidden*2)
        return context, weights.squeeze(-1)


class DeepfakeDetector(nn.Module):
    """
    EfficientNetB4 extracts per-frame features.
    Frame projector reduces to 512-dim.
    Bidirectional LSTM models temporal relationships.
    Temporal attention weights each frame.
    Classifier outputs fake probability (sigmoid applied at inference).
    """

    def __init__(self):
        super().__init__()
        backbone        = efficientnet_b4(weights=None)   # Weights loaded from checkpoint
        self.cnn        = backbone.features
        self.pool       = nn.AdaptiveAvgPool2d(1)
        cnn_out         = 1792

        self.cnn_drop   = nn.Dropout(0.2)
        self.frame_proj = nn.Sequential(
            nn.Linear(cnn_out, 512),
            nn.LayerNorm(512),
            nn.SiLU(),
            nn.Dropout(0.3),
        )
        self.bilstm = nn.LSTM(
            input_size=512,
            hidden_size=LSTM_HIDDEN,
            num_layers=LSTM_LAYERS,
            batch_first=True,
            bidirectional=True,
            dropout=DROPOUT if LSTM_LAYERS > 1 else 0.0,
        )
        self.attention  = TemporalAttention(LSTM_HIDDEN, ATTENTION_DIM)
        self.classifier = nn.Sequential(
            nn.Linear(LSTM_HIDDEN * 2, 128),
            nn.LayerNorm(128),
            nn.SiLU(),
            nn.Dropout(DROPOUT),
            nn.Linear(128, 1),
        )
        self._init_weights()

    def _init_weights(self):
        for name, p in self.bilstm.named_parameters():
            if "weight_ih" in name:   nn.init.xavier_uniform_(p)
            elif "weight_hh" in name: nn.init.orthogonal_(p)
            elif "bias" in name:      nn.init.zeros_(p)
        for m in [*self.frame_proj, *self.classifier]:
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        B, T, C, H, W = x.shape
        x_flat = x.contiguous().view(B * T, C, H, W)

        # In eval mode: no gradient needed through CNN
        with torch.no_grad():
            feats = self.cnn(x_flat)

        feats       = self.pool(feats).view(B * T, -1)   # (B*T, 1792)
        feats       = self.cnn_drop(feats)
        feats       = feats.view(B, T, -1)               # (B, T, 1792)
        feats       = self.frame_proj(feats)             # (B, T, 512)
        lstm_out, _ = self.bilstm(feats)                 # (B, T, 512)
        context, attn_weights = self.attention(lstm_out) # (B, 512), (B, T)
        logit       = self.classifier(context).squeeze(-1)
        return logit, attn_weights


#  MODEL LOADING

_model: Optional[DeepfakeDetector] = None
_model_meta: Dict[str, Any]        = {}


def load_model() -> None:
    """Load model weights from checkpoint at startup. Crashes fast if file is invalid."""
    global _model, _model_meta

    model     = DeepfakeDetector().to(DEVICE)
    ckpt_path = Path(MODEL_PATH)

    if not ckpt_path.exists():
        logger.warning(f"Checkpoint not found at '{MODEL_PATH}'. Running with random weights.")
        _model_meta = {"warning": "No checkpoint found — random weights"}
        model.eval()
        _model = model
        return

    logger.info(f"Loading checkpoint: {MODEL_PATH}")
    ckpt  = torch.load(str(ckpt_path), map_location=DEVICE, weights_only=False)

    # Training loop saves with key 'model_state' (confirmed in notebook cell 9)
    state = ckpt.get("model_state")
    if state is None:
        raise RuntimeError(
            f"Key 'model_state' not found in checkpoint. "
            f"Found keys: {list(ckpt.keys())}"
        )

    model.load_state_dict(state, strict=True)
    model.eval()
    _model = model

    _model_meta = {
        "file":      ckpt_path.name,
        "epoch":     ckpt.get("epoch",     "N/A"),
        "val_auc":   ckpt.get("val_auc",   "N/A"),
        "val_acc":   ckpt.get("val_acc",   "N/A"),
        "train_auc": ckpt.get("train_auc", "N/A"),
        "train_acc": ckpt.get("train_acc", "N/A"),
    }
    logger.info(
        f"Model loaded | epoch={_model_meta['epoch']} | "
        f"val_auc={_model_meta['val_auc']} | val_acc={_model_meta['val_acc']}"
    )


def get_model() -> DeepfakeDetector:
    if _model is None:
        raise HTTPException(status_code=503, detail="Model not loaded.")
    return _model

#  PREPROCESSING HELPERS

def preprocess_frame(img_rgb: np.ndarray) -> torch.Tensor:
    """
    HWC uint8 RGB → CHW float32 tensor, resized to 380×380, ImageNet normalized.
    This exactly mirrors the training pipeline in deepfake_fixed_v3.ipynb.
    """
    img = cv2.resize(img_rgb, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_LANCZOS4)
    img = img.astype(np.float32) / 255.0
    img = (img - IMAGENET_MEAN) / IMAGENET_STD
    return torch.from_numpy(img).permute(2, 0, 1)   # CHW


def bytes_to_rgb(data: bytes) -> np.ndarray:
    """Decode raw file bytes → HWC uint8 RGB array."""
    arr = np.frombuffer(data, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        raise ValueError("OpenCV could not decode the image.")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def image_to_sequence(frame: np.ndarray) -> List[np.ndarray]:
    """
    Expand a single image into N_FRAMES by applying subtle random spatial jitter.
    This gives the BiLSTM a valid temporal sequence — same strategy used in inference
    throughout the project's chat history.
    """
    h, w   = frame.shape[:2]
    frames = []
    for _ in range(N_FRAMES):
        f    = frame.copy()
        frac = random.uniform(0.93, 1.0)
        ch, cw = int(h * frac), int(w * frac)
        y0   = random.randint(0, max(0, h - ch))
        x0   = random.randint(0, max(0, w - cw))
        f    = f[y0:y0 + ch, x0:x0 + cw]
        f    = cv2.resize(f, (w, h), interpolation=cv2.INTER_LINEAR)
        frames.append(f)
    return frames


def sample_video_frames(video_path: str, n_frames: int) -> List[np.ndarray]:
    """
    Evenly sample n_frames from a video file using OpenCV.
    Handles corrupted/unreadable frames by repeating the last good frame.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_frames = min(total_frames, MAX_VIDEO_FRAMES)
    indices      = np.linspace(0, max(total_frames - 1, 0), n_frames, dtype=int).tolist()
    frames       = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, bgr = cap.read()
        if ret and bgr is not None:
            frames.append(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        else:
            # Corrupted frame — pad with last good frame or blank
            frames.append(
                frames[-1].copy() if frames
                else np.zeros((IMG_SIZE, IMG_SIZE, 3), dtype=np.uint8)
            )

    cap.release()

    # Safety: pad to exactly n_frames if video was shorter than expected
    while len(frames) < n_frames:
        frames.append(frames[-1].copy())

    return frames[:n_frames]


def frames_to_tensor(frames: List[np.ndarray]) -> torch.Tensor:
    """Stack a list of RGB frames into model input tensor: (1, T, C, 380, 380)."""
    tensors = [preprocess_frame(f) for f in frames]
    return torch.stack(tensors).unsqueeze(0).to(DEVICE)   # (1, N_FRAMES, 3, 380, 380)


def frame_to_b64_preview(frame_rgb: np.ndarray, size: int = 224) -> str:
    """
    Encode a frame as a base64 JPEG string for frontend display.
    Size 224px — small enough for fast transmission, large enough to see detail.
    NOTE: Inference always uses 380×380 via preprocess_frame(). This is preview only.
    """
    thumb      = cv2.resize(frame_rgb, (size, size))
    bgr        = cv2.cvtColor(thumb, cv2.COLOR_RGB2BGR)
    ok, buf    = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 75])
    return base64.b64encode(buf.tobytes()).decode("utf-8") if ok else ""


def safe_b64_decode(b64_string: str) -> bytes:
    """
    Safely decode a base64 string.
    Strips data-URL prefix (data:image/jpeg;base64,...) if present.
    """
    if "," in b64_string:
        b64_string = b64_string.split(",", 1)[1]

    b64_string = b64_string.strip().replace("\n", "").replace("\r", "")
    padding    = 4 - (len(b64_string) % 4)
    if padding != 4:
        b64_string += "=" * padding

    return base64.b64decode(b64_string, validate=True)


#  INFERENCE ENGINE

@torch.no_grad()
def run_inference(tensor: torch.Tensor) -> Tuple[float, float, List[float]]:
    """
    Run model forward pass on a (1, T, 3, 380, 380) tensor.
    Uses mixed precision (AMP) on GPU for speed.
    Returns: (prob_fake, prob_real, attention_weights_per_frame)
    """
    model   = get_model()
    use_amp = DEVICE.type == "cuda"

    with torch.amp.autocast(device_type=DEVICE.type, enabled=use_amp):
        logit, attn = model(tensor)

    prob_fake = float(torch.sigmoid(logit).cpu().item())
    prob_real = 1.0 - prob_fake
    weights   = attn.squeeze(0).cpu().tolist()
    return prob_fake, prob_real, weights


#  RESPONSE BUILDER
#  All endpoints return the same structure — clean, frontend-friendly JSON.

def build_response(
    prob_fake:  float,
    prob_real:  float,
    attn:       List[float],
    elapsed_ms: float,
    threshold:  float,
    extra:      Optional[Dict] = None,
) -> Dict[str, Any]:

    label    = "FAKE" if prob_fake >= threshold else "REAL"
    conf_raw = prob_fake if label == "FAKE" else prob_real

    result: Dict[str, Any] = {
        "label":              label,
        "confidence_pct":     round(conf_raw * 100, 2),
        "confidence_display": f"{round(conf_raw * 100, 2)}%",
        "probabilities": {
            "fake_pct": round(prob_fake * 100, 2),
            "real_pct": round(prob_real * 100, 2),
            "fake_raw": round(prob_fake, 6),
            "real_raw": round(prob_real, 6),
        },
        "threshold":         threshold,
        "attention_weights": [round(w, 6) for w in attn],
        "inference_time_ms": round(elapsed_ms, 2),
        "device":            str(DEVICE),
    }

    if extra:
        result.update(extra)

    return result

#  FACE DETECTION HELPER (for live endpoint bounding box)

# Load OpenCV Haar cascade — ships with opencv-python, no extra download needed
_HAAR_PATH   = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
FACE_CASCADE = cv2.CascadeClassifier(_HAAR_PATH)


def detect_faces(img_rgb: np.ndarray) -> List[Dict[str, int]]:
    """
    Detect faces using Haar cascade.
    Returns list of {x, y, w, h} dicts — directly usable by frontend canvas.
    """
    gray  = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    faces = FACE_CASCADE.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
    )
    if len(faces) == 0:
        return []
    return [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for x, y, w, h in faces]


#  APP LIFESPAN — load model at startup, clean up at shutdown


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 55)
    logger.info("  DeepFake Detection API — Starting")
    logger.info(f"  Device  : {DEVICE}")
    if DEVICE.type == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1e9
        logger.info(f"  GPU     : {gpu_name} ({vram_gb:.1f} GB VRAM)")
    else:
        logger.info("  GPU     : Not available — running on CPU")
    logger.info(f"  Model   : {MODEL_PATH}")
    logger.info("=" * 55)

    load_model()
    logger.info("  Model ready ✓")

    yield   # Server runs here

    logger.info("DeepFake Detection API — Shutting down")
    gc.collect()
    if DEVICE.type == "cuda":
        torch.cuda.empty_cache()

#  FASTAPI APP


app = FastAPI(
    title       = "DeepFake Detection API",
    description = "EfficientNetB4 + BiLSTM + Temporal Attention | Image | Video | Live",
    version     = "3.0.0",
    lifespan    = lifespan,
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

#  SYSTEM ENDPOINTS

@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({
        "api":    "DeepFake Detection API v3.0",
        "docs":   "/docs",
        "health": "/api/v1/health",
    })


@app.get("/api/v1/health", tags=["System"])
async def health():
    """Server health check — confirms model is loaded and device info."""
    return {
        "status":         "ok",
        "device":         str(DEVICE),
        "cuda_available": torch.cuda.is_available(),
        "gpu_name":       torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "model_loaded":   _model is not None,
        "model_meta":     _model_meta,
        "torch_version":  torch.__version__,
        "python_version": sys.version,
    }


@app.get("/api/v1/model/info", tags=["System"])
async def model_info():
    """Model architecture details and parameter counts."""
    model = get_model()
    return {
        "architecture":     "EfficientNetB4 + BiLSTM + Temporal Attention",
        "input_size":       f"{IMG_SIZE}x{IMG_SIZE}",
        "n_frames":         N_FRAMES,
        "lstm_hidden":      LSTM_HIDDEN,
        "lstm_layers":      LSTM_LAYERS,
        "attention_dim":    ATTENTION_DIM,
        "classification":   {"0": "REAL", "1": "FAKE"},
        "threshold":        THRESHOLD,
        "total_params":     sum(p.numel() for p in model.parameters()),
        "trainable_params": sum(p.numel() for p in model.parameters() if p.requires_grad),
        "device":           str(DEVICE),
        "checkpoint":       _model_meta,
    }

#  ENDPOINT 1 — IMAGE DEEPFAKE DETECTION
#  POST /api/v1/detect/image


@app.post("/api/v1/detect/image", tags=["Detection"])
async def detect_image(
    file:      UploadFile      = File(..., description="JPEG / PNG / WEBP image"),
    threshold: Optional[float] = Form(None, description="Decision threshold 0–1. Default: 0.5"),
):
    """
    Upload a single face image. Returns REAL/FAKE label with confidence %.

    The image is expanded into a 15-frame temporal sequence with subtle
    spatial jitter so the BiLSTM receives a valid sequence to process.

    Supported formats: jpg, jpeg, png, webp
    Max file size: 20 MB
    """
    # Validate file type
    if file.content_type and file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported image type: '{file.content_type}'. Allowed: jpg, jpeg, png, webp"
        )

    thr  = threshold if (threshold is not None and 0.0 < threshold < 1.0) else THRESHOLD
    data = await file.read()

    if len(data) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image exceeds 20 MB limit.")

    try:
        img_rgb = bytes_to_rgb(data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot decode image: {e}")

    h, w = img_rgb.shape[:2]

    t0      = time.perf_counter()
    frames  = image_to_sequence(img_rgb)     # Single image → 15-frame sequence
    tensor  = frames_to_tensor(frames)        # (1, 15, 3, 380, 380)
    prob_fake, prob_real, attn = run_inference(tensor)
    elapsed = (time.perf_counter() - t0) * 1000

    # Cleanup GPU memory
    gc.collect()
    if DEVICE.type == "cuda":
        torch.cuda.empty_cache()

    return build_response(prob_fake, prob_real, attn, elapsed, thr, extra={
        "image_meta": {
            "filename":     file.filename,
            "content_type": file.content_type,
            "width":        w,
            "height":       h,
            "size_bytes":   len(data),
        },
    })


#  ENDPOINT 2 — VIDEO DEEPFAKE DETECTION
#  POST /api/v1/detect/video


@app.post("/api/v1/detect/video", tags=["Detection"])
async def detect_video(
    file:      UploadFile      = File(..., description="MP4 / AVI / MOV / MKV / WEBM video"),
    n_frames:  Optional[int]   = Form(None, description=f"Frames to sample (1–{N_FRAMES}). Default: {N_FRAMES}"),
    threshold: Optional[float] = Form(None, description="Decision threshold 0–1. Default: 0.5"),
):
    """
    Upload a video file. Evenly samples up to 15 frames, runs temporal inference,
    and returns REAL/FAKE result with confidence %.

    Also returns 224×224 base64 JPEG previews of the sampled frames so the
    frontend can display which frames were analysed.

    Note: Inference runs on 380×380 tensors. The 224×224 previews are display-only.

    Supported formats: mp4, avi, mov, mkv, webm
    Max file size: 500 MB
    """
    if file.content_type and file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported video type: '{file.content_type}'. Allowed: mp4, avi, mov, mkv, webm"
        )

    thr         = threshold if (threshold is not None and 0.0 < threshold < 1.0) else THRESHOLD
    used_frames = n_frames if (n_frames and 1 <= n_frames <= N_FRAMES) else N_FRAMES
    data        = await file.read()

    if len(data) > 500 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Video exceeds 500 MB limit.")

    # Write to temp file — OpenCV needs a file path, not bytes
    suffix = Path(file.filename or "upload.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(data)
        tmp_path = tmp.name

    try:
        # Read video metadata before processing frames
        cap    = cv2.VideoCapture(tmp_path)
        fps    = cap.get(cv2.CAP_PROP_FPS) or 0
        total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        dur    = round(total / fps, 2) if fps > 0 else 0
        cap.release()

        t0      = time.perf_counter()
        frames  = sample_video_frames(tmp_path, used_frames)   # HWC uint8 RGB
        tensor  = frames_to_tensor(frames)                      # (1, T, 3, 380, 380) ← correct
        prob_fake, prob_real, attn = run_inference(tensor)
        elapsed = (time.perf_counter() - t0) * 1000

        # 224×224 previews for frontend rendering — NOT used in inference
        previews = [frame_to_b64_preview(f, size=224) for f in frames]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video processing error: {e}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
        gc.collect()
        if DEVICE.type == "cuda":
            torch.cuda.empty_cache()

    return build_response(prob_fake, prob_real, attn, elapsed, thr, extra={
        "frames_sampled":  used_frames,
        "frame_previews":  previews,       # List of base64 JPEG strings (224×224)
        "video_meta": {
            "filename":         file.filename,
            "width":            width,
            "height":           height,
            "fps":              round(fps, 2),
            "total_frames":     total,
            "duration_seconds": dur,
            "size_bytes":       len(data),
        },
    })

#  ENDPOINT 3a — LIVE DETECTION
#  POST /api/v1/detect/live

class LiveFrameRequest(BaseModel):
    frame_b64:  str           = Field(..., description="Base64 JPEG/PNG frame from browser webcam. Accepts plain base64 or data:image/... prefix.")
    session_id: Optional[str] = Field(None, description="Optional session ID for tracking.")


@app.post("/api/v1/detect/live", tags=["Live Detection"])
async def detect_live(payload: LiveFrameRequest):
    """
    Receive one webcam frame from the browser and return a deepfake prediction.

    Browser flow (implemented in GET /api/v1/live test page):
      getUserMedia() → canvas.toDataURL('image/jpeg') → POST here → display result

    Also returns face bounding box coordinates so the frontend can draw a
    GREEN (REAL) or RED (FAKE) box around the detected face.

    Call this every 800–1000 ms for smooth real-time detection.
    """
    try:
        raw = safe_b64_decode(payload.frame_b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 frame: {e}")

    if len(raw) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Frame exceeds 10 MB.")

    try:
        img_rgb = bytes_to_rgb(raw)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot decode frame image: {e}")

    # Detect faces — returns [{x, y, w, h}, ...] for frontend canvas overlay
    face_boxes = detect_faces(img_rgb)

    t0      = time.perf_counter()
    frames  = image_to_sequence(img_rgb)
    tensor  = frames_to_tensor(frames)
    prob_fake, prob_real, attn = run_inference(tensor)
    elapsed = (time.perf_counter() - t0) * 1000

    return build_response(prob_fake, prob_real, attn, elapsed, THRESHOLD, extra={
        "session_id": payload.session_id,
        "face_boxes": face_boxes,    # Frontend draws GREEN/RED box based on label
        "frame_meta": {
            "width":      img_rgb.shape[1],
            "height":     img_rgb.shape[0],
            "size_bytes": len(raw),
        },
    })

#  ENDPOINT 3b — LIVE TEST PAGE
#  GET /api/v1/live

@app.get("/api/v1/live", tags=["Live Detection"], response_class=HTMLResponse)
async def live_test_page():
    """
    Browser-based live deepfake detection test page.
    Open this URL in Chrome/Firefox to test the full live detection pipeline
    before wiring up the Node.js frontend.
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DeepFake Live Detection</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #0d0d0d;
      color: #f0f0f0;
      font-family: 'Segoe UI', sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 16px;
      min-height: 100vh;
    }
    h1 { font-size: 1.6rem; margin-bottom: 6px; letter-spacing: 1px; }
    p.sub { color: #888; font-size: 0.85rem; margin-bottom: 24px; }

    .camera-container {
      position: relative;
      width: 640px;
      max-width: 100%;
      border-radius: 10px;
      overflow: hidden;
      border: 2px solid #333;
    }
    video, canvas {
      display: block;
      width: 100%;
      border-radius: 8px;
    }
    canvas {
      position: absolute;
      top: 0; left: 0;
      pointer-events: none;
    }

    .result-card {
      margin-top: 20px;
      width: 640px;
      max-width: 100%;
      background: #1a1a1a;
      border-radius: 10px;
      padding: 20px 24px;
      border: 1px solid #2a2a2a;
    }
    .label-row {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 10px;
    }
    .label {
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: 2px;
    }
    .FAKE { color: #ff4444; }
    .REAL { color: #44dd88; }
    .confidence {
      font-size: 1.4rem;
      color: #ccc;
    }
    .prob-row {
      display: flex;
      gap: 12px;
      font-size: 0.85rem;
      color: #888;
      margin-top: 6px;
    }
    .meta { font-size: 0.78rem; color: #555; margin-top: 10px; }

    .controls {
      margin-top: 20px;
      display: flex;
      gap: 12px;
    }
    button {
      padding: 10px 28px;
      border-radius: 6px;
      border: none;
      font-size: 1rem;
      cursor: pointer;
      font-weight: 600;
    }
    #startBtn { background: #22c55e; color: #000; }
    #stopBtn  { background: #ef4444; color: #fff; display: none; }
    .status { margin-top: 12px; font-size: 0.82rem; color: #666; }
  </style>
</head>
<body>

  <h1>🔍 DeepFake Live Detection</h1>
  <p class="sub">Browser webcam → FastAPI → REAL / FAKE result in real time</p>

  <div class="camera-container">
    <video id="video" autoplay playsinline muted></video>
    <canvas id="overlay"></canvas>
  </div>

  <div class="result-card">
    <div class="label-row">
      <span class="label" id="label">—</span>
      <span class="confidence" id="confidence"></span>
    </div>
    <div class="prob-row">
      <span id="fakePct"></span>
      <span id="realPct"></span>
      <span id="inferMs"></span>
    </div>
    <div class="meta" id="meta"></div>
  </div>

  <div class="controls">
    <button id="startBtn" onclick="startDetection()">▶ Start Detection</button>
    <button id="stopBtn"  onclick="stopDetection()">■ Stop</button>
  </div>
  <p class="status" id="status">Click Start Detection to begin.</p>

  <script>
    const video    = document.getElementById('video');
    const overlay  = document.getElementById('overlay');
    const ctx      = overlay.getContext('2d');
    let   stream   = null;
    let   interval = null;
    let   sending  = false;

    async function startDetection() {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        video.srcObject = stream;
        await new Promise(r => video.onloadedmetadata = r);
        overlay.width  = video.videoWidth;
        overlay.height = video.videoHeight;

        document.getElementById('startBtn').style.display = 'none';
        document.getElementById('stopBtn').style.display  = 'inline-block';
        document.getElementById('status').textContent     = 'Detection running…';

        // Send a frame every 800ms
        interval = setInterval(sendFrame, 800);
      } catch (err) {
        document.getElementById('status').textContent = 'Camera error: ' + err.message;
      }
    }

    function stopDetection() {
      clearInterval(interval);
      if (stream) stream.getTracks().forEach(t => t.stop());
      ctx.clearRect(0, 0, overlay.width, overlay.height);
      document.getElementById('startBtn').style.display = 'inline-block';
      document.getElementById('stopBtn').style.display  = 'none';
      document.getElementById('status').textContent     = 'Stopped.';
    }

    async function sendFrame() {
      if (sending) return;   // Skip if previous request still in flight
      sending = true;

      // Draw current video frame to an offscreen canvas and encode as JPEG
      const cap    = document.createElement('canvas');
      cap.width    = video.videoWidth;
      cap.height   = video.videoHeight;
      cap.getContext('2d').drawImage(video, 0, 0);
      const b64 = cap.toDataURL('image/jpeg', 0.85);

      try {
        const res  = await fetch('/api/v1/detect/live', {
          method:  'POST',
          headers: { 'Content-Type': 'application/json' },
          body:    JSON.stringify({ frame_b64: b64, session_id: 'browser-test' }),
        });
        const data = await res.json();

        if (!res.ok) {
          document.getElementById('status').textContent = 'Error: ' + (data.detail || res.status);
          sending = false;
          return;
        }

        updateUI(data);
        drawBoxes(data.face_boxes, data.label);
        document.getElementById('status').textContent = 'Running…';

      } catch (err) {
        document.getElementById('status').textContent = 'Network error: ' + err.message;
      }

      sending = false;
    }

    function updateUI(data) {
      const labelEl = document.getElementById('label');
      labelEl.textContent  = data.label;
      labelEl.className    = 'label ' + data.label;

      document.getElementById('confidence').textContent = data.confidence_display;
      document.getElementById('fakePct').textContent    = 'Fake: ' + data.probabilities.fake_pct + '%';
      document.getElementById('realPct').textContent    = 'Real: ' + data.probabilities.real_pct + '%';
      document.getElementById('inferMs').textContent    = data.inference_time_ms + ' ms';
      document.getElementById('meta').textContent       =
        'Device: ' + data.device + '  |  Threshold: ' + (data.threshold * 100).toFixed(0) + '%';
    }

    function drawBoxes(boxes, label) {
      ctx.clearRect(0, 0, overlay.width, overlay.height);
      if (!boxes || boxes.length === 0) return;

      const color     = label === 'FAKE' ? '#ff4444' : '#44dd88';
      ctx.strokeStyle = color;
      ctx.lineWidth   = 3;
      ctx.font        = 'bold 16px Segoe UI';
      ctx.fillStyle   = color;

      boxes.forEach(b => {
        ctx.strokeRect(b.x, b.y, b.w, b.h);
        ctx.fillText(label, b.x + 4, b.y - 6);
      });
    }
  </script>
</body>
</html>"""
    return HTMLResponse(content=html)

# # =============================================================================
# #  ENTRY POINT
# # =============================================================================

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         "app:app",
#         host    = "0.0.0.0",
#         port    = PORT,
#         reload  = False,   
#         workers = 1,       
#     )