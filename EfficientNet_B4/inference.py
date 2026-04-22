# """
# inference.py — Face detection + deepfake prediction
# Extracted and cleaned from Testing_.ipynb
# """

# import os
# import io
# import gc
# import urllib.request
# import urllib.error

# import cv2
# import numpy as np
# import torch
# import torchvision.transforms as transforms
# from PIL import Image

# from model import DEFAULT_MODEL_CONFIG

# # ── Face-detector weights URLs (OpenCV SSD ResNet10) ─────────────────────────
# _PROTO_URL   = (
#     "https://raw.githubusercontent.com/opencv/opencv/master/"
#     "samples/dnn/face_detector/deploy.prototxt"
# )
# _WEIGHTS_URL = (
#     "https://github.com/opencv/opencv_3rdparty/raw/"
#     "dnn_samples_face_detector_20170830/"
#     "res10_300x300_ssd_iter_140000.caffemodel"
# )

# # ── ImageNet transform (must match preprocessing exactly) ────────────────────
# _INFERENCE_TRANSFORM = transforms.Compose([
#     transforms.Resize((
#         DEFAULT_MODEL_CONFIG["image_size"],
#         DEFAULT_MODEL_CONFIG["image_size"],
#     )),
#     transforms.ToTensor(),
#     transforms.Normalize(
#         mean=DEFAULT_MODEL_CONFIG["mean"],
#         std=DEFAULT_MODEL_CONFIG["std"],
#     ),
# ])


# def download_face_detector(detector_dir: str) -> None:
#     """Download OpenCV SSD face-detector weights if not already present."""
#     os.makedirs(detector_dir, exist_ok=True)
#     proto_path   = os.path.join(detector_dir, "deploy.prototxt")
#     weights_path = os.path.join(detector_dir, "res10_300x300_ssd_iter_140000.caffemodel")

#     if not os.path.exists(proto_path):
#         print("[inference] Downloading face-detector config …")
#         urllib.request.urlretrieve(_PROTO_URL, proto_path)
#         print("[inference] deploy.prototxt downloaded.")

#     if not os.path.exists(weights_path):
#         print("[inference] Downloading face-detector weights (~10 MB) …")
#         urllib.request.urlretrieve(_WEIGHTS_URL, weights_path)
#         print("[inference] caffemodel downloaded.")

#     return proto_path, weights_path


# def load_face_net(detector_dir: str) -> cv2.dnn_Net:
#     """Return a loaded OpenCV DNN face-detection network."""
#     proto_path, weights_path = download_face_detector(detector_dir)
#     net = cv2.dnn.readNetFromCaffe(proto_path, weights_path)
#     return net


# def load_image_from_bytes(data: bytes) -> np.ndarray | None:
#     """
#     Decode image bytes → BGR numpy array.
#     Falls back to PIL for formats OpenCV may miss (e.g. WEBP on some builds).
#     Returns None if the image cannot be decoded.
#     """
#     arr = np.frombuffer(data, dtype=np.uint8)
#     img_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
#     if img_bgr is not None:
#         return img_bgr
#     # PIL fallback
#     try:
#         pil = Image.open(io.BytesIO(data)).convert("RGB")
#         return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
#     except Exception:
#         return None


# def detect_and_crop_face(
#     img_bgr: np.ndarray,
#     face_net: cv2.dnn_Net,
#     margin: float = 0.2,
#     confidence_thresh: float = 0.5,
# ) -> tuple[Image.Image, bool]:
#     """
#     Detect the most confident face in *img_bgr* and return a cropped PIL image.
#     Falls back to a centre-square crop when no face is detected.

#     Returns
#     -------
#     face_pil   : PIL.Image (RGB)
#     face_found : bool
#     """
#     h, w = img_bgr.shape[:2]

#     blob = cv2.dnn.blobFromImage(
#         img_bgr, 1.0, (300, 300), (104.0, 177.0, 123.0), swapRB=False
#     )
#     face_net.setInput(blob)
#     detections = face_net.forward()

#     best_conf = 0.0
#     best_box  = None
#     for i in range(detections.shape[2]):
#         conf = float(detections[0, 0, i, 2])
#         if conf > confidence_thresh and conf > best_conf:
#             best_conf = conf
#             x1 = int(detections[0, 0, i, 3] * w)
#             y1 = int(detections[0, 0, i, 4] * h)
#             x2 = int(detections[0, 0, i, 5] * w)
#             y2 = int(detections[0, 0, i, 6] * h)
#             best_box = (x1, y1, x2, y2)

