# DeepFake Detection API — Setup & Run Guide

**EfficientNetB4 + BiLSTM + Temporal Attention | FastAPI | PyTorch**

---

# Verified Architecture (from training notebook)

| Config              | Value                  |
| ------------------- | ---------------------- |
| Input Size          | `380 × 380`            |
| Frames Per Sample   | `15`                   |
| CNN Backbone        | `EfficientNetB4`       |
| LSTM Hidden Size    | `256`                  |
| LSTM Layers         | `2`                    |
| Attention Dimension | `128`                  |
| Dropout             | `0.5`                  |
| Labels              | `0 = REAL`, `1 = FAKE` |
| Checkpoint Key      | `model_state`          |
| Checkpoint File     | `best_model.pth`       |

---

# Project Structure

```text
deepfake_api/
├── app.py
├── requirements-gpu.txt
├── requirements-cpu.txt
├── README.md
└── checkpoints/
    └── best_model.pth
```

---

# Features

* Image DeepFake Detection
* Video DeepFake Detection
* Live Webcam Detection
* Face Bounding Box Detection
* Temporal Attention Visualization
* GPU + CPU Support
* Built-in Browser Test UI
* FastAPI Swagger Documentation
* Frontend Ready JSON Responses

---

# API Architecture

```text
Browser / React / Node.js
        ↓
FastAPI (app.py)
        ↓
Preprocessing
        ↓
EfficientNetB4
        ↓
BiLSTM
        ↓
Temporal Attention
        ↓
REAL / FAKE Prediction
```

---

# Model Pipeline

## Image Detection

```text
Image
 → duplicate into 15 frames
 → random spatial jitter
 → resize to 380×380
 → ImageNet normalization
 → EfficientNetB4
 → BiLSTM
 → Temporal Attention
 → REAL / FAKE
```

---

## Video Detection

```text
Video
 → evenly sample 15 frames
 → preprocess each frame
 → stack tensor (1,15,3,380,380)
 → model inference
 → prediction
```

---

## Live Webcam Detection

```text
Browser Webcam
 → canvas.toDataURL('image/jpeg')
 → POST base64 frame
 → FastAPI decodes frame
 → face detection
 → temporal sequence generation
 → inference
 → return REAL / FAKE + face boxes
```

---

# Setup

## Create Virtual Environment

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

# GPU Installation (CUDA 11.8)

```bash
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118

pip install -r requirements-gpu.txt
```

---

# CPU Installation

```bash
pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu

pip install -r requirements-cpu.txt
```

---

# Verify Installation

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

---

# Place Checkpoint

```bash
mkdir checkpoints
```

Copy your trained checkpoint:

```text
checkpoints/best_model.pth
```

---

# Important Checkpoint Note

The API expects the checkpoint to contain:

```python
{
    "model_state": ...
}
```

This key is required because the training notebook saves:

```python
torch.save({
    "model_state": model.state_dict(),
    ...
}, "best_model.pth")
```

If `model_state` is missing, the API will crash intentionally to avoid silently loading incorrect weights.

---

# Run Server

## Development

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Production

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

---

# Open API Docs

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

---

# Built-in Live Webcam Test Page

Open:

```text
http://localhost:8000/api/v1/live
```

Features:

* Webcam access
* Real-time prediction
* GREEN box → REAL
* RED box → FAKE
* Confidence display
* Inference timing
* Automatic polling every 800ms

No frontend setup required.

---

# API Endpoints

## Health Check

### GET `/api/v1/health`

Returns:

```json
{
  "status": "ok",
  "device": "cuda",
  "model_loaded": true
}
```

---

## Model Information

### GET `/api/v1/model/info`

Returns architecture + parameter info.

---

## Image Detection

### POST `/api/v1/detect/image`

### Supported Formats

* jpg
* jpeg
* png
* webp

### Example

