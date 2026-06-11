# DrishtiVision — AI-Powered Deepfake Detection System

> An end-to-end deepfake detection platform capable of analyzing images, videos, and live webcam feeds using state-of-the-art deep learning models, built as a final-year capstone project.

---

## Table of Contents

- [Overview](#overview)
- [Team](#team)
- [System Architecture](#system-architecture)
- [Models](#models)
  - [Image Model — EfficientNet-B4](#image-model--efficientnet-b4)
  - [Video & Live Model — Hybrid EfficientNet-B4 + BiLSTM + Temporal Attention](#video--live-model--hybrid-efficientnet-b4--bilstm--temporal-attention)
- [Datasets](#datasets)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Backend](#backend)
- [Installation & Setup](#installation--setup)
- [Training Details](#training-details)
- [Results](#results)
- [Resume Summary](#resume-summary)
- [License](#license)

---

## Overview

DrishtiVision is a full-stack AI system for deepfake detection supporting three modes:

- **Image Detection** — Single image analysis using a fine-tuned EfficientNet-B4 model (96% accuracy, AUC 0.9947)
- **Video Detection** — Temporal frame analysis using a hybrid CNN + Bidirectional LSTM + Temporal Attention architecture
- **Live / Webcam Detection** — Real-time per-frame inference via webcam feed

The system is accessible through a React web application backed by a Node.js/Express API gateway, two FastAPI inference services, and a MongoDB database for user management and detection history.

---

## Team

| Name | Role |
|---|---|
| **Farhan Abid** | ML Engineering — Dataset collection & cleaning, model architecture, training (EfficientNet-B4 + hybrid video/live model), FastAPI inference servers, full-stack integration |
| **Utsav Kashyap** | Backend — Node.js/Express API gateway, JWT authentication, MongoDB integration |
| **Nandini** | Data Lead — Primary responsibility for data collection, preprocessing, cleaning, organisation, and pipeline construction across all datasets |
| **Jamal Ashraf** | Data collection & support |

---

## System Architecture

```
React Frontend  (Port 3000)
        │
        ▼
Node.js / Express API Gateway  (Port 5000)
  ├── Google OAuth + JWT Authentication
  ├── MongoDB  (Users, Sessions, Detection Logs & History)
  └── Proxies inference requests to:
        ├── FastAPI — EfficientNet-B4 Image Model     (Port 8000)
        └── FastAPI — Hybrid Video / Live Model       (Port 8001)
```

---

## Models

### Image Model — EfficientNet-B4

A standalone image classifier trained to distinguish real vs. AI-generated faces from a single image.

| Property | Value |
|---|---|
| Architecture | EfficientNet-B4 |
| Input Size | 380 × 380 |
| Training Strategy | Two-phase: head-only warmup → last-3-block backbone fine-tune |
| Loss | BCE with Label Smoothing |
| Test Accuracy | **96%** |
| AUC | **0.9947** |

Key decisions:
- EfficientNet-B4 was selected over XceptionNet and ResNet50 after both showed overfitting on the dataset
- A denormalize → augment → renormalize pipeline was implemented to prevent augmentation from corrupting already-normalized inputs

---

### Video & Live Model — Hybrid EfficientNet-B4 + BiLSTM + Temporal Attention

Extracts per-frame spatial features with EfficientNet-B4, then models temporal inconsistencies across the sequence with a Bidirectional LSTM and a Temporal Attention layer.

| Property | Value |
|---|---|
| Architecture | EfficientNet-B4 + BiLSTM + Temporal Attention |
| Input | 15 frames × 380 × 380 × 3 |
| LSTM Hidden Size | 256 |
| LSTM Layers | 2 |
| Attention Dim | 128 |
| Dropout | 0.5 |
| Loss | FocalLabelSmoothBCE (γ=1.5, smoothing=0.10) |
| Inference Threshold | 0.45 |
| Test Accuracy | **83.82%** |
| Dataset | MAVOS-DD (9,600 samples) |

Training configuration:

```
IMG_SIZE      = 380       N_FRAMES    = 15
LSTM_HIDDEN   = 256       LSTM_LAYERS = 2
ATTENTION_DIM = 128       DROPOUT     = 0.5
LABEL_SMOOTH  = 0.05      LR          = 1e-4
BATCH_SIZE    = 4         ACCUM_STEPS = 4
PATIENCE      = 7
```

Notable engineering:
- Gradient checkpointing enabled to fit training within 4 GB VRAM (RTX 2050)
- `hardfake_sim` augmentation applied to real samples at 15% for fake-bias correction
- Live endpoint uses `image_to_frames()` with ±1.5% per-slot spatial/brightness jitter to simulate temporal diversity from a single webcam frame

---

## Datasets

All datasets were collected from Kaggle, GitHub, Hugging Face, academic survey sources, and dedicated deepfake research sites, then cleaned, organised, and preprocessed by the team (led by Nandini, with data collection and cleaning contributions from Farhan).

### Video Dataset — MAVOS-DD Preprocessed

> Bronze Medal on Kaggle

| Property | Detail |
|---|---|
| Samples | 9,600 video clips |
| Languages | 4 |
| Generation Methods | 6 |
| Preprocessed Format | HDF5 (`faces_9600_380.h5`) |
| H5 Shape | `(9600, 15, 380, 380, 3)` — float16, ImageNet-normalized |
| Kaggle Link | [deepfake-video-9.6k](https://www.kaggle.com/datasets/farhanabidtech786/deepfake-video-9-6k/) |

### Image Dataset

| Property | Detail |
|---|---|
| Sources | 140k-real-vs-fake, deepfake-vs-real-60k, FFHQ, real-vs-hardfakes, and others |
| Preprocessed Format | `.npz` files at 224×224, ImageNet-normalized |
| Kaggle Link | [image_dataset](https://www.kaggle.com/datasets/farhanabidtech786/deepfake) |

---

## Tech Stack

**Machine Learning**
- Python 3.10.11 · PyTorch · CUDA 11.8
- `efficientnet-pytorch==0.7.1` · `opencv-python-headless`

**Inference API**
- FastAPI · Uvicorn
- Port 8000 — Image model (EfficientNet-B4)
- Port 8001 — Video + Live hybrid model

**API Gateway / Backend**
- Node.js · Express.js
- JWT (`jsonwebtoken`) · Google OAuth
- Multer · Axios · MongoDB (Mongoose)
- Port 5000

**Frontend**
- React 19 · Vite · React Router DOM
- Tailwind CSS v4 · Framer Motion · OGL
- Port 3000

---

## Repository Structure

**Main Repo** — [`farhanabid786/Project-final-Year`](https://github.com/farhanabid786/Project-final-Year)

```
Project-final-Year/
├── DL/
│   └── deepfake_fixed_v3.ipynb    # Base hybrid model (training notebook)
├── frontend/                      # React + Tailwind CSS + Vite application
├── LICENSE
└── README.md
```

Branches contain individual contributor work. The `farhan` branch holds the EfficientNet model code. An early XceptionNet experiment is available as a [release/tag](https://github.com/farhanabid786/Project-final-Year/releases).

**Backend Repo** — [`utsavkashyap5/backend-deep`](https://github.com/utsavkashyap5/backend-deep)

```
backend/
├── src/
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── auth.routes.js
│   │   │   ├── auth.controller.js
│   │   │   └── auth.service.js
│   │   └── detection/
│   │       ├── detection.routes.js
│   │       ├── detection.controller.js
│   │       └── detection.service.js
│   ├── middleware/
│   │   └── upload.middleware.js
│   ├── uploads/
│   ├── server.js
│   └── app.js
├── .env
└── package.json
```

---

## API Reference

### Node.js / Express Gateway (Port 5000)

#### Authentication

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/api/auth/register` | `{ name, email, password }` | Register new user |
| POST | `/api/auth/login` | `{ email, password }` | Login, receive JWT |

#### Detection

| Method | Endpoint | Body | Description |
|---|---|---|---|
| POST | `/api/detect/image` | `multipart/form-data { file }` | Image deepfake detection |
| POST | `/api/detect/video` | `multipart/form-data { file }` | Video deepfake detection |

The Express backend validates, buffers uploaded files in `src/uploads/`, then forwards to FastAPI via Axios and returns the prediction to the frontend.

---

### FastAPI — Image Inference (Port 8000)

Accepts a single face image. Returns `REAL` / `FAKE` with a confidence score using the EfficientNet-B4 model.

---

### FastAPI — Video & Live Inference (Port 8001)

- **Video endpoint** — Accepts a video file, extracts 15 evenly-spaced frames, runs hybrid model inference
- **Live endpoint** — Accepts a base64-encoded webcam frame, generates a 15-frame jittered sequence via `image_to_frames()`, runs inference

Both return a `REAL` / `FAKE` label with a confidence score.

---

## Frontend

Built with React 19 + Vite, Tailwind CSS v4, Framer Motion, and OGL for WebGL effects. Three main views:

- **Image Upload** — Drag-and-drop or file picker, instant result with confidence bar
- **Video Upload** — Upload a clip for frame-level temporal analysis
- **Live Detection** — Webcam feed with real-time HUD overlay showing per-frame predictions

Authentication is handled via Google OAuth; JWT tokens are issued and validated by the Express backend.

---

## Backend

The Node.js/Express backend (Port 5000) is the API gateway between the React frontend and the FastAPI AI services. Responsibilities:

- User registration and login (password hashing, JWT issuance)
- Middleware: CORS, Multer upload handling, JWT validation
- Forwarding detection requests to FastAPI via Axios
- Returning model predictions to the frontend
- MongoDB: users, sessions, detection logs, detection history

**Environment variables (`.env`):**

```env
PORT=5000
JWT_SECRET=your_secret
FASTAPI_URL=http://127.0.0.1:8001
MONGO_URI=your_mongodb_uri
```

---

## Installation & Setup

### Prerequisites

- Python 3.10.11
- Node.js v18+
- CUDA 11.8 compatible GPU (recommended; CPU inference supported)
- MongoDB instance (local or Atlas)

### 1. Clone Repositories

```bash
git clone https://github.com/farhanabid786/Project-final-Year.git
git clone https://github.com/utsavkashyap5/backend-deep.git
```

### 2. FastAPI Inference Servers

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
pip install fastapi uvicorn efficientnet-pytorch opencv-python-headless h5py numpy

# Image model — port 8000
uvicorn app_image:app --host 0.0.0.0 --port 8000

# Hybrid video/live model — port 8001
uvicorn app:app --host 0.0.0.0 --port 8001
```

Download model weights from the [Releases](https://github.com/farhanabid786/Project-final-Year/releases) section.

### 3. Node.js Backend

```bash
cd backend-deep
npm install
# configure .env
npm run dev
# runs at http://localhost:5000
```

### 4. React Frontend

```bash
cd Project-final-Year/frontend
npm install
npm run dev
# runs at http://localhost:3000
```

---

## Training Details

Training notebooks are in `DL/`. The base hybrid model was trained in `deepfake_fixed_v3.ipynb`; fine-tuning variants are in `deepfake_finetune_v1` through `v3_final`.

**Critical bugs identified and resolved:**

| Bug | Impact | Fix |
|---|---|---|
| MixUp applied inside `evaluate()` instead of `train_one_epoch()` | Validation AUC stuck at 0.5 | Moved MixUp strictly to the training loop |
| Double-divide normalization on H5 inputs | Inputs collapsed to near-zero | Fixed normalization pipeline |
| CUDA OOM on 4 GB VRAM | Training crashes | Enabled `torch.utils.checkpoint` for gradient checkpointing |
| Augmentation applied to already-normalized data (ColorJitter on ImageNet values) | Corrupted training signal | Implemented denormalize → augment → renormalize |
| Live endpoint forwarding 15 identical frame copies to BiLSTM | Fake-bias in live predictions | Introduced per-slot spatial/brightness jitter in `image_to_frames()` |
| Inference threshold not loading from checkpoint | Wrong threshold at runtime | Fixed threshold loading in FastAPI startup |

---

## Results

| Model | Mode | Test Accuracy | AUC |
|---|---|---|---|
| EfficientNet-B4 | Image | **96.00%** | **0.9947** |
| EfficientNet-B4 + BiLSTM + Temporal Attention | Video / Live | **83.82%** | — |

---

## Resume Summary

> **DrishtiVision — AI-Powered Deepfake Detection System** | Final Year Capstone Project

- Built an end-to-end deepfake detection system with three detection modes (image, video, live webcam) using a custom EfficientNet-B4 image model (96% accuracy, AUC 0.9947) and a hybrid EfficientNet-B4 + Bidirectional LSTM + Temporal Attention architecture for video/live inference (83.82% accuracy on MAVOS-DD); deployed via dual FastAPI services integrated with a React + Node.js + MongoDB full-stack application.
- Curated and published two Kaggle datasets (image and video) aggregated from Kaggle, Hugging Face, GitHub, and research sources — the video dataset (9,600 samples, 4 languages, 6 generation methods, preprocessed as HDF5) received a Kaggle Bronze Medal.
- Resolved critical training bugs (MixUp leakage into validation, double-normalization collapse, CUDA OOM via gradient checkpointing, augmentation-on-normalized-data) and engineered production inference fixes (per-frame jitter for live detection, threshold loading from checkpoint, CPU/GPU-safe autocast).

---

## License

This project is licensed under the MIT License. See [LICENSE](https://github.com/farhanabid786/Project-final-Year/blob/main/LICENSE) for details.