#     if best_box is None:
#         # Centre-square crop
#         img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
#         pil     = Image.fromarray(img_rgb)
#         s       = min(w, h)
#         return pil.crop(((w - s) // 2, (h - s) // 2,
#                          (w + s) // 2, (h + s) // 2)), False

#     x1, y1, x2, y2 = best_box
#     bw, bh = x2 - x1, y2 - y1
#     x1 = max(0, int(x1 - margin * bw))
#     y1 = max(0, int(y1 - margin * bh))
#     x2 = min(w, int(x2 + margin * bw))
#     y2 = min(h, int(y2 + margin * bh))

#     face_rgb = cv2.cvtColor(img_bgr[y1:y2, x1:x2], cv2.COLOR_BGR2RGB)
#     return Image.fromarray(face_rgb), True


# def predict_from_bytes(
#     image_bytes: bytes,
#     model: torch.nn.Module,
#     face_net: cv2.dnn_Net,
#     device: torch.device,
#     threshold: float,
#     use_amp: bool = True,
# ) -> dict:
#     """
#     Full inference pipeline:  raw image bytes → prediction dict.

#     Parameters
#     ----------
#     image_bytes : raw bytes from an uploaded image file
#     model       : loaded DeepfakeEfficientNet (eval mode)
#     face_net    : OpenCV DNN face detector
#     device      : torch.device
#     threshold   : classification boundary (calibrated on test set)
#     use_amp     : whether to use automatic mixed precision on CUDA

#     Returns
#     -------
#     dict with keys:
#         label          : "FAKE" | "REAL"
#         confidence     : float [0-100] — confidence in the *predicted* label
#         fake_prob      : float [0-100]
#         real_prob      : float [0-100]
#         face_detected  : bool
#         threshold      : float
#     """
#     # 1. Decode image
#     img_bgr = load_image_from_bytes(image_bytes)
#     if img_bgr is None:
#         raise ValueError("Could not decode image. Ensure the file is a valid "
#                          "JPG, PNG, BMP, WEBP, or TIFF.")

#     # 2. Face detection / crop
#     face_pil, face_found = detect_and_crop_face(img_bgr, face_net)

#     # 3. Transform
#     tensor = _INFERENCE_TRANSFORM(face_pil).unsqueeze(0).to(device)

#     # 4. Forward pass
#     model.eval()
#     amp_enabled = use_amp and device.type == "cuda"
#     with torch.no_grad():
#         if amp_enabled:
#             with torch.amp.autocast("cuda"):
#                 prob = torch.sigmoid(model(tensor)).item()
#         else:
#             prob = torch.sigmoid(model(tensor)).item()

#     # 5. Cleanup
#     del tensor
#     if device.type == "cuda":
#         torch.cuda.empty_cache()
#     gc.collect()

#     # 6. Build result
#     label      = "FAKE" if prob >= threshold else "REAL"
#     confidence = prob if prob >= threshold else 1.0 - prob

#     return {
#         "label"        : label,
#         "confidence"   : round(confidence * 100, 2),
#         "fake_prob"    : round(prob        * 100, 2),
#         "real_prob"    : round((1 - prob)  * 100, 2),
#         "face_detected": face_found,
#         "threshold"    : round(threshold, 2),
#     }


import os
import io
import urllib.request

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

from model import DEFAULT_MODEL_CONFIG


# ================= FACE DETECTOR URLs =================
_PROTO_URL = (
    "https://raw.githubusercontent.com/opencv/opencv/master/"
    "samples/dnn/face_detector/deploy.prototxt"
)

_WEIGHTS_URL = (
    "https://github.com/opencv/opencv_3rdparty/raw/"
    "dnn_samples_face_detector_20170830/"
    "res10_300x300_ssd_iter_140000.caffemodel"
)


# ================= TRANSFORM =================
_INFERENCE_TRANSFORM = transforms.Compose([
    transforms.Resize((
        DEFAULT_MODEL_CONFIG["image_size"],
        DEFAULT_MODEL_CONFIG["image_size"]
    )),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=DEFAULT_MODEL_CONFIG["mean"],
        std=DEFAULT_MODEL_CONFIG["std"]
    ),
])