```bash
curl -X POST http://localhost:8000/api/v1/detect/image \
  -F "file=@face.jpg"
```

---

## Video Detection

### POST `/api/v1/detect/video`

### Supported Formats

* mp4
* avi
* mov
* mkv
* webm

### Example

```bash
curl -X POST http://localhost:8000/api/v1/detect/video \
  -F "file=@video.mp4"
```

---

## Live Frame Detection

### POST `/api/v1/detect/live`

### Request

```json
{
  "frame_b64": "data:image/jpeg;base64,...",
  "session_id": "test"
}
```

### Response

```json
{
  "label": "REAL",
  "confidence_display": "82.31%",
  "face_boxes": [
    {
      "x": 120,
      "y": 80,
      "w": 220,
      "h": 220
    }
  ]
}
```

---

# Standard API Response

```json
{
  "label": "FAKE",
  "confidence_pct": 94.32,
  "confidence_display": "94.32%",
  "probabilities": {
    "fake_pct": 94.32,
    "real_pct": 5.68,
    "fake_raw": 0.9432,
    "real_raw": 0.0568
  },
  "threshold": 0.5,
  "attention_weights": [0.06, 0.07],
  "inference_time_ms": 85.2,
  "device": "cuda"
}
```

---

# Video Response Extras

```json
{
  "frames_sampled": 15,
  "frame_previews": ["base64...", "base64..."],
  "video_meta": {
    "fps": 30,
    "duration_seconds": 10
  }
}
```

---

# Environment Variables

| Variable         | Default                    |
| ---------------- | -------------------------- |
| MODEL_PATH       | checkpoints/best_model.pth |
| THRESHOLD        | 0.5                        |
| MAX_VIDEO_FRAMES | 120                        |
| PORT             | 8000                       |

---

# Node.js Integration Flow

```text
React Frontend
      ↓
Node.js / Express
      ↓
FastAPI
      ↓
DeepFake Model
      ↓
Prediction JSON
      ↓
Frontend Display
```

---

# Performance

## GPU (RTX 2050)

| Task            | Time        |
| --------------- | ----------- |
| Image Detection | ~80–150 ms  |
| Video Detection | ~300–800 ms |
| Live Frame      | ~100–200 ms |

---

## CPU

| Task            | Time        |
| --------------- | ----------- |
| Image Detection | ~300–800 ms |
| Video Detection | ~2–5 sec    |
| Live Frame      | ~400–700 ms |

---

# Live Detection Frontend Logic

```javascript
setInterval(sendFrame, 800)
```

Each frame:

```javascript
canvas.toDataURL('image/jpeg', 0.85)
```

is sent to:

```text
POST /api/v1/detect/live
```

---

# Troubleshooting

## CUDA Not Detected

```bash
nvidia-smi
```

Then reinstall CUDA PyTorch:

```bash
pip install torch==2.0.1+cu118 torchvision==0.15.2+cu118 --index-url https://download.pytorch.org/whl/cu118
```

---

## Checkpoint Error

```text
Key 'model_state' not found in checkpoint
```

Your checkpoint format is incorrect.

Inspect it using:

```python
import torch

ckpt = torch.load("best_model.pth", map_location="cpu")

print(ckpt.keys())
```

---

## Slow Live Detection on CPU

Increase polling interval:

```javascript
setInterval(sendFrame, 1500)
```

---

# Tech Stack

* FastAPI
* PyTorch
* OpenCV
* EfficientNetB4
* BiLSTM
* Temporal Attention
* CUDA 11.8
* Uvicorn

---

# Complete Request Flow

```text
User Uploads Image / Video
        ↓
FastAPI Receives Request
        ↓
Frame Preprocessing
        ↓
380×380 Normalization
        ↓
EfficientNetB4 Features
        ↓
BiLSTM Temporal Modeling
        ↓
Attention Weighting
        ↓
REAL / FAKE Prediction
        ↓
Frontend JSON Response
```