#  DOWNLOAD 
def download_face_detector(detector_dir: str):
    os.makedirs(detector_dir, exist_ok=True)

    proto_path = os.path.join(detector_dir, "deploy.prototxt")
    weights_path = os.path.join(detector_dir, "res10_300x300_ssd_iter_140000.caffemodel")

    if not os.path.exists(proto_path):
        print("⬇️ Downloading deploy.prototxt...")
        urllib.request.urlretrieve(_PROTO_URL, proto_path)

    if not os.path.exists(weights_path):
        print("⬇️ Downloading caffemodel...")
        urllib.request.urlretrieve(_WEIGHTS_URL, weights_path)

    return proto_path, weights_path


#  LOAD DETECTOR 
def load_face_net(detector_dir: str):
    proto, weights = download_face_detector(detector_dir)
    net = cv2.dnn.readNetFromCaffe(proto, weights)
    return net


#  IMAGE LOADING 
def load_image_from_bytes(data: bytes):
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    if img is not None:
        return img

    # PIL fallback
    try:
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


#  FACE DETECTION 
def detect_and_crop_face(img_bgr, face_net, margin=0.2, conf_thresh=0.5):
    h, w = img_bgr.shape[:2]

    blob = cv2.dnn.blobFromImage(
        img_bgr, 1.0, (300, 300),
        (104.0, 177.0, 123.0),
        swapRB=False
    )

    face_net.setInput(blob)
    detections = face_net.forward()

    best_box = None
    best_conf = 0.0

    for i in range(detections.shape[2]):
        conf = float(detections[0, 0, i, 2])

        if conf > conf_thresh and conf > best_conf:
            best_conf = conf

            x1 = int(detections[0, 0, i, 3] * w)
            y1 = int(detections[0, 0, i, 4] * h)
            x2 = int(detections[0, 0, i, 5] * w)
            y2 = int(detections[0, 0, i, 6] * h)

            best_box = (x1, y1, x2, y2)

    #  FALLBACK 
    if best_box is None:
        # center crop (better than full image)
        size = min(w, h)
        cx, cy = w // 2, h // 2

        x1 = max(0, cx - size // 2)
        y1 = max(0, cy - size // 2)
        x2 = min(w, cx + size // 2)
        y2 = min(h, cy + size // 2)

        face = img_bgr[y1:y2, x1:x2]
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

        return Image.fromarray(face), False

    #  APPLY MARGIN 
    x1, y1, x2, y2 = best_box
    bw, bh = x2 - x1, y2 - y1

    x1 = max(0, int(x1 - margin * bw))
    y1 = max(0, int(y1 - margin * bh))
    x2 = min(w, int(x2 + margin * bw))
    y2 = min(h, int(y2 + margin * bh))

    face = img_bgr[y1:y2, x1:x2]
    face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)

    return Image.fromarray(face), True


#  MAIN PREDICTION 
def predict_from_bytes(image_bytes, model, face_net, device, threshold, use_amp=True):
    # 1. Decode image
    img_bgr = load_image_from_bytes(image_bytes)
    if img_bgr is None:
        raise ValueError("Invalid image")

    # 2. Detect face
    face_pil, face_found = detect_and_crop_face(img_bgr, face_net)

    # 3. Correct transform (MATCH TRAINING)
    transform = transforms.Compose([
        transforms.Resize((380, 380)),
        transforms.ToTensor(),
        transforms.Normalize(
            [0.485, 0.456, 0.406],
            [0.229, 0.224, 0.225]
        )
    ])

    tensor = transform(face_pil).unsqueeze(0).to(device)

    # 4. Prediction
    model.eval()
    with torch.no_grad():
        if use_amp and device.type == "cuda":
            with torch.amp.autocast("cuda"):
                logits = model(tensor)
        else:
            logits = model(tensor)

        prob = torch.sigmoid(logits).item()

    # 5. Decision
    label = "FAKE" if prob >= threshold else "REAL"

    return {
        "label": label,
        "confidence": round(max(prob, 1 - prob) * 100, 2),
        "fake_prob": round(prob * 100, 2),
        "real_prob": round((1 - prob) * 100, 2),
        "face_detected": face_found,
        "threshold": threshold
    }